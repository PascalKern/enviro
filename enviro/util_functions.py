import ujson
import sys

import machine

from enviro import ENVIRO_VERSION, GIT_REV

ADC_VOLT_CONVERSATION = 3.3 / 65535


def set_pad(gpio, value):
  machine.mem32[0x4001c000 | (4 + (4 * gpio))] = value


def get_pad(gpio):
  return machine.mem32[0x4001c000 | (4 + (4 * gpio))]


def get_battery_voltage():
  old_pad = get_pad(29)
  set_pad(29, 128)  # no pulls, no output, no input

  sample_count = 10
  battery_voltage = 0
  for i in range(0, sample_count):
    battery_voltage += _read_vsys_voltage()
  battery_voltage /= sample_count
  battery_voltage = round(battery_voltage, 3)
  set_pad(29, old_pad)
  return battery_voltage


def _read_vsys_voltage():
  adc_Vsys = machine.ADC(3)
  return adc_Vsys.read_u16() * 3.0 * ADC_VOLT_CONVERSATION


def get_sys_version_info():
  if ('GIT_REV' in globals() or 'GIT_REV' in locals()) and GIT_REV is not None:
    return ujson.dumps({'enviro': ENVIRO_VERSION, 'git_rev': GIT_REV, 'system': f"{sys.version.split('; ')[1]}"})
  else:
    return ujson.dumps({'enviro': ENVIRO_VERSION, 'git_rev': 'UNKNOWN', 'system': f"{sys.version.split('; ')[1]}"})
