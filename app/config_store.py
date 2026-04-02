import json
import os
from copy import deepcopy

from app.defaults import DEFAULT_CONFIG

DISK_KEYS = ("disk1", "disk2", "disk3", "disk4")
ALLOWED_TOP_LEVEL_KEYS = ("power", "netdev", *DISK_KEYS)
ALLOWED_DISK_STATES = ("active", "standby", "error")


def _merge_dict(defaults, current):
    result = deepcopy(defaults)
    for key, value in current.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def _normalize_config(config):
    merged = _merge_dict(DEFAULT_CONFIG, config or {})

    for key in list(merged.keys()):
        if key not in ALLOWED_TOP_LEVEL_KEYS:
            merged.pop(key, None)

    for disk_name in DISK_KEYS:
        disk_cfg = merged.get(disk_name, {})
        if not isinstance(disk_cfg, dict):
            merged[disk_name] = deepcopy(DEFAULT_CONFIG[disk_name])
            continue

        normalized_disk_cfg = {}
        for state in ALLOWED_DISK_STATES:
            value = disk_cfg.get(state, deepcopy(DEFAULT_CONFIG[disk_name][state]))
            if isinstance(value, dict):
                normalized_disk_cfg[state] = value
            else:
                normalized_disk_cfg[state] = deepcopy(DEFAULT_CONFIG[disk_name][state])

        merged[disk_name] = normalized_disk_cfg

    return merged


def get_config_path():
    return os.environ.get("LED_CONFIG_PATH", "config/led-config.json")


def load_config():
    path = get_config_path()
    if not os.path.exists(path):
        return deepcopy(DEFAULT_CONFIG)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return _normalize_config(data)


def save_config(config):
    path = get_config_path()
    normalized = _normalize_config(config)

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, indent=2)
