import time

from servo import ServoController
from robot import Robot, RobotConfig

def main():
    # Create controller (50 Hz is standard for most hobby servos)
    ctrl = ServoController(pwm_hz=50)

    # Your channel mapping:
    # 0 = base, 3 = head, 1 = right arm, 2 = left arm
    cfg = RobotConfig(
        base_ch=0,
        head_yaw_ch=3,
        right_arm_ch=1,
        left_arm_ch=2,

        # Home angles (adjust if “forward” isn’t 90)
        base_home=90,
        head_yaw_home=90,
        right_arm_home=90,
        left_arm_home=90,

        margin_deg=5.0
    )

    robot = Robot(ctrl, cfg)

    try:
        print("Homing...")
        robot.home()
        time.sleep(0.75)

        # Call gestures if they exist
        if hasattr(robot, "shake_head"):
            print("Shake head...")
            robot.shake_head(times=2, amount_deg=20, period_s=0.5)
            time.sleep(0.5)

        if hasattr(robot, "wave"):
            print("Wave right arm...")
            robot.wave(which="right", times=3, amount_deg=25, period_s=0.5)
            time.sleep(0.5)

            print("Wave left arm...")
            robot.wave(which="left", times=3, amount_deg=25, period_s=0.5)
            time.sleep(0.5)

        if hasattr(robot, "scan_base"):
            print("Scan base...")
            robot.scan_base(duration_s=3.0, speed_hz=0.6, amplitude_deg=30)
            time.sleep(0.5)

        if hasattr(robot, "celebrate"):
            print("Celebrate!")
            robot.celebrate(duration_s=6.0)
            time.sleep(0.5)

        print("Back to home...")
        robot.home()
        time.sleep(0.75)

    finally:
        print("Sleeping outputs...")
        robot.sleep()

if __name__ == "__main__":
    main()
