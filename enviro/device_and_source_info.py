import sys

import re
from ucollections import OrderedDict

from enviro import ENVIRO_VERSION
from enviro.custom_constants import ENVIRO_VERSION_CUSTOM_POSTFIX
from enviro.custom_helpers import is_custom_config_active
from enviro.helpers import file_exists



def get_system_infos() -> OrderedDict:
  sys_info = OrderedDict()
  sys_info['enviro_micropython'] = 'UNKNOWN'
  sys_info['micropython'] = 'UNKNOWN'
  sys_info['machine'] = 'UNKNOWN'
  sys_info['mpy'] = 'UNKNOWN'
  sys_info['version'] = 'UNKNOWN'

  splitter = re.compile(r'(.*); *(.*), *(.*)')
  version, micropython, enviro_micropython = splitter.match(sys.version).groups()

  if version:
    sys_info['version'] = version
  if micropython:
    sys_info['micropython'] = micropython
  if enviro_micropython:
    sys_info['enviro_micropython'] = enviro_micropython

  if hasattr(sys.implementation, '_machine'):
    sys_info['machine'] = sys.implementation._machine
  if hasattr(sys.implementation, '_mpy'):
    sys_info['mpy'] = sys.implementation._mpy

  return sys_info


def get_release_infos() -> OrderedDict:
  release_infos = OrderedDict()
  release_infos['enviro_src_version'] = _get_enviro_version_info()
  release_infos['git_infos'] = _get_git_rev()
  return release_infos


def _get_enviro_version_info() -> str:
  return f'{ENVIRO_VERSION}.{ENVIRO_VERSION_CUSTOM_POSTFIX}' if ENVIRO_VERSION_CUSTOM_POSTFIX else ENVIRO_VERSION


def _get_git_rev() -> OrderedDict:
  git_info = OrderedDict()
  git_info['branch'] = 'UNKNOWN'
  git_info['commit'] = 'UNKNOWN'
  git_info['repo'] = 'UNKNOWN'

  for line in _read_git_rev_info():
    if line.lower().startswith('branch'):
      git_info['branch'] = _get_info_value(line, 'UNKNOWN')
    if line.lower().startswith('commit'):
      git_info['commit'] = _get_info_value(line, 'UNKNOWN')
    if line.lower().startswith('repo'):
      git_info['repo'] = _get_info_value(line, 'UNKNOWN')

  return git_info


def _read_git_rev_info() -> list[str]:
  lines = []
  if file_exists('git_rev_infos.txt'):
    with open('git_rev_infos.txt', 'r') as f:
      lines = f.readlines()
  return lines


def _get_info_value(line, default_value) -> str:
    if '=' in line:
      value = line.split('=')[-1].strip()
      return value if value else default_value
    else:
      return default_value
