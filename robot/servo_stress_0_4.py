import time
import math
from pi_servo_hat import PiServoHat

CHANNELS = [0, 1, 2, 3, 4]
DURATION_S = 10.0
UPDATE_HZ = 100.0          # 100 updates/sec (fairly stressful but reasonable)
SWING_DEG = 180            # set 90 if you have 90° servos

# Keep within safe mechanical range to avoid slamming hard-stops
MIN_DEG = 15
MAX_DEG = 165
CENTER = (MIN_DEG + MAX_DEG) / 2.0
AMP = (MAX_DEG - MIN_DEG) / 2.0

hat = PiServoHat()

# Helpful guard: fail fast if the board isn't seen
if hasattr(hat, "is_connected") and not hat.is_connected():
    raise RuntimeError("Pi Servo pHAT not detected on I2C (expected addr 0x40).")

hat.restart()
hat.set_pwm_frequency(50)

print(f"Starting stress test on channels {CHANNELS} for {DURATION_S:.1f}s @ {UPDATE_HZ:.0f} Hz")
t0 = time.perf_counter()
next_t = t0

# Different phase offsets so they aren’t all trying to peak current at the same instant
phases = [0.0, 2*math.pi/5, 4*math.pi/5, 6*math.pi/5, 8*math.pi/5]
omega = 2 * math.pi * 1.5   # 1.5 Hz motion (adjust as you like)

updates = 0
while True:
    now = time.perf_counter()
    elapsed = now - t0
    if elapsed >= DURATION_S:
        break

    # Compute all target angles first, then write them out "together"
    for ch, ph in zip(CHANNELS, phases):
        angle = CENTER + AMP * math.sin(omega * elapsed + ph)
        hat.move_servo_position(ch, angle, swing=SWING_DEG)

    updates += 1

    # Print status ~5 times/sec
    if updates % int(UPDATE_HZ / 5) == 0:
        print(f"t={elapsed:5.2f}s  updates={updates}")

    # Rate control
    next_t += 1.0 / UPDATE_HZ
    sleep_dt = next_t - time.perf_counter()
    if sleep_dt > 0:
        time.sleep(sleep_dt)
    else:
        # If we fall behind, resync so we don't spiral
        next_t = time.perf_counter()

# Return servos to center and release outputs
for ch in CHANNELS:
    hat.move_servo_position(ch, CENTER, swing=SWING_DEG)
time.sleep(0.5)
hat.sleep()

print(f"Done. Total updates: {updates} (~{updates/DURATION_S:.0f} Hz actual)")
