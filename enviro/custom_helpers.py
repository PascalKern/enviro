import time

from umachine import RTC
from pcf85063a import PCF85063A

import custom_config
from pimoroni_i2c import PimoroniI2C


def is_custom_config_active(key: str) -> bool:
  return hasattr(custom_config, key) and getattr(custom_config, key, False)

def initialize_rtc(i2c: PimoroniI2C, max_tries: int = 10) -> PCF85063A:
  # initialize the pcf85063a real time clock chip
  rtc = PCF85063A(i2c)
  i2c.writeto_mem(0x51, 0x00, b'\x00')  # ensure rtc is running (this should be default?)
  rtc.enable_timer_interrupt(False)
  t = rtc.datetime()
  # Bellow iteration should prevent (it does on my devices):
  # BUG ERRNO 22, EINVAL, when date read from RTC is invalid for the pico's RTC.
  # TODO Maybe need to check other indices like t[6], t[7] (t[1] can be 0 no clue why but can)?
  while any(item == 0 for item in t) and max_tries > 0:
    max_tries -= 1
    time.sleep_ms(2)
    t = rtc.datetime()
  try:
    RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))  # synch PR2040 rtc too
  except Exception as e:
    print(f"Failed to sync Pico RTC: {e}. Tuple: {t!r}.")
  return rtc