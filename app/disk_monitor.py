import os
import subprocess
import threading
import time

from app.config_store import load_config


def _env_bool(name, default=False):
    value = os.environ.get(name, str(default)).strip().lower()
    return value in ("1", "true", "yes", "on")


def _parse_disk_map():
    raw = os.environ.get("LED_DISK_MAP", "disk1:sda,disk2:sdb,disk3:sdc,disk4:sdd")
    result = {}

    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        led_name, dev_name = part.split(":", 1)
        result[led_name.strip()] = dev_name.strip()

    return result


class DiskMonitor:
    def __init__(self, led_service):
        self.led_service = led_service
        self.enabled = _env_bool("LED_MONITOR_ENABLED", False)
        self.disk_map = _parse_disk_map()
        self.smart_device_type = os.environ.get("LED_SMART_DEVICE_TYPE", "ata").strip()
        self.poll_interval = float(os.environ.get("LED_POLL_INTERVAL", "5"))
        self.smart_interval = float(os.environ.get("LED_SMART_INTERVAL", "30"))
        self.active_hold_seconds = float(os.environ.get("LED_ACTIVE_HOLD_SECONDS", "15"))

        self.last_stat = {}
        self.last_change = {}
        self.last_smart = {}
        self.last_smart_check = {}
        self.last_applied = {}

    def start(self):
        if not self.enabled:
            return

        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def _read_block_stat(self, dev_name):
        path = f"/sys/block/{dev_name}/stat"
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            return None
        except OSError:
            return None

    def _probe_smart(self, dev_name):
        cmd = [
            "smartctl",
            "-n", "standby,3",
            "-H",
            "-d", self.smart_device_type,
            f"/dev/{dev_name}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        text = f"{result.stdout}\n{result.stderr}".upper()

        if result.returncode == 3:
            return {
                "standby": True,
                "error": False,
                "available": True
            }

        if "FAILED" in text or "BAD" in text:
            return {
                "standby": False,
                "error": True,
                "available": True
            }

        return {
            "standby": False,
            "error": False,
            "available": result.returncode == 0
        }

    def _desired_state(self, led_name, dev_name):
        now = time.monotonic()
        stat = self._read_block_stat(dev_name)

        if stat is None:
            return "error"

        previous = self.last_stat.get(led_name)
        if previous is None:
            self.last_stat[led_name] = stat
            self.last_change.setdefault(led_name, 0)
        elif stat != previous:
            self.last_stat[led_name] = stat
            self.last_change[led_name] = now

        if now - self.last_smart_check.get(led_name, 0) >= self.smart_interval:
            self.last_smart[led_name] = self._probe_smart(dev_name)
            self.last_smart_check[led_name] = now

        smart_info = self.last_smart.get(
            led_name,
            {"standby": False, "error": False, "available": False}
        )

        if smart_info.get("error"):
            return "error"

        if now - self.last_change.get(led_name, 0) <= self.active_hold_seconds:
            return "active"

        if smart_info.get("standby"):
            return "standby"

        return "active"

    def _apply_disk_states(self):
        config = load_config()

        for led_name, dev_name in self.disk_map.items():
            if led_name not in config:
                continue

            state = self._desired_state(led_name, dev_name)
            color = config[led_name][state]
            apply_key = (
                state,
                color["r"],
                color["g"],
                color["b"],
                int(color.get("brightness", 255))
            )
            
            if self.last_applied.get(led_name) == apply_key:
                continue

            self.led_service.set_color(led_name, color)
            self.last_applied[led_name] = apply_key

    def _loop(self):
        while True:
            try:
                self._apply_disk_states()
            except Exception as exc:
                print(f"[disk-monitor] {exc}", flush=True)

            time.sleep(self.poll_interval)
