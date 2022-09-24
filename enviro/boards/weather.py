import time, math
from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from machine import Pin, PWM
from pimoroni import Analog
from enviro import i2c, hold_vsys_en_pin, RAIN_PIN
import enviro.helpers as helpers
from phew import logging

RAIN_MM_PER_TICK = 0.2794

# bme280 = BreakoutBME280(i2c, 0x77)
# ltr559 = BreakoutLTR559(i2c)

wind_direction_pin = Analog(26)
wind_speed_pin = Pin(9, Pin.IN, Pin.PULL_UP)


current_pin_mapping = {
  2: 'HOLD_VSYS_EN_PIN',
  3: 'EXTERNAL_INTERRUPT_PIN',  # Reset
  4: 'I2C_SDA_PIN',
  5: 'I2C_SCL_PIN',
  6: 'ACTIVITY_LED_PIN',
  7: 'BUTTON_PIN',  # Poke Button
  8: 'RTC_ALARM_PIN',
  9: 'WIND_SPEED_PIN',
  10: 'RAIN_PIN',
  26: 'WIND_DIRECTION_PIN',  # Analog
}


def get_pins_from_gpiostat(stat: int, keep_lows: bool = False) -> typing.Iterable[int]:
  result = []
  for pin in range(32):
    mask = (1 << pin)
    if stat & mask:
      result.append(pin)
    else:
      if keep_lows:
        result.append(0)
  return result


def startup():
  import wakeup

  wake_state = wakeup.get_gpio_state()

  # check if rain sensor triggered wake
  rain_sensor_trigger = wake_state & (1 << 10)

  if rain_sensor_trigger:
    # read the current rain entries
    rain_entries = []
    if helpers.file_exists("rain.txt"):
      with open("rain.txt", "r") as rainfile:
        rain_entries = rainfile.read().split("\n")

    # add new entry
    logging.info("> add new rain trigger at {helpers.datetime_string()}")
    datetime_string = helpers.datetime_string()
    rain_entries.append(datetime_string)

    # limit number of entries to 190 - each entry is 21 bytes including
    # newline so this keeps the total rain.txt filesize just under one 
    # filesystem block (4096 bytes)
    rain_entries = rain_entries[-190:]

    # write out adjusted rain log
    with open("rain.txt", "w") as rainfile:
      rainfile.write("\n".join(rain_entries))

    with open("gpio_state.txt", "a") as gpio_state_file:
      gpio_state_file.write(f'{helpers.datetime_string()}\t{wake_state}\n')

    # go immediately back to sleep, we'll wake up at next scheduled reading
    hold_vsys_en_pin.init(Pin.IN)

  else:
    logging.debug(f'Weather StartUp! Rainsensor-Trigger: {rain_sensor_trigger}, GPIO State: {wake_state}')
    pins = [f"{pin_nr}: {current_pin_mapping.get(pin_nr)}" for pin_nr in get_pins_from_gpiostat(wake_state)]
    logging.debug(f'Active pins: {pins}')


def wind_speed(sample_time_ms=1000):  
  # get initial sensor state
  state = wind_speed_pin.value()

  # create an array for each sensor to log the times when the sensor state changed
  # then we can use those values to calculate an average tick time for each sensor
  ticks = []
  
  start = time.ticks_ms()
  while time.ticks_ms() - start <= sample_time_ms:
    now = wind_speed_pin.value()
    if now != state: # sensor output changed
      # record the time of the change and update the state
      ticks.append(time.ticks_ms())
      state = now

  # if no sensor connected then we have no readings, skip
  if len(ticks) < 2:
    return 0

  # calculate the average tick between transitions in ms
  average_tick_ms = (ticks[-1] - ticks[0]) / (len(ticks) - 1)

  # work out rotation speed in hz (two ticks per rotation)
  rotation_hz = (1000 / average_tick_ms) / 2

  # calculate the wind speed in metres per second
  radius = 7.0
  circumference = radius * 2.0 * math.pi
  factor = 0.0218  # scaling factor for wind speed in m/s
  wind_m_s = rotation_hz * circumference * factor

  return wind_m_s

def wind_direction():
  # adc reading voltage to cardinal direction taken from our python
  # library - each array index represents a 45 degree step around
  # the compass (index 0 == 0, 1 == 45, 2 == 90, etc.)
  # we find the closest matching value in the array and use the index
  # to determine the heading
  ADC_TO_DEGREES = (0.9, 2.0, 3.0, 2.8, 2.5, 1.5, 0.3, 0.6)

  closest_index = -1
  last_index = None

  # ensure we have two readings that match in a row as otherwise if
  # you read during transition between two values it can glitch
  # fixes https://github.com/pimoroni/enviro/issues/20
  while True:
    value = wind_direction_pin.read_voltage()

    closest_index = -1
    closest_value = float('inf')

    for i in range(8):
      distance = abs(ADC_TO_DEGREES[i] - value)
      if distance < closest_value:
        closest_value = distance
        closest_index = i

    if last_index == closest_index:
      break
      
    last_index = closest_index

  return closest_index * 45

def timestamp(dt):
  year = int(dt[0:4])
  month = int(dt[5:7])
  day = int(dt[8:10])
  hour = int(dt[11:13])
  minute = int(dt[14:16])
  second = int(dt[17:19])
  return time.mktime((year, month, day, hour, minute, second, 0, 0))
  
def rainfall():
  if not helpers.file_exists("rain.txt"):
    return 0

  now = timestamp(helpers.datetime_string())
  with open("rain.txt", "r") as rainfile:
    rain_entries = rainfile.read().split("\n")

  # count how many rain ticks in past hour
  amount = 0
  for entry in rain_entries:
    if entry:
      ts = timestamp(entry)
      if now - ts < 60 * 60:
        amount += RAIN_MM_PER_TICK

  return amount

def get_sensor_readings():
  # bme280 returns the register contents immediately and then starts a new reading
  # we want the current reading so do a dummy read to discard register contents first
#  bme280.read()
#  time.sleep(0.1)
#  bme280_data = bme280.read()

#  ltr_data = ltr559.get_reading()

  from ucollections import OrderedDict
  return OrderedDict({
#    "temperature": round(bme280_data[0], 2),
#    "humidity": round(bme280_data[2], 2),
#    "pressure": round(bme280_data[1] / 100.0, 2),
#    "light": round(ltr_data[BreakoutLTR559.LUX], 2),
    "wind_speed": wind_speed(),
    "rain": rainfall(),
    "wind_direction": wind_direction()
  })
  
