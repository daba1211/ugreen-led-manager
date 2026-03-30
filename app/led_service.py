import os
import subprocess


def _brightness_value(config):
    value = int(config.get("brightness", 255))
    return max(0, min(255, value))


class MockLedService:
    def status(self):
        return {
            "mode": "mock",
            "cli_path": None,
            "ready": True
        }

    def set_color(self, target, config):
        return {
            "mode": "mock",
            "success": True,
            "command": (
                f"{target} -on -color {config['r']} {config['g']} {config['b']} "
                f"-brightness {_brightness_value(config)}"
            )
        }

    def apply_config(self, config):
        commands = []

        commands.append(
            f"power -on -color {config['power']['r']} {config['power']['g']} {config['power']['b']} "
            f"-brightness {_brightness_value(config['power'])}"
        )
        commands.append(
            f"netdev -on -color {config['netdev']['r']} {config['netdev']['g']} {config['netdev']['b']} "
            f"-brightness {_brightness_value(config['netdev'])}"
        )


        return {
            "mode": "mock",
            "applied": True,
            "commands": commands
        }

    def all_off(self):
        return {
            "mode": "mock",
            "success": True,
            "commands": ["all -off"]
        }


class CliLedService:
    def __init__(self):
        self.cli_path = os.environ.get("LED_CLI_PATH", "/opt/ugreen-led/bin/ugreen_leds_cli")

    def status(self):
        return {
            "mode": "real",
            "cli_path": self.cli_path,
            "ready": os.path.exists(self.cli_path)
        }

    def _run(self, args):
        cmd = [self.cli_path] + args
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    def _run_set(self, target, config):
        return self._run([
            target,
            "-on",
            "-color", str(config["r"]), str(config["g"]), str(config["b"]),
            "-brightness", str(_brightness_value(config))
        ])

    def set_color(self, target, config):
        if not os.path.exists(self.cli_path):
            return {
                "mode": "real",
                "success": False,
                "error": f"CLI not found: {self.cli_path}"
            }

        result = self._run_set(target, config)

        return {
            "mode": "real",
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }

    def apply_config(self, config):
        if not os.path.exists(self.cli_path):
            return {
                "mode": "real",
                "applied": False,
                "error": f"CLI not found: {self.cli_path}"
            }

        results = []
        results.append(self._run_set("power", config["power"]))
        results.append(self._run_set("netdev", config["netdev"]))

        return {
            "mode": "real",
            "applied": all(r.returncode == 0 for r in results),
            "results": [
                {
                    "returncode": r.returncode,
                    "stdout": r.stdout.strip(),
                    "stderr": r.stderr.strip()
                }
                for r in results
            ]
        }

    def all_off(self):
        if not os.path.exists(self.cli_path):
            return {
                "mode": "real",
                "success": False,
                "error": f"CLI not found: {self.cli_path}"
            }

        result = self._run(["all", "-off"])

        return {
            "mode": "real",
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }


def get_led_service():
    mode = os.environ.get("LED_MODE", "mock").lower()
    if mode == "real":
        return CliLedService()
    return MockLedService()
