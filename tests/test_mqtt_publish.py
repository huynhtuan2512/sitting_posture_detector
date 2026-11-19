
"""Kiểm tra MQTT Publish."""

import time
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mqtt.mqtt_client import MQTTClient

logging.basicConfig(level=logging.INFO)

mqtt_client = MQTTClient()

if not mqtt_client.connect():
    print("Không thể khởi tạo kết nối MQTT")
    raise SystemExit(1)

try:
    # Chờ kết nối hoàn tất
    for _ in range(30):
        if mqtt_client.connected:
            break
        time.sleep(0.5)

    if not mqtt_client.connected:
        print("Không kết nối được MQTT Broker")
        raise SystemExit(1)

    print("MQTT connected!")

    # Test telemetry
    mqtt_client.publish_telemetry(
        posture="SLOUCH",
        confidence=0.93,
        angles={
            "esh": 130.5,
            "neck": 35.2,
            "trunk": 12.4
        },
        person_detected=True
    )

    # Test alert
    mqtt_client.publish_alert(
        alert_type="SLOUCH",
        severity="WARNING",
        message="Phat hien tu the ngoi gu lung"
    )

    # Test heartbeat
    mqtt_client.publish_heartbeat()

    print("Đã gửi các message kiểm thử.")

    time.sleep(2)

finally:
    mqtt_client.disconnect()
