import os
import shutil
import subprocess
import threading
import time

from app.config_store import load_config


def _env_bool(name, default=False):
    value = os.environ.get(name, str(default)).strip().lower()
    return value in ("1", "true", "yes", "on")


def _parse_disk_map():
    """
    Erwartetes Format:
    LED_DISK_MAP="disk1:sda,disk2:sdb,disk3:sdc,disk4:sdd"
    """
    raw = os.environ.get("LED_DISK_MAP", "disk1:sda,disk2:sdb,disk3:sdc,disk4:sdd")
    result = {}

    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue

        led_name, dev_name = part.split(":", 1)
        led_name = led_name.strip()
        dev_name = dev_name.strip()

        if led_name and dev_name:
            result[led_name] = dev_name

    return result


class DiskMonitor:
    def __init__(self, led_service):
        self.led_service = led_service

        self.enabled = _env_bool("LED_MONITOR_ENABLED", False)
        self.disk_map = _parse_disk_map()

        # SMART / standby-safe checking
        self.smart_check_enabled = _env_bool("LED_SMART_CHECK_ENABLED", True)
        self.smart_device_type = os.environ.get("LED_SMART_DEVICE_TYPE", "ata").strip()
        self.smart_binary = os.environ.get("LED_SMART_BINARY", "smartctl").strip()

        # Timing
        self.poll_interval = float(os.environ.get("LED_POLL_INTERVAL", "10"))
        self.smart_interval = float(os.environ.get("LED_SMART_INTERVAL", "60"))
        self.active_hold_seconds = float(os.environ.get("LED_ACTIVE_HOLD_SECONDS", "20"))
        self.idle_after_seconds = float(os.environ.get("LED_IDLE_AFTER_SECONDS", "45"))

        # Internal state
        self.last_stat = {}
        self.last_change = {}
        self.last_smart = {}
        self.last_smart_check = {}
        self.last_applied = {}
        self.current_state = {}

        self._thread = None

    def start(self):
        if not self.enabled:
            print("[disk-monitor] disabled", flush=True)
            return

        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[disk-monitor] started", flush=True)

    def get_states(self):
        """
        Kann später von der App genutzt werden, um den letzten erkannten Zustand
        pro Disk in der Oberfläche anzuzeigen.
        """
        return dict(self.current_state)

    def _read_block_stat(self, dev_name):
        """
        Liest /sys/block/<dev>/stat.
        Das ist ein Sysfs-Lesezugriff und sollte keine HDD aufwecken.
        """
        path = f"/sys/block/{dev_name}/stat"

        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
        except OSError:
            return None

    def _probe_smart(self, dev_name):
        """
        Standby-sichere SMART-Prüfung.

        Ziel:
        - standby erkennen, ohne die HDD aufzuwecken
        - SMART-Fehler erkennen, wenn die HDD bereits aktiv ist
        - keine Autodetektion des Gerätetyps -> -d ata

        Rückgabe:
        {
            "standby": bool,
            "error": bool,
            "available": bool,
            "returncode": int | None,
            "stdout": str,
            "stderr": str
        }
        """
        if not self.smart_check_enabled:
            return {
                "standby": False,
                "error": False,
                "available": False,
                "returncode": None,
                "stdout": "",
                "stderr": "",
            }

        if shutil.which(self.smart_binary) is None:
            return {
                "standby": False,
                "error": False,
                "available": False,
                "returncode": None,
                "stdout": "",
                "stderr": f"{self.smart_binary} not found",
            }

        cmd = [
            self.smart_binary,
            "-n", "standby,3",
            "-H",
            "-d", self.smart_device_type,
            f"/dev/{dev_name}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        combined = f"{stdout}\n{stderr}".upper()

        # 3 = standby, Prüfung absichtlich nicht weiter ausgeführt
        if result.returncode == 3:
            return {
                "standby": True,
                "error": False,
                "available": True,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }

        # 0 = normaler SMART health check auf aktiver Disk
        # Fehlertext enthält typischerweise FAILED / BAD
        if "FAILED" in combined or "BAD" in combined:
            return {
                "standby": False,
                "error": True,
                "available": True,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }

        # Bei 0 und ohne Fehler ist SMART ok, Device aktiv
        if result.returncode == 0:
            return {
                "standby": False,
                "error": False,
                "available": True,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }

        # Alles andere behandeln wir konservativ als "nicht standby bestätigt",
        # aber nicht automatisch als Fehler, damit wir keine falschen Error-LEDs
        # bei temporären Host-/Tool-Problemen setzen.
        return {
            "standby": False,
            "error": False,
            "available": False,
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }

    def _pick_color_config(self, disk_cfg, state):
        """
        Holt die passende Farb-Konfiguration aus der Config.

        Erwartete Zustände:
        - active
        - idle
        - standby
        - error

        Fallback:
        - wenn idle fehlt -> active
        - wenn state allgemein fehlt -> active
        """
        if state in disk_cfg:
            return disk_cfg[state]

        if state == "idle" and "active" in disk_cfg:
            return disk_cfg["active"]

        return disk_cfg.get("active")

    def _desired_state(self, led_name, dev_name):
        now = time.monotonic()
        stat = self._read_block_stat(dev_name)

        # Device / sysfs fehlt -> error
        if stat is None:
            return "error"

        previous = self.last_stat.get(led_name)

        # Initialisierung
        if previous is None:
            self.last_stat[led_name] = stat
            self.last_change[led_name] = now
        elif stat != previous:
            # Es gab I/O-Änderung -> als Aktivität merken
            self.last_stat[led_name] = stat
            self.last_change[led_name] = now

        # SMART / standby nur in definierten Intervallen prüfen
        if self.smart_check_enabled:
            if now - self.last_smart_check.get(led_name, 0) >= self.smart_interval:
                self.last_smart[led_name] = self._probe_smart(dev_name)
                self.last_smart_check[led_name] = now

        smart_info = self.last_smart.get(
            led_name,
            {
                "standby": False,
                "error": False,
                "available": False,
                "returncode": None,
                "stdout": "",
                "stderr": "",
            },
        )

        # Reihenfolge ist wichtig:
        # 1) error
        # 2) standby
        # 3) active
        # 4) idle
        if smart_info.get("error"):
            return "error"

        if smart_info.get("standby"):
            return "standby"

        age = now - self.last_change.get(led_name, now)

        if age <= self.active_hold_seconds:
            return "active"

        if age >= self.idle_after_seconds:
            return "idle"

        return "active"

    def _apply_disk_states(self):
        config = load_config()

        for led_name, dev_name in self.disk_map.items():
            if led_name not in config:
                continue

            state = self._desired_state(led_name, dev_name)
            self.current_state[led_name] = state

            disk_cfg = config[led_name]
            color_cfg = self._pick_color_config(disk_cfg, state)

            if not color_cfg:
                continue

            apply_key = (
                state,
                int(color_cfg.get("r", 0)),
                int(color_cfg.get("g", 0)),
                int(color_cfg.get("b", 0)),
                int(color_cfg.get("brightness", 255)),
            )

            # Nur bei echter Änderung neu setzen
            if self.last_applied.get(led_name) == apply_key:
                continue

            result = self.led_service.set_color(led_name, color_cfg)

            # Nur bei Erfolg den letzten Zustand übernehmen
            if result.get("success"):
                self.last_applied[led_name] = apply_key
            else:
                print(
                    f"[disk-monitor] failed to apply {led_name}={state}: {result}",
                    flush=True
                )

    def _loop(self):
        while True:
            try:
                self._apply_disk_states()
            except Exception as exc:
                print(f"[disk-monitor] {exc}", flush=True)

            time.sleep(self.poll_interval)
