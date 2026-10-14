"""Logic cảnh báo: màu overlay + điều khiển LED xanh/đỏ qua GPIO (gpiozero)."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import config

log = logging.getLogger(__name__)

# Màu BGR cho OpenCV
COLOR_GOOD = (0, 200, 0)
COLOR_BAD = (0, 0, 255)
COLOR_NEUTRAL = (160, 160, 160)


class _Led:
    """Bọc gpiozero.LED; tự động no-op nếu không chạy trên Raspberry Pi."""

    def __init__(self, pin: int, name: str) -> None:
        self.name, self._led = name, None
        try:
            from gpiozero import LED
            self._led = LED(pin)
        except Exception as exc:  # noqa: BLE001
            log.warning("LED %s (GPIO%d) không khả dụng, chạy chế độ giả lập: %s", name, pin, exc)

    def set(self, on: bool) -> None:
        if self._led is not None:
            self._led.on() if on else self._led.off()

    def close(self) -> None:
        if self._led is not None:
            self._led.off()
            self._led.close()


@dataclass
class AlertState:
    status: str
    is_alert: bool
    color: tuple
    green_on: bool
    red_on: bool
    bad_seconds: float


class AlertManager:
    """Debounce trạng thái: chỉ báo đỏ khi sai tư thế liên tục >= BAD_POSTURE_HOLD_SEC."""

    def __init__(self) -> None:
        self.green = _Led(config.LED_GREEN_PIN, "green")
        self.red = _Led(config.LED_RED_PIN, "red")
        self._bad_since: Optional[float] = None
        self._good_since: Optional[float] = None
        self._alerting = False

    def update(self, status: str, now: Optional[float] = None) -> AlertState:
        now = time.monotonic() if now is None else now
        bad_seconds = 0.0

        if status in config.BAD_STATUSES:
            self._good_since = None
            self._bad_since = self._bad_since or now
            bad_seconds = now - self._bad_since
            if bad_seconds >= config.BAD_POSTURE_HOLD_SEC:
                self._alerting = True
        elif status == config.STATUS_GOOD:
            self._bad_since = None
            self._good_since = self._good_since or now
            if now - self._good_since >= config.GOOD_POSTURE_HOLD_SEC:
                self._alerting = False
        else:  # NO_PERSON / UNKNOWN
            self._bad_since = self._good_since = None
            self._alerting = False

        tracking = status in (config.STATUS_GOOD, *config.BAD_STATUSES)
        red_on = self._alerting
        green_on = tracking and not self._alerting
        self.red.set(red_on)
        self.green.set(green_on)

        if red_on:
            color = COLOR_BAD
        elif tracking:
            color = COLOR_GOOD
        else:
            color = COLOR_NEUTRAL
        return AlertState(status, red_on, color, green_on, red_on, bad_seconds)

    def close(self) -> None:
        self.green.close()
        self.red.close()
