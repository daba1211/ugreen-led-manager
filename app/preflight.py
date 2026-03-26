import os
import shutil
import subprocess


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


class PreflightChecker:
    def __init__(self):
        self.cli_path = os.environ.get("LED_CLI_PATH", "/opt/ugreen-led/bin/ugreen_leds_cli")
        self.i2c_device = os.environ.get("LED_I2C_DEVICE", "/dev/i2c-1")

    def _module_loaded(self, name):
        return os.path.exists(f"/sys/module/{name}")

    def check(self):
        cli_exists = os.path.exists(self.cli_path)
        i2c_dev_loaded = self._module_loaded("i2c_dev")
        led_ugreen_loaded = self._module_loaded("led_ugreen")
        i2c_device_exists = os.path.exists(self.i2c_device)
        modprobe_exists = shutil.which("modprobe") is not None

        ready = cli_exists and i2c_dev_loaded and not led_ugreen_loaded

        messages = []

        if not cli_exists:
            messages.append(f"CLI fehlt: {self.cli_path}")

        if not i2c_dev_loaded:
            messages.append("Kernel-Modul i2c_dev ist nicht geladen")

        if led_ugreen_loaded:
            messages.append("Kernel-Modul led_ugreen ist geladen und kollidiert mit der CLI")

        if not i2c_device_exists:
            messages.append(f"I2C-Gerät nicht gefunden: {self.i2c_device}")

        return {
            "ready": ready,
            "cli_exists": cli_exists,
            "cli_path": self.cli_path,
            "i2c_dev_loaded": i2c_dev_loaded,
            "led_ugreen_loaded": led_ugreen_loaded,
            "i2c_device_exists": i2c_device_exists,
            "i2c_device": self.i2c_device,
            "modprobe_available": modprobe_exists,
            "messages": messages,
        }

    def fix(self):
        actions = []

        if shutil.which("modprobe") is None:
            return {
                "success": False,
                "actions": actions,
                "error": "modprobe ist im Container nicht verfügbar"
            }

        load_i2c = _run(["modprobe", "i2c-dev"])
        actions.append({
            "action": "modprobe i2c-dev",
            "returncode": load_i2c.returncode,
            "stdout": load_i2c.stdout.strip(),
            "stderr": load_i2c.stderr.strip(),
        })

        unload_led = _run(["modprobe", "-r", "led_ugreen"])
        actions.append({
            "action": "modprobe -r led_ugreen",
            "returncode": unload_led.returncode,
            "stdout": unload_led.stdout.strip(),
            "stderr": unload_led.stderr.strip(),
        })

        status = self.check()

        return {
            "success": status["ready"],
            "actions": actions,
            "status": status,
        }
