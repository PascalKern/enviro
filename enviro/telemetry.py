from collections import OrderedDict

import machine

import config
from enviro.hw_helpers import get_pad, set_pad, CPU_TEMP


def add_telemetry_readings(readings: OrderedDict) -> OrderedDict:
  telemetry_readings = OrderedDict()

  if _config_key_exists_with_enabling_value('enable_voltage_sensing'):
    telemetry_readings["voltage"] = get_battery_voltage()

  if _config_key_exists_with_enabling_value('enable_cpu_temperature_sensing'):
    telemetry_readings["cpu_temp"] = get_cpu_temperature()

  return {**readings, 'telemetry': {**telemetry_readings}} if telemetry_readings else readings


def _config_key_exists_with_enabling_value(key: str) -> bool:
  return hasattr(config, key) and getattr(config, key, False)


ADC_VOLT_CONVERSION = 3.3 / 65535


def get_battery_voltage(adc_voltage_sample_count:int = 10):
  old_pad = get_pad(29)
  set_pad(29, 128)  # no pulls, no output, no input

  battery_voltage = 0
  for i in range(0, adc_voltage_sample_count):
    battery_voltage += _read_vsys_voltage()
  battery_voltage /= adc_voltage_sample_count
  battery_voltage = round(battery_voltage, 3)
  set_pad(29, old_pad)
  return battery_voltage


def _read_vsys_voltage():
  adc_volt_conversion = 3.3 / 65535
  adc_vsys = machine.ADC(3)
  return adc_vsys.read_u16() * 3.0 * adc_volt_conversion


def get_cpu_temperature():
  reading = CPU_TEMP.read_u16() * ADC_VOLT_CONVERSION
  return 27 - (reading - 0.706) / 0.001721
