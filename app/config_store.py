import json
import os
from copy import deepcopy

from app.defaults import DEFAULT_CONFIG


def _merge_dict(defaults, current):
    result = deepcopy(defaults)
    for key, value in current.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def get_config_path():
    return os.environ.get("LED_CONFIG_PATH", "config/led-config.json")


def load_config():
    path = get_config_path()
    if not os.path.exists(path):
        return deepcopy(DEFAULT_CONFIG)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return _merge_dict(DEFAULT_CONFIG, data)


def save_config(config):
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
