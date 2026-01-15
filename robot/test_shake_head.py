import time
from servo_control import ServoController, Servo, ServoConfig

# Channels: 0 base, 1 right arm, 2 left arm, 3 head
base = Servo(ServoConfig(channel=0, name="base", swing_deg=180, home_deg=90))
right_arm = Servo(ServoConfig(channel=1, name="right_arm", swing_deg=180, home_deg=90))
left_arm = Servo(ServoConfig(channel=2, name="left_arm", swing_deg=180, home_deg=90))
head = Servo(ServoConfig(channel=3, name="head_yaw", swing_deg=180, home_deg=90))

ctrl = ServoController(pwm_hz=50)

for s in (base, right_arm, left_arm, head):
    ctrl.register(s)

# Go to home pose
ctrl.move_many({
    base: base.cfg.home_deg,
    right_arm: right_arm.cfg.home_deg,
    left_arm: left_arm.cfg.home_deg,
    head: head.cfg.home_deg
})
time.sleep(0.5)

# Shake head: left-right around center
center = head.cfg.home_deg
amount = 20          # degrees left/right from center
times = 4            # number of left-right cycles
half_period = 0.25   # seconds (so one full cycle = 0.5s)

for _ in range(times):
    ctrl.move(head, center + amount)  # turn one way
    time.sleep(half_period)
    ctrl.move(head, center - amount)  # turn the other way
    time.sleep(half_period)

# Return to center and release outputs
ctrl.move(head, center)
time.sleep(0.3)
ctrl.sleep()
