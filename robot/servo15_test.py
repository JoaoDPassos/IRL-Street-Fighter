import time
import pi_servo_hat

SERVO_CH = 15          # you said your servo is on “number 15”
SWING_DEG = 180        # set 90 if you have a 90° servo

hat = pi_servo_hat.PiServoHat()

# Soft reset + defaults (docs note default 50 Hz, recommended for most servos)
hat.restart()

# Move to a few positions
hat.move_servo_position(SERVO_CH, 0,   swing=SWING_DEG)
time.sleep(1)

hat.move_servo_position(SERVO_CH, 90,  swing=SWING_DEG)
time.sleep(1)

hat.move_servo_position(SERVO_CH, 180, swing=SWING_DEG)
time.sleep(1)

hat.move_servo_position(SERVO_CH, 90,  swing=SWING_DEG)
time.sleep(1)

hat.move_servo_position(SERVO_CH, 0,   swing=SWING_DEG)
time.sleep(1)

# Optional: unpower outputs when done (preserves servo life)
hat.sleep()
