import sys
from collections import OrderedDict

from enviro import ENVIRO_VERSION
from enviro.custom_constants import ENVIRO_VERSION_CUSTOM_POSTFIX
from enviro.custom_readings import _config_key_exists_with_enabling_value
from enviro.helpers import file_exists


def get_system_info_readings():
  system_info_readings = OrderedDict()

  system_info_readings['hardware'] = []

  if _config_key_exists_with_enabling_value('system_info'):
    system_info_readings['system_version'] = _get_sys_version_info()

  if _config_key_exists_with_enabling_value('enviro_version_info'):
    system_info_readings['enviro_version'] = _get_enviro_version_info()

  if _config_key_exists_with_enabling_value('git_rev_info'):
    system_info_readings['git_info'] = _get_git_rev()

  return system_info_readings


def _get_sys_version_info() -> str:
  sys_info = 'Unknown'

  sys_version_split = sys.version.split('; ')
  if len(sys_version_split) > 1:
    sys_info = f"{sys_version_split[1]}"

  return sys_info


def _get_enviro_version_info() -> str:
  return f'{ENVIRO_VERSION}-{ENVIRO_VERSION_CUSTOM_POSTFIX}'


def _get_git_rev() -> str:
  branch = 'UNKNOWN'
  commit = 'UNKNOWN'

  if file_exists('git_rev_infos.txt'):
    with open('git_rev_infos.txt', 'r') as f:
      for line in f.readlines():
        if line.to_lower().startswith('branch'):
          branch = _get_info_value(line, branch)
        if line.to_lower().startswith('commit'):
          commit = _get_info_value(line, commit)

  return f"{branch} - {commit}"


def _get_info_value(line, default_value) -> str:
    if line.contains('='):
      return line.split('=')[-1]
    else:
      return line if line else default_value
