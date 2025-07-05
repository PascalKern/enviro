import machine


def get_pad(gpio):
  return machine.mem32[0x4001c000 | (4 + (4 * gpio))]


def set_pad(gpio, value):
  machine.mem32[0x4001c000 | (4 + (4 * gpio))] = value
