import time
from pi_servo_hat import PiServoHat

CHANNEL = 1        # change to your channel
FREQ_HZ = 50       # datasheet allows 50-330 Hz; 50 is standard
STEP_US = 50       # step size for the sweep
DWELL = 0.10       # seconds between steps

MIN_US = 500
NEUTRAL_US = 1500
MAX_US = 2500

def us_to_duty(us: int, freq_hz: int) -> float:
    period_us = 1_000_000.0 / freq_hz
    return (us / period_us) * 100.0

hat = PiServoHat()
hat.restart()
hat.set_pwm_frequency(FREQ_HZ)

# go to neutral first
hat.set_duty_cycle(CHANNEL, us_to_duty(NEUTRAL_US, FREQ_HZ))
time.sleep(0.5)

print("Sweeping pulse width. Measure the total rotation from MIN to MAX.")
print("If you hit a hard stop or buzzing, stop and reduce your range.\n")

# sweep up
for us in range(MIN_US, MAX_US + 1, STEP_US):
    duty = us_to_duty(us, FREQ_HZ)
    hat.set_duty_cycle(CHANNEL, duty)
    print(f"us={us:4d}  duty={duty:5.2f}%")
    time.sleep(DWELL)

time.sleep(0.5)

# sweep back down
for us in range(MAX_US, MIN_US - 1, -STEP_US):
    duty = us_to_duty(us, FREQ_HZ)
    hat.set_duty_cycle(CHANNEL, duty)
    time.sleep(DWELL)

# return to neutral and release outputs
hat.set_duty_cycle(CHANNEL, us_to_duty(NEUTRAL_US, FREQ_HZ))
time.sleep(0.5)
hat.sleep()

print("Done.")
