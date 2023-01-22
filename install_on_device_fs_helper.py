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


def rmdir(dir_name, only_print=False):
  if dir_exists(dir_name):
    for i in os.ilistdir(dir_name):
      if i[1] == 16384:
        # print(f'Is directory: {i} -> {"{}/{}".format(dir_name, i[0])}')
         rmdir('{}/{}'.format(dir_name, i[0]))
      elif i[1] == 32768:
        # print(f'Is file: {i} -> {"{}/{}".format(dir_name, i[0])}')
        target_path = '{}/{}'.format(dir_name, i[0])
        print(f'    {target_path}') if only_print else os.remove(target_path)
      # else:
        # print(f'Unknown filehandle number: {i[1]}')
    print(f'    {dir_name}') if only_print else os.rmdir(dir_name)
    return True
  return False


def main(dirs):
  for dr in dirs:
    print(f'> Cleaning directory: {dr} (inclusive content)', end='')
    if rmdir(dr):
      print(' .. done!')
    else:
      print(' .. skipped as directory does not exist on board!')
  print('> Left over directories and files on board after clean up:')
  rmdir('/', only_print=True)


main(['phew', 'umqtt', 'enviro', 'uploads'])
