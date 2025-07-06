from collections import OrderedDict

import config
from enviro.telemetry import get_telemetry_readings
from enviro.system_info import get_system_info_readings


def add_custom_readings(readings: OrderedDict) -> OrderedDict:
  custom_readings = OrderedDict()

  telemetry_readings = get_telemetry_readings()
  if telemetry_readings:
    custom_readings['telemetry'] = {**telemetry_readings}

  system_info_readings = get_system_info_readings()
  if system_info_readings:
    custom_readings['system_info'] = {**system_info_readings}

  return {**readings, **custom_readings} if custom_readings else readings


def _config_key_exists_with_enabling_value(key: str) -> bool:
  return hasattr(config, key) and getattr(config, key, False)
