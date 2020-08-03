"""Simple test for a standard servo on channel 0 and a continuous rotation servo on channel 1."""
import time
from adafruit_servokit import ServoKit

# Set channels to the number of servo channels on your kit.
# 8 for FeatherWing, 16 for Shield/HAT/Bonnet.
kit = ServoKit(channels=16)
cnt = 0
range_ = list(range(30, 120))  # type: list

while cnt < 5:
    for position in range_:
        for servo in range(1, 15):
            kit.servo[servo].angle = position
            print(servo, position)
            time.sleep(0.01)
    # time.sleep(1)
    range_.reverse()
    for position in range_:
        for servo in range(1, 15):
            kit.servo[servo].angle = position
            time.sleep(0.01)
    # time.sleep(1)
    # cnt += 1
    # if cnt == 5:
    #     for servo in range(1, 15):
    #         kit.servo[servo].angle = 90

# kit.servo[14].angle = 180
# kit.continuous_servo[1].throttle = 1.0
# time.sleep(1)
# kit.continuous_servo[1].throttle = -1.0
# time.sleep(1)
# kit.servo[14].angle = 0
# time.sleep(1)
# kit.servo[14].angle = 90
# kit.continuous_servo[1].throttle = 0
