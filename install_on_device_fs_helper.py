import os


def dir_exists(dir_name):
  try:
    return os.stat(dir_name)[0] == 16384
  except OSError:
    return False


def file_exists(filename):
  try:
    return (os.stat(filename)[0] & 0x4000) == 0
  except OSError:
    return False


def rmdir(dir_name):
  if dir_exists(dir_name):
    for i in os.ilistdir(dir_name):
      if i[1] == 16384:
        # print(f'Is directory: {i} -> {"{}/{}".format(dir_name, i[0])}')
        rmdir('{}/{}'.format(dir_name, i[0]))
      elif i[1] == 32768:
        # print(f'Is file: {i} -> {"{}/{}".format(dir_name, i[0])}')
        os.remove('{}/{}'.format(dir_name, i[0]))
      # else:
        # print(f'Unknown filehandle number: {i[1]}')
    os.rmdir(dir_name)


def main(dirs):
  for dr in dirs:
    print(f'Cleaning directory: {dr} (inclusive content)')
    rmdir(dr)


main(['phew', 'umqtt', 'enviro'])
