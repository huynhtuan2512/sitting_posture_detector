
"""Định nghĩa MQTT Topic và JSON Payload."""

import json
import uuid
from datetime import datetime, timezone, timedelta

from mqtt.mqtt_config import (
    DEVICE_ID,
    TOPIC_TELEMETRY,
    TOPIC_ALERTS,
    TOPIC_STATUS,
    TOPIC_COMMAND,
    TOPIC_COMMAND_ACK,
    TOPIC_HEARTBEAT,
)


def current_timestamp():
    """Lấy thời gian hiện tại theo múi giờ Việt Nam."""
    vn_timezone = timezone(timedelta(hours=7))

    return datetime.now(vn_timezone).isoformat(timespec="seconds")


def encode_payload(data):
    """Chuyển dictionary thành JSON string."""
    return json.dumps(
        data,
        ensure_ascii=False,
        separators=(",", ":")
    )


def decode_payload(payload):
    """Chuyển JSON string thành dictionary."""
    return json.loads(payload)


# ==========================================
# TELEMETRY
# ==========================================

def build_telemetry(
    posture,
    confidence=None,
    angles=None,
    person_detected=True
):
    return {
        "device_id": DEVICE_ID,
        "posture": posture,
        "confidence": confidence,
        "angles": angles or {},
        "person_detected": person_detected,
        "timestamp": current_timestamp()
    }


# ==========================================
# ALERT
# ==========================================

def build_alert(alert_type, severity="WARNING", message=""):
    return {
        "event_id": str(uuid.uuid4()),
        "device_id": DEVICE_ID,
        "alert_type": alert_type,
        "severity": severity,
        "message": message,
        "timestamp": current_timestamp()
    }


# ==========================================
# DEVICE STATUS
# ==========================================

def build_device_status(
    device_status="ONLINE",
    camera_status="READY",
    ai_status="READY"
):
    return {
        "device_id": DEVICE_ID,
        "device_status": device_status,
        "camera_status": camera_status,
        "ai_status": ai_status,
        "timestamp": current_timestamp()
    }


# ==========================================
# HEARTBEAT
# ==========================================

def build_heartbeat():
    return {
        "device_id": DEVICE_ID,
        "timestamp": current_timestamp()
    }


# ==========================================
# COMMAND ACK
# ==========================================

def build_command_ack(
    command_id,
    command,
    status,
    message=""
):
    return {
        "device_id": DEVICE_ID,
        "command_id": command_id,
        "command": command,
        "status": status,
        "message": message,
        "timestamp": current_timestamp()
    }


# ==========================================
# TOPIC MAP
# ==========================================

TOPICS = {
    "telemetry": TOPIC_TELEMETRY,
    "alerts": TOPIC_ALERTS,
    "status": TOPIC_STATUS,
    "command": TOPIC_COMMAND,
    "command_ack": TOPIC_COMMAND_ACK,
    "heartbeat": TOPIC_HEARTBEAT
}
