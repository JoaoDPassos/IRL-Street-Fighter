import time
from pi_servo_hat import PiServoHat

CHANNEL = 1      # change to the servo channel you’re calibrating
FREQ_HZ = 50     # servo supports 50–330 Hz; 50 Hz is standard
STEP_US = 25     # smaller = safer, slower
SETTLE_S = 0.25

NEUTRAL_US = 1500
START_MIN_US = 900    # start conservative; widen later
START_MAX_US = 2100

def us_to_duty(us: int, freq_hz: int) -> float:
    period_us = 1_000_000.0 / freq_hz
    return (us / period_us) * 100.0

def set_pulse_us(hat, ch, us):
    hat.set_duty_cycle(ch, us_to_duty(us, FREQ_HZ))

hat = PiServoHat()
hat.restart()
hat.set_pwm_frequency(FREQ_HZ)

print(f"Calibrating channel {CHANNEL} at {FREQ_HZ} Hz")
print("Tip: horn off the mechanism, no load. Stop BEFORE hard buzzing.\n")

# Go neutral first
set_pulse_us(hat, CHANNEL, NEUTRAL_US)
time.sleep(0.5)

# Sweep to find max
print("Finding MAX pulse width...")
max_ok = NEUTRAL_US
for us in range(NEUTRAL_US, START_MAX_US + 1, STEP_US):
    set_pulse_us(hat, CHANNEL, us)
    print(f"  us={us}")
    time.sleep(SETTLE_S)
    ans = input("Press Enter to continue, or type 'stop' if it buzzes/halts: ").strip().lower()
    if ans == "stop":
        break
    max_ok = us

# Back to neutral
set_pulse_us(hat, CHANNEL, NEUTRAL_US)
time.sleep(0.5)

# Sweep to find min
print("\nFinding MIN pulse width...")
min_ok = NEUTRAL_US
for us in range(NEUTRAL_US, START_MIN_US - 1, -STEP_US):
    set_pulse_us(hat, CHANNEL, us)
    print(f"  us={us}")
    time.sleep(SETTLE_S)
    ans = input("Press Enter to continue, or type 'stop' if it buzzes/halts: ").strip().lower()
    if ans == "stop":
        break
    min_ok = us

# Return neutral + release
set_pulse_us(hat, CHANNEL, NEUTRAL_US)
time.sleep(0.5)
hat.sleep()

print("\nRESULTS (safe endpoints you found):")
print(f"  min_us = {min_ok}")
print(f"  max_us = {max_ok}")
print(f"  neutral_us = {NEUTRAL_US}")
