"""Cấu hình trung tâm cho Posture Monitor. Chỉnh ngưỡng/chân GPIO tại đây."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ----------------------------- Model ---------------------------------
MODEL_PATH = BASE_DIR / "models" / "yolov8n-pose.onnx"
MODEL_INPUT_SIZE = 640        # Chỉ dùng khi model có input shape động
CONF_THRESHOLD = 0.50         # Ngưỡng tin cậy người
NMS_IOU_THRESHOLD = 0.45
KPT_CONF_THRESHOLD = 0.40     # Ngưỡng tin cậy từng keypoint
ORT_NUM_THREADS = 4           # Pi 4/5 có 4 nhân
ORT_PROVIDERS = ["CPUExecutionProvider"]

# ----------------------------- Camera --------------------------------
CAMERA_RESOLUTION = (640, 480)   # hoặc (1280, 720)
CAMERA_FPS = 30
CAMERA_HFLIP = False
CAMERA_VFLIP = False
ALLOW_WEBCAM_FALLBACK = False    # True: dùng cv2.VideoCapture(0) khi dev trên PC

# ----------------------------- Inference -----------------------------
INFERENCE_MAX_FPS = 15           # Giới hạn để tránh nghẽn CPU
ANGLE_EMA_ALPHA = 0.4            # Làm mượt góc (0..1, càng nhỏ càng mượt)

# ----------------------------- Trạng thái tư thế ---------------------
STATUS_GOOD = "GOOD"
STATUS_SLOUCH = "SLOUCH"         # Ngồi gù
STATUS_LEAN = "LEAN"             # Nghiêng
STATUS_HEAD_DOWN = "HEAD_DOWN"   # Cúi đầu
STATUS_NO_PERSON = "NO_PERSON"
STATUS_UNKNOWN = "UNKNOWN"       # Thấy người nhưng thiếu keypoint tai/vai/hông
BAD_STATUSES = {STATUS_SLOUCH, STATUS_LEAN, STATUS_HEAD_DOWN}

# Ngưỡng góc (độ) - điểm khởi đầu, hãy hiệu chỉnh theo vị trí đặt camera.
# Camera nên đặt nhìn NGANG (góc ~90°) để đo tai-vai-hông chính xác.
SLOUCH_ESH_MIN_DEG = 145.0       # Góc Tai-Vai-Hông < ngưỡng  -> gù
NECK_FORWARD_MAX_DEG = 30.0      # Góc (vai->tai) lệch phương thẳng đứng > ngưỡng -> cúi đầu
TRUNK_LEAN_MAX_DEG = 15.0        # Góc (hông->vai) lệch phương thẳng đứng > ngưỡng -> nghiêng
SHOULDER_TILT_MAX_DEG = 10.0     # Chỉ dùng khi nhìn chính diện: vai lệch ngang > ngưỡng -> nghiêng

# ----------------------------- GPIO (BCM) ----------------------------
LED_GREEN_PIN = 17               # Chân vật lý 11
LED_RED_PIN = 27                 # Chân vật lý 13
BUZZER_PIN = 22                  # Chân vật lý 15, buzzer chủ động
LCD_I2C_ADDRESS = 0x27           # Thường là 0x27 hoặc 0x3F
LCD_I2C_BUS = 1
BUZZER_BEEP_INTERVAL_SEC = 1.0
BUZZER_BEEP_DURATION_SEC = 0.2

# ----------------------------- Web -----------------------------------
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
JPEG_QUALITY = 70
