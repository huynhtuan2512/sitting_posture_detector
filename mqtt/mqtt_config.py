
"""Cấu hình kết nối MQTT cho Raspberry Pi."""

import os

# ==========================================
# MQTT BROKER
# ==========================================

# Giai đoạn kiểm thử nếu Mosquitto cài trên chính Raspberry Pi:
BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))

USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")

KEEPALIVE = 60

# ID duy nhất của Raspberry Pi
DEVICE_ID = os.getenv("MQTT_DEVICE_ID", "raspi_01")

# Tiền tố Topic
TOPIC_PREFIX = "sitting"

# ==========================================
# MQTT TOPICS
# ==========================================

BASE_TOPIC = f"{TOPIC_PREFIX}/{DEVICE_ID}"

TOPIC_TELEMETRY = f"{BASE_TOPIC}/telemetry"
TOPIC_ALERTS = f"{BASE_TOPIC}/alerts"
TOPIC_STATUS = f"{BASE_TOPIC}/status"
TOPIC_COMMAND = f"{BASE_TOPIC}/command"
TOPIC_COMMAND_ACK = f"{BASE_TOPIC}/command/ack"
TOPIC_HEARTBEAT = f"{BASE_TOPIC}/heartbeat"

# ==========================================
# QOS
# ==========================================

QOS_TELEMETRY = 0
QOS_ALERTS = 1
QOS_STATUS = 1
QOS_COMMAND = 1
QOS_COMMAND_ACK = 1
QOS_HEARTBEAT = 0

# ==========================================
# PUBLISH INTERVALS
# ==========================================

# Gửi telemetry định kỳ nếu trạng thái không đổi
TELEMETRY_INTERVAL = 2.0

# Gửi heartbeat mỗi 30 giây
HEARTBEAT_INTERVAL = 30.0
