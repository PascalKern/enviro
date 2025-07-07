from ucollections import OrderedDict

import machine

from enviro.custom_helpers import is_custom_config_active
from enviro.hw_helpers import get_pad, set_pad, CPU_TEMP


def get_telemetry_readings() -> OrderedDict:
  telemetry_readings = OrderedDict()

  if is_custom_config_active('enable_voltage_sensing'):
    telemetry_readings["voltage"] = get_battery_voltage()

  if is_custom_config_active('enable_cpu_temperature_sensing'):
    telemetry_readings["cpu_temp"] = get_cpu_temperature()

  if is_custom_config_active('enable_power_source_sensing'):
    telemetry_readings["power_source"] = get_power_source()

  return telemetry_readings


ADC_VOLT_CONVERSION = 3.3 / 65535


def get_battery_voltage(adc_voltage_sample_count:int = 10):
  battery_voltage = 0

  old_pad = get_pad(29)
  set_pad(29, 128)  # no pulls, no output, no input

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
  cpu_temp = 0

  reading = CPU_TEMP.read_u16() * ADC_VOLT_CONVERSION
  if reading > 0:
    cpu_temp = 27 - (reading - 0.706) / 0.001721
  return cpu_temp


def get_power_source():
  if _is_running_on_usb_power():
    return "USB"
  else:
    return "Battery"


def _is_running_on_usb_power():
  # Could also use vbus_present but like it to be more clear and not to import just a variable from
  # maybe changing __init__.py:
  ## from enviro import vbus_present
  ## return True if vbus_present == 1 else False

  # The bellow probe_vbus_activ_pin would also belong to the constants.py but as for the vbus_present
  # this wasn't done either I'd rather keep it here and do not touch the constants.py file!
  probe_vbus_activ_pin = 'WL_GPIO2'  # WL_GPIO2 is NOT the same as GPIO2 aka HOLD_VSYS_EN_PIN

  usb_power_detection = machine.Pin(probe_vbus_activ_pin, machine.Pin.IN)
  return True if usb_power_detection.value() == 1 else False
