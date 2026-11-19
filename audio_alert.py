
import subprocess
from pathlib import Path


class AudioAlertPlayer:
    """
    Phát âm thanh MP3 tương ứng với trạng thái tư thế.

    SLOUCH    -> slouch.mp3
    LEAN      -> lean.mp3
    HEAD_DOWN -> head_down.mp3

    Âm thanh chỉ phát một lần khi trạng thái chuyển sang
    một tư thế sai mới.
    """

    STATUS_AUDIO = {
        "SLOUCH": "slouch.mp3",
        "LEAN": "lean.mp3",
        "HEAD_DOWN": "head_down.mp3",
    }

    def __init__(self):
        self.audio_dir = Path(__file__).resolve().parent

        self.process = None
        self.current_status = None

    def stop(self):
        """Dừng âm thanh đang phát."""

        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()

                try:
                    self.process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()

            self.process = None

    def update(self, status):
        """
        Cập nhật âm thanh theo trạng thái nhận diện.

        Chỉ phát lại khi trạng thái thay đổi.
        """

        status = str(status).upper()

        # Không thay đổi trạng thái: không phát lại
        if status == self.current_status:
            return

        # Dừng âm thanh trước đó
        self.stop()

        self.current_status = status

        # Lấy file âm thanh tương ứng
        filename = self.STATUS_AUDIO.get(status)

        # GOOD, NO_PERSON, UNKNOWN: không phát âm thanh
        if filename is None:
            return

        audio_path = self.audio_dir / filename

        if not audio_path.exists():
            print(f"[AUDIO] Không tìm thấy file: {audio_path}")
            return

        try:
            self.process = subprocess.Popen(
                ["mpg123", "-q", str(audio_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            print(f"[AUDIO] Đang phát: {filename}")

        except FileNotFoundError:
            print("[AUDIO] Chưa cài mpg123!")

        except Exception as error:
            print(f"[AUDIO] Lỗi phát âm thanh: {error}")

    def close(self):
        """Dọn dẹp khi tắt chương trình."""

        self.stop()
        self.current_status = None
