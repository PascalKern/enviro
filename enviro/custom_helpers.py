import time

from uio import StringIO
from umachine import RTC
from pcf85063a import PCF85063A

import custom_config
from pimoroni_i2c import PimoroniI2C

from enviro.helpers import mkdir_safe, copy_file, file_size


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
  while any(item == 0 for item in t) and max_tries > 0:
    max_tries -= 1
    time.sleep_ms(2)
    t = rtc.datetime()
  try:
    RTC().datetime((t[0], t[1], t[2], t[6], t[3], t[4], t[5], 0))  # synch PR2040 rtc too
  except Exception as e:
    print(f"Failed to sync Pico RTC: {e}. Tuple: {t!r}.")
  return rtc


def check_cached_file_is_not_empty(cache_file_name: str, upload_file: StringIO) -> bool:
  """

  :param cache_file_name: The name of the file in the uploads directory to check, e.g. ``'2023-01-01_12-00-00.json'``.
  :param upload_file: The file object returned by `open` for the cache_file.
  :return: bool: True if the cache file is not empty, False otherwise.
  """
  if file_size(f'uploads/{cache_file_name}'):
    return True
  else:
    current_pos = upload_file.tell()  # Should be 0 anyway but better safe than sorry.
    first_eight_bytes = upload_file.read(8)
    if str == type(first_eight_bytes) and len(first_eight_bytes) > 0: # We seem to have some data in the file. Hopefully it's also a valid json!
      upload_file.seek(current_pos) # Reset the reading position for later effective read for the upload!
      return True
    else:
      return False


def move_incompatible_file_out_of_uploads_dir(cache_file_name: str):
  mkdir_safe('impossible_uploads')
  failing_file = f'uploads/{cache_file_name}'
  copy_file(failing_file, f'impossible_uploads/{cache_file_name}')
