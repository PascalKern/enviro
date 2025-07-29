from ucollections import OrderedDict

from enviro.telemetry import get_telemetry_readings
from enviro.device_and_source_info import get_system_infos, get_release_infos


def add_custom_readings(sensor_readings: OrderedDict, config_module, logging_module) -> OrderedDict:
  """
  :param sensor_readings: The sensor readings as returned by the board. See bellow for the structure.
  :param logging_module: The logging from phew or any other possible logging framework
  :param config_module: The base config from enviro.
  :returns sensor_readings augmented with custom readings if enabled in the config AND compatible with the destination.
  :rtype OrderedDict

  **NOTE**: Does (yet) **only work with MQTT** destination! To add custom readings support for these destinations, the
  payload setup/preparation needs to be extended.

  The sensor_readings structure and later finalization when uploading (originally):
  Received readings have the following structure:

  .. code-block:: python
  {
    'sensor_value_a': 123,
    'sensor_value_b': 456,
    ...
  }

  and will be finalized for caching (uploading) to the following structure:

  .. code-block:: python
  {
    'nickname':   config.nickname,
    'timestamp':  helpers.datetime_string(),
    'readings':   readings,   # This will be the content of the sensor_readings.
    'model':      model,
    'uid':        helpers.uid()
  }

  Within this method the sensor_readings will be updated, depending on the custom
  configuration **AND** the configure destination as mentioned earlier, to the following structure:

  .. code-block:: python
  {
    'sensors': {
      'sensor_value_a': 123,
      'sensor_value_b': 456,
      ...
    },
    'telemetry': {
      'telemetry_a': 12,
      ...
    },
    'system_infos': {},
    'release_infos': {}
  }

  The finalization will be the same as with the default / stock source version!
  """

  if config_module.destination in ['influxdb', 'adafruit_io']:
    logging_module.debug(f"  - custom readings are not yet supported for destination '{config_module.destination}'")
    return sensor_readings
  else:
    logging_module.debug(f"  - augment readings with custom readings from depending on the given custom configuration...")
    new_readings = OrderedDict()
    new_readings['sensors'] = sensor_readings

    telemetry_readings = get_telemetry_readings()
    if telemetry_readings:
      new_readings['telemetry'] = telemetry_readings

    system_infos = get_system_infos()
    if system_infos:
      new_readings['system_infos'] = system_infos

    release_infos = get_release_infos()
    if release_infos:
      new_readings['release_infos'] = release_infos

    return new_readings

