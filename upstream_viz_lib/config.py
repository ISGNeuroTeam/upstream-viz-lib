import locale
import os
import yaml

from pathlib import Path

from enum import Enum

from ot_simple_connector.connector import Connector


base_src_dir = Path(__file__).parent


# try to read path to config from environment
conf_path_env = os.environ.get('UPSTREAM_VIZ_CONFIG', '')

if conf_path_env:
    default_config_yaml_path = Path(conf_path_env).resolve()
else:
    default_config_yaml_path = base_src_dir / 'config.yaml'

get_data_conf_env = os.environ.get('UPSTREAM_VIZ_DATA_CONFIG', '')

if get_data_conf_env:
    default_data_config_yaml_path = Path(get_data_conf_env).resolve()
else:
    default_data_config_yaml_path = base_src_dir / 'get_data.yaml'


def get_conf(file_path=default_config_yaml_path):
    with open(file_path, "r", encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_data_conf(file_path=default_data_config_yaml_path):
    return get_conf(file_path)


def get_rest_connector(file_path=default_config_yaml_path):
    conf = get_conf(file_path)
    conf_rest = {
        k: v
        for k, v in conf["rest"].items()
    }
    return Connector(**conf_rest)


def get_data_folder(file_path=default_config_yaml_path):
    conf = get_conf(file_path)
    return conf["data"]["path"]


def with_locale(value, precision):
    locale.setlocale(locale.LC_ALL, "")
    return locale.format_string(f"%10.{precision}f", value, grouping=True)


CURRENT_THEME = "light"
RED_COLOR = "#fcccbb" if CURRENT_THEME == "light" else "#8b0000"
YELLOW_COLOR = "#fff0ce" if CURRENT_THEME == "light" else "#ffcc00"


class Color(Enum):
    RED_LIGHT = "#fcccbb"
    RED_DARK = "#8b0000"
    YELLOW_LIGHT = "#fff0ce"
    YELLOW_DARK = "#ffcc00"
