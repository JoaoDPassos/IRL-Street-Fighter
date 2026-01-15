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
    home_deg: float = 0
    margin_deg: float = 5.0

class Servo:
    """
    Represents one servo (configuration + last commanded position).
    Movement is executed through a shared ServoController.
    """
    def __init__(self, cfg: ServoConfig):
        self.cfg = cfg
        self.last_deg: Optional[float] = None

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
        self.hat.move_servo_position(servo.cfg.channel, deg, swing=servo.cfg.swing_deg)
        servo.last_deg = deg
        return deg

    def move_many(self, commands: Dict[Servo, float]) -> Dict[Servo, float]:
        """
        Issue several channel updates back-to-back (as 'simultaneous' as I2C allows).
        """
        results: Dict[Servo, float] = {}
        for s, d in commands.items():
            results[s] = self.move(s, d)
        return results

    def home_all(self) -> None:
        for s in self.servos.values():
            self.move(s, s.cfg.home_deg)

    def sleep(self) -> None:
        self.hat.sleep()
