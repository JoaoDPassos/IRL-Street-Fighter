# servo_control.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Dict, Optional, List
import time
import math

from pi_servo_hat import PiServoHat


@dataclass
class ServoConfig:
    channel: int                 # 0-15
    name: str = ""
    swing_deg: int = 180         
    invert: bool = False         # flip direction if mounted reversed

class Servo:
    """
    Represents one servo (configuration + last commanded position).
    Movement is executed through a shared ServoController.
    """
    def __init__(self, cfg: ServoConfig):
        self.cfg = cfg

class ServoController:
    """
    Owns the PiServoHat and provides safe movement commands.
    Create one controller, then create multiple Servo objects that use it.
    """
    def __init__(self, pwm_hz: int = 50, debug: int = 0):
        self.hat = PiServoHat(debug=debug)
        # If your library version has is_connected(), this is a good guard:
        if hasattr(self.hat, "is_connected") and not self.hat.is_connected():
            raise RuntimeError("Pi Servo pHAT not detected on I2C (expected addr 0x40).")

        self.hat.restart()
        self.hat.set_pwm_frequency(pwm_hz)

        self.servos: Dict[int, Servo] = {}

    def register(self, servo: Servo) -> None:
        ch = servo.cfg.channel
        if not (0 <= ch <= 15):
            raise ValueError(f"Channel must be 0..15, got {ch}")
        self.servos[ch] = servo

    def move(self, servo: Servo, deg: float) -> float:
        target = servo.clamp(deg)
        self.hat.move_servo_position(servo.cfg.channel, target, swing=servo.cfg.swing_deg)
        servo.last_deg = target
        return target

    def move_many(self, commands: Dict[Servo, float]) -> Dict[Servo, float]:
        """
        Issue several channel updates back-to-back (as 'simultaneous' as I2C allows).
        """
        results: Dict[Servo, float] = {}
        for s, d in commands.items():
            results[s] = self.move(s, d)
        return results

    def sleep(self) -> None:
        self.hat.sleep()


# ---- Example usage / quick test ----
if __name__ == "__main__":
    ctrl = ServoController(pwm_hz=50)

    s0 = Servo(ServoConfig(channel=0, name="base", home_deg=90))
    s1 = Servo(ServoConfig(channel=1, name="left_arm", home_deg=90))
    s2 = Servo(ServoConfig(channel=2, name="right_arm", home_deg=90))

    for s in [s0, s1, s2]:
        ctrl.register(s)

    ctrl.home_all()
    time.sleep(0.5)

    # Small coordinated motion for ~5 seconds
    t0 = time.perf_counter()
    phases = [0.0, 2*math.pi/5, 4*math.pi/5, 6*math.pi/5, 8*math.pi/5]
    servos: List[Servo] = [s0, s1, s2]

    while (time.perf_counter() - t0) < 5.0:
        t = time.perf_counter() - t0
        cmds = {}
        for s, ph in zip(servos, phases):
            angle = s.center + s.amp * math.sin(2 * math.pi * 1.0 * t + ph)
            cmds[s] = angle
        ctrl.move_many(cmds)
        time.sleep(0.01)

    ctrl.home_all()
    time.sleep(0.5)
    ctrl.sleep()
