
"""MQTT Client chạy độc lập với AI inference."""

import logging
import threading
import queue
import json
from mqtt.mqtt_protocol import encode_payload, build_device_status

import paho.mqtt.client as mqtt

from mqtt.mqtt_config import (
    BROKER_HOST,
    BROKER_PORT,
    USERNAME,
    PASSWORD,
    KEEPALIVE,
    DEVICE_ID,
    TOPIC_TELEMETRY,
    TOPIC_ALERTS,
    TOPIC_STATUS,
    TOPIC_COMMAND,
    TOPIC_COMMAND_ACK,
    TOPIC_HEARTBEAT,
    QOS_TELEMETRY,
    QOS_ALERTS,
    QOS_STATUS,
    QOS_COMMAND,
    QOS_COMMAND_ACK,
    QOS_HEARTBEAT
)

from mqtt.mqtt_protocol import (
    encode_payload,
    decode_payload,
    build_telemetry,
    build_alert,
    build_device_status,
    build_heartbeat,
    build_command_ack
)


log = logging.getLogger(__name__)


class MQTTClient:

    def __init__(self, command_callback=None):

        self.command_callback = command_callback

        self.connected = False
        self.running = False

        self.command_queue = queue.Queue()

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"sitting_{DEVICE_ID}"
        )

        if USERNAME:
            self.client.username_pw_set(USERNAME, PASSWORD or None)

        # Callback kết nối
        self.client.on_connect = self._on_connect

        # Callback mất kết nối
        self.client.on_disconnect = self._on_disconnect

        # Callback nhận message
        self.client.on_message = self._on_message

        # Callback publish hoàn tất
        self.client.on_publish = self._on_publish

        self.client.reconnect_delay_set(
            min_delay=1,
            max_delay=30
        )
        # Cấu hình Last Will and Testament
        will_payload = {
            "device_id": DEVICE_ID,
            "device_status": "OFFLINE",
            "camera_status": "UNKNOWN",
            "ai_status": "UNKNOWN",
            "reason": "MQTT_CONNECTION_LOST"
        }

        self.client.will_set(
            TOPIC_STATUS,
            payload=encode_payload(will_payload),
            qos=QOS_STATUS,
            retain=True
        )
    # ======================================
    # CONNECTION
    # ======================================

    def connect(self):

        try:
            log.info(
                "Connecting to MQTT Broker %s:%s",
                BROKER_HOST,
                BROKER_PORT
            )

            self.running = True

            self.client.connect(
                BROKER_HOST,
                BROKER_PORT,
                KEEPALIVE
            )

            # Chạy network loop ở background thread
            self.client.loop_start()

            return True

        except Exception:
            log.exception("MQTT connection failed")
            self.running = False
            return False

    def _on_connect(self, client, userdata, flags, reason_code, properties):

        if reason_code.is_failure:
            log.error("MQTT connection rejected: %s", reason_code)
            self.connected = False
            return

        self.connected = True

        log.info("Connected to MQTT Broker")

        # Đăng ký nhận lệnh từ Backend
        client.subscribe(
            TOPIC_COMMAND,
            qos=QOS_COMMAND
        )

        log.info("Subscribed: %s", TOPIC_COMMAND)

        # Thông báo thiết bị online
        self.publish_status(
            device_status="ONLINE",
            camera_status="READY",
            ai_status="READY"
        )

    def _on_disconnect(
        self,
        client,
        userdata,
        disconnect_flags,
        reason_code,
        properties
    ):

        self.connected = False

        log.warning(
            "MQTT disconnected: %s",
            reason_code
        )

    # ======================================
    # MESSAGE CALLBACK
    # ======================================

    def _on_message(self, client, userdata, message):

        try:
            payload = decode_payload(
                message.payload.decode("utf-8")
            )

            log.info(
                "Received command: %s",
                payload
            )

            # Không thực hiện điều khiển phần cứng
            # trực tiếp trong callback.
            self.command_queue.put(payload)

        except (UnicodeDecodeError, json.JSONDecodeError):
            log.exception("Invalid MQTT JSON message")

    def _on_publish(
        self,
        client,
        userdata,
        mid,
        reason_code,
        properties
    ):
        log.debug("MQTT message published: mid=%s", mid)

    # ======================================
    # PUBLISH HELPER
    # ======================================

    def _publish(self, topic, data, qos=0, retain=False):

        if not self.connected:
            log.warning("MQTT not connected. Skip: %s", topic)
            return False

        try:
            payload = encode_payload(data)

            result = self.client.publish(
                topic,
                payload=payload,
                qos=qos,
                retain=retain
            )

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                log.error("Publish failed: %s", result.rc)
                return False

            return True

        except Exception:
            log.exception("MQTT publish error")
            return False

    # ======================================
    # PUBLISH TELEMETRY
    # ======================================

    def publish_telemetry(
        self,
        posture,
        confidence=None,
        angles=None,
        person_detected=True
    ):

        data = build_telemetry(
            posture=posture,
            confidence=confidence,
            angles=angles,
            person_detected=person_detected
        )

        return self._publish(
            TOPIC_TELEMETRY,
            data,
            qos=QOS_TELEMETRY
        )

    # ======================================
    # PUBLISH ALERT
    # ======================================

    def publish_alert(
        self,
        alert_type,
        severity="WARNING",
        message=""
    ):

        data = build_alert(
            alert_type=alert_type,
            severity=severity,
            message=message
        )

        return self._publish(
            TOPIC_ALERTS,
            data,
            qos=QOS_ALERTS
        )

    # ======================================
    # PUBLISH DEVICE STATUS
    # ======================================

    def publish_status(
        self,
        device_status="ONLINE",
        camera_status="READY",
        ai_status="READY"
    ):

        data = build_device_status(
            device_status=device_status,
            camera_status=camera_status,
            ai_status=ai_status
        )

        return self._publish(
            TOPIC_STATUS,
            data,
            qos=QOS_STATUS,
            retain=True
        )

    # ======================================
    # PUBLISH HEARTBEAT
    # ======================================

    def publish_heartbeat(self):

        data = build_heartbeat()

        return self._publish(
            TOPIC_HEARTBEAT,
            data,
            qos=QOS_HEARTBEAT
        )

    # ======================================
    # COMMAND PROCESSING
    # ======================================

    def process_commands(self):

        while True:

            try:
                command_data = self.command_queue.get_nowait()

            except queue.Empty:
                break

            command_id = command_data.get("command_id", "")
            command = command_data.get("command", "")

            try:
                if not command_id or not command:
                    raise ValueError("Missing command_id or command")

                if self.command_callback is None:
                    raise RuntimeError("No command handler registered")

                result = self.command_callback(command_data)

                if result is False:
                    raise RuntimeError("Command execution failed")

                self.publish_command_ack(
                    command_id,
                    command,
                    "SUCCESS",
                    "Command executed successfully"
                )

            except Exception as error:

                log.exception("Command execution failed")

                self.publish_command_ack(
                    command_id,
                    command,
                    "FAILED",
                    str(error)
                )

            finally:
                self.command_queue.task_done()

    def publish_command_ack(
        self,
        command_id,
        command,
        status,
        message=""
    ):

        data = build_command_ack(
            command_id=command_id,
            command=command,
            status=status,
            message=message
        )

        return self._publish(
            TOPIC_COMMAND_ACK,
            data,
            qos=QOS_COMMAND_ACK
        )

    # ======================================
    # SHUTDOWN
    # ======================================

    def disconnect(self):

        self.running = False

        if self.connected:
            self.publish_status(
                device_status="OFFLINE",
                camera_status="UNKNOWN",
                ai_status="STOPPED"
            )

        self.client.disconnect()
        self.client.loop_stop()

        self.connected = False

        log.info("MQTT Client stopped")
