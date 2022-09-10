import time, math
from breakout_bme280 import BreakoutBME280
from breakout_ltr559 import BreakoutLTR559
from machine import Pin, PWM
from pimoroni import Analog
from enviro import i2c, hold_vsys_en_pin, wake_reason_name, WAKE_REASON_RAIN_TRIGGER
import enviro.helpers
from phew import logging

RAIN_MM_PER_TICK = 0.2794

bme280 = BreakoutBME280(i2c, 0x77)
ltr559 = BreakoutLTR559(i2c)

piezo_pwm = PWM(Pin(28))

wind_direction_pin = Analog(26)
wind_speed_pin = Pin(9, Pin.IN, Pin.PULL_UP)

def startup():
  import wakeup  
  # check if rain sensor triggered wake
  rain_sensor_trigger = wakeup.get_gpio_state() & (1 << 10)
  if rain_sensor_trigger:
    # log the wake reason
    logging.info("  - board startup - wake reason:", wake_reason_name(WAKE_REASON_RAIN_TRIGGER))
    # read the current rain entries
    rain_entries = []
    
    #readings_filename = f"readings/{helpers.date_string()}.txt"
    #new_file = not helpers.file_exists(readings_filename)
    #with open(readings_filename, "a") as f:
      
    enviro.helpers.mkdir_safe("rain_readings")
    rain_readings_file = "rain_readings/rain.txt"
    new_file = enviro.helpers.file_exists(rain_readings_file)
    if new_file:
      with open(rain_readings_file, "rw") as rainfile:
        rain_entries = rainfile.read().split("\n")

    # add new entry
    rain_entries.append(enviro.helpers.datetime_string())

    # limit number of entries to 190 - each entry is 21 bytes including
    # newline so this keeps the total rain.txt filesize just under one 
    # filesystem block (4096 bytes)
    rain_entries = rain_entries[-190:]

    # write out adjusted rain log
    with open(rain_readings_file, "w") as rainfile:
      rainfile.write("\n".join(rain_entries))

    # go immediately back to sleep, we'll wake up at next scheduled reading
    hold_vsys_en_pin.init(Pin.IN)

    ### Bellow code copied from enviro.__init__.py Except the import and button_pin lines
    ### also the remote_mount part is here disabled
    import machine
    from machine import rtc
    from enviro import BUTTON_PIN, stop_activity_led
    button_pin = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)

    # if we're still awake it means power is coming from the USB port in which
    # case we can't (and don't need to) sleep.
    stop_activity_led()

    # if running via mpremote/pyboard.py with a remote mount then we can't
    # reset the board so just exist
  #  if phew.remote_mount:
  #    sys.exit()

    # we'll wait here until the rtc timer triggers and then reset the board
    logging.debug("  - board startup - on usb power (so can't shutdown) halt and reset instead")
    while not rtc.read_alarm_flag():
      time.sleep(0.25)

      if button_pin.value():  # allow button to force reset
        break

    logging.debug("  - board startup - reset")

    # reset the board
    machine.reset()

def wind_speed(sample_time_ms=500):  
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
  if not enviro.helpers.file_exists("rain_readings/rain.txt"):
    return 0

  now = timestamp(enviro.helpers.datetime_string())
  with open("rain_readings/rain.txt", "r") as rainfile:
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
  bme280.read()
  time.sleep(0.1)
  bme280_data = bme280.read()

  ltr_data = ltr559.get_reading()

  from ucollections import OrderedDict
  return OrderedDict({
    "temperature": round(bme280_data[0], 2),
    "humidity": round(bme280_data[2], 2),
    "pressure": round(bme280_data[1] / 100.0, 2),
    "light": round(ltr_data[BreakoutLTR559.LUX], 2),
    "wind_speed": wind_speed(),
    "rain": rainfall(),
    "wind_direction": wind_direction()
  })
  