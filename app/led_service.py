import os
import subprocess


class MockLedService:
    def status(self):
        return {
            "mode": "mock",
            "cli_path": None,
            "ready": True
        }

    def set_color(self, target, color):
        return {
            "mode": "mock",
            "success": True,
            "command": f"{target} -on -color {color['r']} {color['g']} {color['b']}"
        }

    def apply_config(self, config):
        commands = []

        commands.append(
            f"power -on -color {config['power']['r']} {config['power']['g']} {config['power']['b']}"
        )
        commands.append(
            f"netdev -on -color {config['netdev']['r']} {config['netdev']['g']} {config['netdev']['b']}"
        )

        for disk in ("disk1", "disk2", "disk3", "disk4"):
            c = config[disk]["active"]
            commands.append(f"{disk} -on -color {c['r']} {c['g']} {c['b']}")

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

    def set_color(self, target, color):
        if not os.path.exists(self.cli_path):
            return {
                "mode": "real",
                "success": False,
                "error": f"CLI not found: {self.cli_path}"
            }

        result = self._run([
            target, "-on",
            "-color", str(color["r"]), str(color["g"]), str(color["b"])
        ])

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

        power = config["power"]
        results.append(self._run([
            "power", "-on",
            "-color", str(power["r"]), str(power["g"]), str(power["b"])
        ]))

        netdev = config["netdev"]
        results.append(self._run([
            "netdev", "-on",
            "-color", str(netdev["r"]), str(netdev["g"]), str(netdev["b"])
        ]))

        for disk in ("disk1", "disk2", "disk3", "disk4"):
            c = config[disk]["active"]
            results.append(self._run([
                disk, "-on",
                "-color", str(c["r"]), str(c["g"]), str(c["b"])
            ]))

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
