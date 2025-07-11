from ucollections import OrderedDict

from enviro.telemetry import get_telemetry_readings
from enviro.system_info import get_device_environment_infos


def add_custom_readings(sensor_readings: OrderedDict) -> OrderedDict:
  """
  Received readings have the following structure:
  {
    'sensor_value_a': 123,
    'sensor_value_b': 456,
    ...
  }
  and will be finalized for caching (uploading) to the following structure:
  {
    'nickname':   config.nickname,
    'timestamp':  helpers.datetime_string(),
    'readings':   readings,
    'model':      model,
    'uid':        helpers.uid()
  }
  :param sensor_readings:
  :return:
  """

  new_readings = OrderedDict()
  new_readings['sensors'] = sensor_readings

  telemetry_readings = get_telemetry_readings()
  if telemetry_readings:
    new_readings['telemetry'] = telemetry_readings

  system_info_readings = get_device_environment_infos()
  if system_info_readings:
    if 'system_infos' in system_info_readings:
      new_readings['system_infos'] = system_info_readings['system_infos']

    if 'release_infos' in system_info_readings:
      new_readings['release_infos'] = system_info_readings['release_infos']

  return new_readings

