"""Logic cảnh báo: LED, buzzer và LCD trạng thái qua GPIO/I2C."""
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


class _Buzzer:
    """Điều khiển buzzer chủ động; không hoạt động giả lập ngoài Raspberry Pi."""

    def __init__(self, pin: int) -> None:
        self._buzzer = None
        try:
            from gpiozero import Buzzer
            self._buzzer = Buzzer(pin)
        except Exception as exc:  # noqa: BLE001
            log.warning("Buzzer (GPIO%d) không khả dụng: %s", pin, exc)

    def set(self, on: bool) -> None:
        if self._buzzer is not None:
            self._buzzer.on() if on else self._buzzer.off()

    def close(self) -> None:
        if self._buzzer is not None:
            self._buzzer.off()
            self._buzzer.close()


class _StatusLCD:
    """LCD 1602 I2C; tự vô hiệu hóa và ghi log nếu phần cứng không khả dụng."""

    _MESSAGES = {
        config.STATUS_GOOD: ("TU THE TOT", "NGOI DUNG"),
        config.STATUS_SLOUCH: ("SAI: NGOI GU", "HAY NGHOI THANG"),
        config.STATUS_LEAN: ("SAI: NGHIENG", "HAY NGHOI THANG"),
        config.STATUS_HEAD_DOWN: ("SAI: CUI DAU", "HAY NANG DAU LEN"),
        config.STATUS_NO_PERSON: ("CHUA THAY NGUOI", "DANG CHO..."),
        config.STATUS_UNKNOWN: ("KHONG RO TU THE", "CHINH GOC CAM"),
    }

    def __init__(self) -> None:
        self._lcd = None
        self._last_lines = None
        try:
            from RPLCD.i2c import CharLCD
            self._lcd = CharLCD(
                "PCF8574", address=config.LCD_I2C_ADDRESS, port=config.LCD_I2C_BUS,
                cols=16, rows=2, charmap="A00", auto_linebreaks=False,
                backlight_enabled=True,
            )
            self.update(config.STATUS_NO_PERSON)
        except Exception as exc:  # noqa: BLE001
            log.warning("LCD 1602 I2C không khả dụng: %s", exc)
            self._lcd = None

    def update(self, status: str) -> None:
        if self._lcd is None:
            return
        lines = self._MESSAGES.get(status, self._MESSAGES[config.STATUS_UNKNOWN])
        if lines == self._last_lines:
            return
        try:
            for row, text in enumerate(lines):
                self._lcd.cursor_pos = (row, 0)
                self._lcd.write_string(text[:16].ljust(16))
            self._last_lines = lines
        except Exception:  # noqa: BLE001
            log.exception("Không thể cập nhật LCD; tắt cập nhật LCD")
            self._lcd = None

    def close(self) -> None:
        if self._lcd is not None:
            self._lcd.close()


@dataclass
class AlertState:
    status: str
    is_alert: bool
    color: tuple
    green_on: bool
    red_on: bool
    bad_seconds: float


class AlertManager:
    """LED/LCD phản ánh tư thế hiện tại; buzzer kêu nhịp khi tư thế sai."""

    def __init__(self) -> None:
        self.green = _Led(config.LED_GREEN_PIN, "green")
        self.red = _Led(config.LED_RED_PIN, "red")
        self.buzzer = _Buzzer(config.BUZZER_PIN)
        self.lcd = _StatusLCD()
        self._bad_since: Optional[float] = None

    def update(self, status: str, now: Optional[float] = None) -> AlertState:
        now = time.monotonic() if now is None else now
        bad_seconds = 0.0

        if status in config.BAD_STATUSES:
            if self._bad_since is None:
                self._bad_since = now
            bad_seconds = now - self._bad_since
        else:
            self._bad_since = None

        red_on = status in config.BAD_STATUSES
        green_on = status == config.STATUS_GOOD
        self.red.set(red_on)
        self.green.set(green_on)
        self.lcd.update(status)

        interval = config.BUZZER_BEEP_INTERVAL_SEC
        duration = config.BUZZER_BEEP_DURATION_SEC
        buzzer_on = red_on and interval > 0 and bad_seconds % interval < duration
        self.buzzer.set(buzzer_on)

        if red_on:
            color = COLOR_BAD
        elif green_on:
            color = COLOR_GOOD
        else:
            color = COLOR_NEUTRAL
        return AlertState(status, red_on, color, green_on, red_on, bad_seconds)

    def close(self) -> None:
        self.green.close()
        self.red.close()
        self.buzzer.close()
        self.lcd.close()
