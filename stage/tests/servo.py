"""Simple test for a standard servo on channel 0 and a continuous rotation servo on channel 1."""
import time
from adafruit_servokit import ServoKit

# Set channels to the number of servo channels on your kit.
# 8 for FeatherWing, 16 for Shield/HAT/Bonnet.
kit = ServoKit(channels=16)
cnt = 0
range_ = list(range(0, 180))  # type: list

while cnt < 5:
    for position in range_:
        for servo in range(0, 15):
            kit.servo[servo].angle = position
            # kit.servo[0].angle = position
            # print(servo, position)
        # time.sleep(0.02)
    range_.reverse()
    for position in range_:
        for servo in range(0, 15):
            kit.servo[servo].angle = position
            # kit.servo[0].angle = position
        # time.sleep(0.02)
    range_.reverse()
