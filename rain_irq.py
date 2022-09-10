import machine
from machine import Pin

# from enviro import RAIN_PIN # Always triggers startup!

RAIN_PIN = 10

irq_counter = 0
drop_counter = 0


def rain_interrup_callback(p):
  print(f'Pin change! Pin state: {p} and value: {p.value()}')
  global irq_counter
  irq_counter = irq_counter + 1


rain_pin = Pin(RAIN_PIN)
print(f'Rain Pin init state: {rain_pin} and value: {rain_pin.value()}')

# rain_pin.irq(trigger=Pin.IRQ_FALLING, handler=rain_interrup_callback)
rain_pin.irq(trigger=Pin.IRQ_RISING, handler=rain_interrup_callback, wake=machine.SLEEP | machine.DEEPSLEEP)
# rain_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=rain_interrup_callback)

import time

machine.enable_irq(1)

while True:
  print('Start with the loooooop')
  if irq_counter > 0:
    state = machine.disable_irq()
    irq_counter = irq_counter - 1
    print(f'Interupted State: {state}')
    machine.enable_irq(state)

    drop_counter = drop_counter + 1
    print(f'Another drop dopped! Total: {drop_counter}')

  #time.sleep(2)


