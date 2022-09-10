import logging
import typing

from enviro.constants import *

import machine, os

# miscellany
# ===========================================================================
def datetime_string():
  dt = machine.RTC().datetime()
  return "{0:04d}-{1:02d}-{2:02d}T{4:02d}:{5:02d}:{6:02d}Z".format(*dt)

def date_string():
  dt = machine.RTC().datetime()
  return "{0:04d}-{1:02d}-{2:02d}".format(*dt)

def uid():
  return "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(*machine.unique_id())

# file management helpers
# ===========================================================================
def file_size(filename):
  try:
    return os.stat(filename)[6]
  except OSError:
    return None

def file_exists(filename):
  try:
    return (os.stat(filename)[0] & 0x4000) == 0
  except OSError:
    return False

def make_file_save(file: str) -> bool:
  from pathlib import Path
  fle = Path(file)
  return make_file_save(fle.name, fle.parent)

def make_file_save(filename: str, directory: typing.Optional[str] = None) -> bool:
  if directory:
    mkdir_safe(directory)
  if not file_exists(filename):
    try:
      from pathlib import Path
      fle = Path(f'{f"{directory}/" if directory else ""}{filename}')
      fle.touch(exist_ok=True)
      return True
    except Exception as e:
      logging.error(f'Failed to create file: {fle}', e)
      return False

def mkdir_safe(path):
  try:
    os.mkdir(path)
  except OSError as e:
    if e.errno != errno.EEXIST:
      raise
    pass # directory already exists, this is fine

def copy_file(source, target):
  with open(source, "rb") as infile:
    with open(target, "wb") as outfile:
      while True:
        chunk = infile.read(1024)
        if not chunk:
          break
        outfile.write(chunk)
