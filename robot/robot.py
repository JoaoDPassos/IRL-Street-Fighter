# robot.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict
import time
import math

from servo import ServoController, Servo, ServoConfig


@dataclass
class RobotConfig:
    # Channels
    base_ch: int = 0
    left_arm_ch: int = 1
    right_arm_ch: int = 2
    head_yaw_ch: int = 3  # horizontal swivel (yaw)

    # Swings (set per joint if needed)
    base_swing: int = 180
    arm_swing: int = 180
    head_yaw_swing: int = 180

    # Home positions (deg)
    base_home: float = 90.0
    left_arm_home: float = 90.0
    right_arm_home: float = 90.0
    head_yaw_home: float = 90.0

    # Invert flags if mounted reversed
    base_invert: bool = False
    left_arm_invert: bool = False
    right_arm_invert: bool = False
    head_yaw_invert: bool = False

    # Keep away from mechanical endpoints
    margin_deg: float = 5.0


class Robot:
    """
    Robot composed of 4 servos:
      - base (yaw)
      - left arm
      - right arm
      - head_yaw (horizontal swivel)
    Uses your ServoController.move / move_many API.
    """
    def __init__(self, ctrl: ServoController, cfg: RobotConfig = RobotConfig()):
        self.ctrl = ctrl
        self.cfg = cfg

        self.base = Servo(ServoConfig(
            channel=cfg.base_ch, name="base",
            swing_deg=cfg.base_swing, invert=cfg.base_invert,
            home_deg=cfg.base_home, margin_deg=cfg.margin_deg
        ))
        self.left_arm = Servo(ServoConfig(
            channel=cfg.left_arm_ch, name="left_arm",
            swing_deg=cfg.arm_swing, invert=cfg.left_arm_invert,
            home_deg=cfg.left_arm_home, margin_deg=cfg.margin_deg
        ))
        self.right_arm = Servo(ServoConfig(
            channel=cfg.right_arm_ch, name="right_arm",
            swing_deg=cfg.arm_swing, invert=cfg.right_arm_invert,
            home_deg=cfg.right_arm_home, margin_deg=cfg.margin_deg
        ))
        self.head_yaw = Servo(ServoConfig(
            channel=cfg.head_yaw_ch, name="head_yaw",
            swing_deg=cfg.head_yaw_swing, invert=cfg.head_yaw_invert,
            home_deg=cfg.head_yaw_home, margin_deg=cfg.margin_deg
        ))

        for s in (self.base, self.left_arm, self.right_arm, self.head_yaw):
            self.ctrl.register(s)

    # ---------- internal helpers ----------
    def _safe_deg(self, servo: Servo, deg: float) -> float:
        """
        Apply margin + optional invert. (Since your controller doesn't use these yet.)
        """
        d = float(deg)

        # clamp away from endpoints
        lo = servo.cfg.margin_deg
        hi = float(servo.cfg.swing_deg) - servo.cfg.margin_deg
        d = max(lo, min(hi, d))

        # invert if mounted reversed
        if servo.cfg.invert:
            d = float(servo.cfg.swing_deg) - d

        return d

    # ---------- basic joint controls ----------
    def move_joint(self, joint: str, deg: float) -> float:
        servo = getattr(self, joint)
        return self.ctrl.move(servo, self._safe_deg(servo, deg))

    def set_pose(
        self,
        *,
        base: Optional[float] = None,
        left_arm: Optional[float] = None,
        right_arm: Optional[float] = None,
        head_yaw: Optional[float] = None,
    ) -> None:
        """
        Move any subset of joints "simultaneously" via ctrl.move_many().
        """
        cmds: Dict[Servo, float] = {}
        if base is not None:
            cmds[self.base] = self._safe_deg(self.base, base)
        if left_arm is not None:
            cmds[self.left_arm] = self._safe_deg(self.left_arm, left_arm)
        if right_arm is not None:
            cmds[self.right_arm] = self._safe_deg(self.right_arm, right_arm)
        if head_yaw is not None:
            cmds[self.head_yaw] = self._safe_deg(self.head_yaw, head_yaw)

        if cmds:
            self.ctrl.move_many(cmds)

    def home(self) -> None:
        self.set_pose(
            base=self.base.cfg.home_deg,
            left_arm=self.left_arm.cfg.home_deg,
            right_arm=self.right_arm.cfg.home_deg,
            head_yaw=self.head_yaw.cfg.home_deg
        )

    def sleep(self) -> None:
        self.ctrl.sleep()

    # ---------- gestures ----------
    def shake_head(self, times: int = 2, amount_deg: float = 20.0, period_s: float = 0.5) -> None:
        """
        Head 'no' gesture (yaw left-right).
        """
        center = self.head_yaw.last_deg if self.head_yaw.last_deg is not None else self.head_yaw.cfg.home_deg
        for _ in range(times):
            self.set_pose(head_yaw=center + amount_deg)
            time.sleep(period_s / 2)
            self.set_pose(head_yaw=center - amount_deg)
            time.sleep(period_s / 2)
        self.set_pose(head_yaw=center)

    def wave(self, which: str = "right", times: int = 3, amount_deg: float = 25.0, period_s: float = 0.5) -> None:
        """
        Simple arm wave by oscillating one arm about its home.
        """
        arm = self.right_arm if which.lower().startswith("r") else self.left_arm
        center = arm.cfg.home_deg
        for _ in range(times):
            self.ctrl.move(arm, self._safe_deg(arm, center + amount_deg))
            time.sleep(period_s / 2)
            self.ctrl.move(arm, self._safe_deg(arm, center - amount_deg))
            time.sleep(period_s / 2)
        self.ctrl.move(arm, self._safe_deg(arm, center))

    def scan_base(self, duration_s: float = 3.0, speed_hz: float = 0.6, amplitude_deg: float = 35.0) -> None:
        """
        Rotate base left-right while keeping arms/head at home.
        """
        self.home()
        time.sleep(0.2)

        center = self.base.cfg.home_deg
        t0 = time.perf_counter()

        while (time.perf_counter() - t0) < duration_s:
            t = time.perf_counter() - t0
            base_angle = center + amplitude_deg * math.sin(2 * math.pi * speed_hz * t)
            self.set_pose(base=base_angle)
            time.sleep(0.01)

    def celebrate(
    self,
    duration_s: float = 6.0,
    update_hz: float = 50.0,
    base_amp: float = 25.0,
    head_amp: float = 20.0,
    arms_amp: float = 35.0,
    base_hz: float = 0.8,
    head_hz: float = 1.2,
    arms_hz: float = 2.0,
    ) -> None:
        """
        Celebrate gesture:
        - base sways left/right
        - head yaws left/right
        - both arms go up/down TOGETHER (same commanded angle)
        """

        # Start from home pose
        self.home()
        time.sleep(0.2)

        dt = 1.0 / float(update_hz)
        t0 = time.perf_counter()
        next_t = t0

        base_center = self.base.cfg.home_deg
        head_center = self.head_yaw.cfg.home_deg
        arms_center = self.right_arm.cfg.home_deg  # both arms use same center

        while True:
            now = time.perf_counter()
            t = now - t0
            if t >= duration_s:
                break

            base_angle = base_center + base_amp * math.sin(2 * math.pi * base_hz * t)
            head_angle = head_center + head_amp * math.sin(2 * math.pi * head_hz * t + math.pi / 6.0)

            # Arms move together (in-phase)
            arms_angle = arms_center + arms_amp * math.sin(2 * math.pi * arms_hz * t)

            # Apply safety/inversion helper (so you don’t hit endpoints)
            cmds = {
                self.base: self._safe_deg(self.base, base_angle),
                self.head_yaw: self._safe_deg(self.head_yaw, head_angle),
                self.right_arm: self._safe_deg(self.right_arm, arms_angle),
                self.left_arm: self._safe_deg(self.left_arm, arms_angle),
            }
            self.ctrl.move_many(cmds)

            # rate control
            next_t += dt
            sleep_dt = next_t - time.perf_counter()
            if sleep_dt > 0:
                time.sleep(sleep_dt)
            else:
                next_t = time.perf_counter()

        # Return to home at the end
        self.home()





