from ucollections import OrderedDict

from enviro.telemetry import get_telemetry_readings
from enviro.system_info import get_system_info_readings


def add_custom_readings(readings: OrderedDict) -> OrderedDict:

  telemetry_readings = get_telemetry_readings()
  if telemetry_readings:
    readings['telemetry'] = telemetry_readings

  system_info_readings = get_system_info_readings()
  if system_info_readings:
    readings['system_info'] = system_info_readings

  return readings

