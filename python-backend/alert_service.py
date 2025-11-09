import paho.mqtt.client as mqtt
import random
import time
import json
import os
from dotenv import load_dotenv
from collections import deque

# --- Load Environment Variables ---
load_dotenv()

# --- MQTT Configuration (Loaded from .env) ---
BROKER_HOST = os.getenv("BROKER_HOST")
BROKER_PORT = 1883
CLIENT_ID = f"alert_service_{random.randint(0, 1000)}"

# --- Topic Configuration ---
LOCATION_TOPIC = "coldchain/truck_001/location"
TELEMETRY_TOPIC = "coldchain/truck_001/telemetry"
ALERT_TOPIC = "coldchain/truck_001/alert"

# --- State Management ---
temperature_history = deque(maxlen=10)
last_known_location = {"lat": 12.9716, "lon": 77.5946} # Default
critical_alert_sent = False
warning_alert_sent = False # --- NEW: Flag for the 4.0°C warning

# --- Alerting Thresholds ---
TEMP_WARNING_THRESHOLD = 4.0  # (Warning) Single reading > 4.0°C
TEMP_CRITICAL_THRESHOLD = 5.5 # (Critical) The 10-reading average is drifting up
TEMP_RECOVERY_THRESHOLD = 3.5 # (Recovery) Both average and current must be below this

def connect_mqtt() -> mqtt.Client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("✅ Connected to public HiveMQ broker!")
            client.subscribe(LOCATION_TOPIC)
            client.subscribe(TELEMETRY_TOPIC)
            print(f"   Subscribed to: {LOCATION_TOPIC}")
            print(f"   Subscribed to: {TELEMETRY_TOPIC}")
        else:
            print(f"❌ Connection failed with code {rc}")

    def on_message(client, userdata, msg):
        # Cleaned up logs
        try:
            payload = json.loads(msg.payload.decode())
            if msg.topic == LOCATION_TOPIC:
                handle_location(payload)
            elif msg.topic == TELEMETRY_TOPIC:
                # Let the handler do the detailed printing
                handle_telemetry(client, payload)
        except Exception as e:
            print(f"⚠️ Message error: {e}")

    client = mqtt.Client(client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connecting to {BROKER_HOST}:{BROKER_PORT} ...")
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    return client


def handle_location(payload: dict):
    global last_known_location
    if "location" in payload:
        last_known_location = payload["location"]
        print(f"📍 Location Updated: {last_known_location}")

def handle_telemetry(client: mqtt.Client, payload: dict):
    """
    Analyzes temperature data and triggers alerts if necessary.
    Includes "Door Open" logic, "Warning" (instant), and "Critical" (average) alerts.
    """
    global critical_alert_sent, warning_alert_sent
    
    if "temp" not in payload:
        return

    current_temp = payload["temp"]
    is_door_open = payload.get("door_open", False)
    temperature_history.append(current_temp)
    
    print(f"📩 Telemetry: Temp={current_temp}°C, DoorOpen={is_door_open}")

    if len(temperature_history) < 10:
        print("   LOG: Collecting initial data (Need 10 readings)...")
        return
    
    rolling_avg = sum(temperature_history) / len(temperature_history)
    
    # --- 1. ROOT CAUSE ANALYSIS: DOOR OPEN ---
    # If the door is open, it's a "valid" reason for high temp.
    # Suppress all alerts and reset flags.
    if is_door_open:
        if current_temp > TEMP_WARNING_THRESHOLD:
            print(f"   LOG: Temp is {current_temp:.2f}°C, but door is open. Suppressing alert.")
        
        # If alerts were active, log that the door opening "pauses" them
        if warning_alert_sent or critical_alert_sent:
            print("   LOG: Door opened, resetting alert state.")
            warning_alert_sent = False
            critical_alert_sent = False
        return # Stop all further alert logic

    # --- 2. ALERTING LOGIC (Door is confirmed CLOSED) ---
    
    # CRITICAL: The rolling average is too high (sustained failure)
    if rolling_avg > TEMP_CRITICAL_THRESHOLD and not critical_alert_sent:
        critical_alert_sent = True
        warning_alert_sent = True # A critical alert is also a warning
        alert_msg = {
            "level": "CRITICAL",
            "message": f"A/C Failure Detected! Rolling Avg is {rolling_avg:.2f}°C",
            "current_temp": current_temp,
            "location": last_known_location,
            "timestamp": int(time.time())
        }
        publish_alert(client, alert_msg)

    # WARNING: The current temp is high (instant spike)
    elif current_temp > TEMP_WARNING_THRESHOLD and not warning_alert_sent:
        warning_alert_sent = True
        alert_msg = {
            "level": "WARNING",
            "message": f"High Temperature Detected! Current Temp is {current_temp:.2f}°C",
            "rolling_avg": f"{rolling_avg:.2f}°C",
            "location": last_known_location,
            "timestamp": int(time.time())
        }
        publish_alert(client, alert_msg)

    # --- 3. RECOVERY LOGIC (Door is closed and temps are good) ---
    elif (current_temp < TEMP_RECOVERY_THRESHOLD and 
          rolling_avg < TEMP_RECOVERY_THRESHOLD and 
          (warning_alert_sent or critical_alert_sent)):
        
        print(f"✅ RECOVERY: Temperature is back to normal. Avg: {rolling_avg:.2f}°C")
        critical_alert_sent = False
        warning_alert_sent = False
        
        # Send a "RECOVERY" message so the dashboard can turn green
        alert_msg = {
            "level": "RECOVERY",
            "message": f"System Recovered. Temps are normal. Avg: {rolling_avg:.2f}°C",
            "current_temp": current_temp,
            "timestamp": int(time.time())
        }
        publish_alert(client, alert_msg)
    
    # --- 4. NORMAL OPERATIONS ---
    elif not warning_alert_sent:
         print(f"   LOG: System normal. Avg: {rolling_avg:.2f}°C")


def publish_alert(client: mqtt.Client, payload: dict):
    msg = json.dumps(payload)
    result = client.publish(ALERT_TOPIC, msg)
    
    level = payload.get("level", "INFO")
    message = payload.get("message", "No message")
    
    if result[0] == 0:
        if level == "CRITICAL":
            print(f"🚨🚨🚨 ALERT PUBLISHED: {level} - {message}")
        elif level == "WARNING":
            print(f"⚠️  ALERT PUBLISHED: {level} - {message}")
        elif level == "RECOVERY":
            print(f"✅ ALERT PUBLISHED: {level} - {message}")
    else:
        print(f"⚠️ Failed to publish alert to topic {ALERT_TOPIC}")

if __name__ == "__main__":
    if not BROKER_HOST:
        print("❌ ERROR: Missing BROKER_HOST in .env file.")
        exit(1)

    print("Starting Alert Service...")
    client = connect_mqtt()
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Alert service stopped by user.")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Disconnected from HiveMQ broker.")