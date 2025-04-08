import yaml
from typing import Any
from types import SimpleNamespace


def dict_to_namespace(obj: Any) -> Any:
    if isinstance(obj, dict):
        return SimpleNamespace(**{k: dict_to_namespace(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return [dict_to_namespace(item) for item in obj]
    else:
        return obj


def read_config(config_file: str = "config.yaml") -> SimpleNamespace:
    try:
        with open(config_file, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Configuration file not found: {config_file}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing the configuration file: {e}") from e

    if not isinstance(config, dict):
        raise ValueError("The configuration file must contain a top-level dictionary.")

    return dict_to_namespace(config)
