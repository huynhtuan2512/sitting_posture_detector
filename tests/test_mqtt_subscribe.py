
"""Kiểm tra MQTT Subscribe và nhận lệnh."""

import time
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mqtt.mqtt_client import MQTTClient

logging.basicConfig(level=logging.INFO)


def handle_command(command_data):

    command = command_data.get("command")
    value = command_data.get("value")

    print("\n========== COMMAND RECEIVED ==========")
    print("Command:", command)
    print("Value:", value)
    print("======================================")

    if command == "SET_AUDIO":
        print("Yêu cầu thay đổi trạng thái âm thanh:", value)
        return True

    if command == "SET_MONITORING":
        print("Yêu cầu thay đổi trạng thái theo dõi:", value)
        return True

    raise ValueError(f"Unsupported command: {command}")


mqtt_client = MQTTClient(
    command_callback=handle_command
)

if not mqtt_client.connect():
    print("Không thể kết nối MQTT")
    raise SystemExit(1)

try:
    print("Đang chờ lệnh từ Backend...")

    while True:
        mqtt_client.process_commands()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("Đang dừng chương trình...")

finally:
    mqtt_client.disconnect()
