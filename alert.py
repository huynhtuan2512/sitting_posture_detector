#BỔ SUNG
"""
Logic cảnh báo:
- LED xanh / LED đỏ qua GPIO.
- LCD 1602 qua I2C.
- Phát âm thanh MP3 qua MAX98357A (I2S).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import config
from alert_audio import AudioAlertPlayer

log = logging.getLogger(__name__)


# Màu BGR cho OpenCV
COLOR_GOOD = (0, 200, 0)
COLOR_BAD = (0, 0, 255)
COLOR_NEUTRAL = (160, 160, 160)


class _Led:
    """Bọc gpiozero.LED; tự động no-op nếu không chạy trên Raspberry Pi."""

    def __init__(self, pin: int, name: str) -> None:
        self.name = name
        self._led = None

        try:
            from gpiozero import LED
            self._led = LED(pin)

        except Exception as exc:  # noqa: BLE001
            log.warning(
                "LED %s (GPIO%d) không khả dụng, chạy chế độ giả lập: %s",
                name,
                pin,
                exc,
            )

    def set(self, on: bool) -> None:
        if self._led is not None:
            self._led.on() if on else self._led.off()

    def close(self) -> None:
        if self._led is not None:
            self._led.off()
            self._led.close()


class _StatusLCD:
    """LCD 1602 I2C; tự vô hiệu hóa nếu phần cứng không khả dụng."""

    _MESSAGES = {
        config.STATUS_GOOD: (
            "TU THE TOT",
            "NGOI DUNG",
        ),
        config.STATUS_SLOUCH: (
            "SAI: NGOI GU",
            "HAY NGOI THANG",
        ),
        config.STATUS_LEAN: (
            "SAI: NGHIENG",
            "HAY NGOI THANG",
        ),
        config.STATUS_HEAD_DOWN: (
            "SAI: CUI DAU",
            "HAY NANG DAU LEN",
        ),
        config.STATUS_NO_PERSON: (
            "CHUA THAY NGUOI",
            "DANG CHO...",
        ),
        config.STATUS_UNKNOWN: (
            "KHONG RO TU THE",
            "CHINH GOC CAM",
        ),
    }

    def __init__(self) -> None:
        self._lcd = None
        self._last_lines = None

        try:
            from RPLCD.i2c import CharLCD

            self._lcd = CharLCD(
                "PCF8574",
                address=config.LCD_I2C_ADDRESS,
                port=config.LCD_I2C_BUS,
                cols=16,
                rows=2,
                charmap="A00",
                auto_linebreaks=False,
                backlight_enabled=True,
            )

            self.update(config.STATUS_NO_PERSON)

        except Exception as exc:  # noqa: BLE001
            log.warning(
                "LCD 1602 I2C không khả dụng: %s",
                exc,
            )
            self._lcd = None

    def update(self, status: str) -> None:
        if self._lcd is None:
            return

        lines = self._MESSAGES.get(
            status,
            self._MESSAGES[config.STATUS_UNKNOWN],
        )

        if lines == self._last_lines:
            return

        try:
            for row, text in enumerate(lines):
                self._lcd.cursor_pos = (row, 0)
                self._lcd.write_string(text[:16].ljust(16))

            self._last_lines = lines

        except Exception:  # noqa: BLE001
            log.exception(
                "Không thể cập nhật LCD; tắt cập nhật LCD"
            )
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
    """
    Quản lý cảnh báo tư thế:

    GOOD:
        - LED xanh bật.
        - LED đỏ tắt.
        - Không phát âm thanh.

    SLOUCH:
        - LED đỏ bật.
        - Phát slouch.mp3.

    LEAN:
        - LED đỏ bật.
        - Phát lean.mp3.

    HEAD_DOWN:
        - LED đỏ bật.
        - Phát head_down.mp3.

    NO_PERSON / UNKNOWN:
        - Hai LED tắt.
        - Dừng âm thanh.
    """

    def __init__(self) -> None:
        # Khởi tạo LED
        self.green = _Led(
            config.LED_GREEN_PIN,
            "green",
        )

        self.red = _Led(
            config.LED_RED_PIN,
            "red",
        )

        # Khởi tạo LCD
        self.lcd = _StatusLCD()

        # Khởi tạo bộ phát âm thanh MAX98357A
        self.audio = AudioAlertPlayer()

        # Thời điểm bắt đầu tư thế sai liên tục
        self._bad_since: Optional[float] = None

        log.info(
            "AlertManager initialized: LED, LCD, Audio"
        )

    def update(
        self,
        status: str,
        now: Optional[float] = None,
    ) -> AlertState:
        """
        Cập nhật cảnh báo theo trạng thái tư thế.

        AudioAlertPlayer.update() chỉ phát âm thanh khi
        trạng thái thay đổi, tránh phát lặp liên tục.
        """

        now = time.monotonic() if now is None else now

        bad_seconds = 0.0

        # Kiểm tra trạng thái sai
        if status in config.BAD_STATUSES:

            if self._bad_since is None:
                self._bad_since = now

            bad_seconds = now - self._bad_since

        else:
            self._bad_since = None

        # Xác định trạng thái LED
        red_on = status in config.BAD_STATUSES
        green_on = status == config.STATUS_GOOD

        # Cập nhật LED
        self.red.set(red_on)
        self.green.set(green_on)

        # Cập nhật LCD
        self.lcd.update(status)

        # Phát âm thanh tương ứng với tư thế
        try:
            self.audio.update(status)

        except Exception:
            log.exception(
                "Lỗi khi cập nhật cảnh báo âm thanh"
            )

        # Xác định màu trạng thái cho giao diện
        if red_on:
            color = COLOR_BAD

        elif green_on:
            color = COLOR_GOOD

        else:
            color = COLOR_NEUTRAL

        return AlertState(
            status=status,
            is_alert=red_on,
            color=color,
            green_on=green_on,
            red_on=red_on,
            bad_seconds=bad_seconds,
        )

    def close(self) -> None:
        """Giải phóng toàn bộ tài nguyên phần cứng."""

        log.info("Closing AlertManager...")

        # Tắt LED
        self.green.close()
        self.red.close()

        # Đóng LCD
        self.lcd.close()

        # Dừng và giải phóng bộ phát âm thanh
        try:
            self.audio.close()

        except Exception:
            log.exception(
                "Lỗi khi đóng AudioAlertPlayer"
            )

        log.info("AlertManager closed.")
