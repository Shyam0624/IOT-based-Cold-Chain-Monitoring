import time
import json
import random
from machine import ADC, Pin
from mqtt_simple import MQTTClient
import secrets
import math

print("Running main.py...")

# --- Analog Temperature Sensor on Pin D34 (3-Pin Module) ---
adc = ADC(Pin(34))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

# --- Constants for the NTC logic ---
R_DIVIDER = 10000.0
B_COEFFICIENT = 3950.0
R_NOMINAL = 10000.0
T_NOMINAL_K = 298.15
V_IN = 3.3
ADC_MAX = 4095.0

def read_temperature():
    """ Reads the 3-pin NTC module with clamping """
    try:
        raw = adc.read()
        if raw < 1: raw = 1
        if raw > 4090: raw = 4090
        voltage = raw * (V_IN / ADC_MAX)
        resistance = (voltage * R_DIVIDER) / (V_IN - voltage)
        steinhart = resistance / R_NOMINAL
        steinhart = math.log(steinhart)
        steinhart /= B_COEFFICIENT
        steinhart += (1.0 / T_NOMINAL_K)
        steinhart = 1.0 / steinhart
        steinhart -= 273.15
        return round(steinhart, 2)
    except Exception as e:
        print(f"Error reading temp: {e}")
        return 4.0

# Door Sensor (Pushbutton on D35)
door_sensor = Pin(35, Pin.IN, Pin.PULL_UP)

# Reboot LED (on D4)
reboot_led = Pin(4, Pin.OUT)
reboot_led.off()

# --- MQTT Configuration ---
CLIENT_ID = f"wokwi_truck_{random.randint(0, 1000)}"
LOCATION_TOPIC = "coldchain/truck_001/location"
TELEMETRY_TOPIC = "coldchain/truck_001/telemetry"
COMMAND_TOPIC = "coldchain/truck_001/command"
ALERT_TOPIC = "coldchain/truck_001/alert"

# --- Simulation State ---
is_system_broken = True
last_reboot_time = 0

# --- Critical Alert Monitoring State ---
IDEAL_TEMP_MAX = 4.0 
WINDOW_DURATION_SECS = 60
FAILURE_THRESHOLD = 2
reboot_failure_count = 0
window_start_time = time.time()
critical_alert_sent_this_window = False

# --- MQTT Callback ---
def on_message(topic, msg):
    global is_system_broken, last_reboot_time, reboot_failure_count, critical_alert_sent_this_window
    
    print(f"📩 Command received on topic: {topic.decode()}")
    try:
        payload = json.loads(msg.decode())
        if payload.get("command") == "reboot":
            print("    REBOOT command received!")
            
            reboot_failure_count += 1
            print(f"[Monitor] Reboot failure count: {reboot_failure_count}")

            if reboot_failure_count > FAILURE_THRESHOLD and not critical_alert_sent_this_window:
                print("---")
                print("🚨🚨 CRITICAL ALERT 🚨🚨")
                print(f"More than {FAILURE_THRESHOLD} reboots in {WINDOW_DURATION_SECS}s. Unit is defective!")
                print("---")
                
                alert_payload = {
                    "timestamp": int(time.time()),
                    "truck_id": "truck_001",
                    "error": "CRITICAL_FREEZER_FAILURE",
                    "message": f"Freezer unit is defective. Operator attempted {reboot_failure_count} reboots in under 5 minutes. Immediate replacement required."
                }
                client.publish(ALERT_TOPIC, json.dumps(alert_payload))
                critical_alert_sent_this_window = True
            
            print("    Cooling unit ON. Forcing ideal temp (0-4°C) for 15s...")
            is_system_broken = False
            reboot_led.on()
            last_reboot_time = time.time()
            
    except Exception as e:
        print(f"    Error processing command: {e}")

# --- Connect to MQTT ---
try:
    print("Connecting to MQTT Broker...")
    client = MQTTClient(CLIENT_ID, secrets.BROKER_HOST, 
                        port=1883,
                        ssl=False)
    client.set_callback(on_message)
    client.connect()
    client.subscribe(COMMAND_TOPIC)
    print(f"✅ Connected to HiveMQ and subscribed to {COMMAND_TOPIC}")
except Exception as e:
    print(f"Failed to connect to MQTT: {e}")

# --- Main Simulation Loop ---
print("🚚 Simulation started. Running main loop...")

first_check_done = False
system_is_currently_stable = False 

# --- NEW: Location Simulation Variables ---
last_location_publish_time = 0
current_lat = 12.9716  # Base latitude
current_lon = 77.5946  # Base longitude

while True:
    try:
        current_time = time.time()
        
        real_temp = read_temperature()
        is_door_open = not door_sensor.value()
        
        if not first_check_done:
            if real_temp > IDEAL_TEMP_MAX:
                print(f"[Monitor] CRITICAL alert window set to {WINDOW_DURATION_SECS}s")
                print("---")
                print(f"🚨 SYSTEM START: Initial temp is {real_temp}°C (OVER LIMIT).")
                print(f"   Reboot the System")
                print("---")
                system_is_currently_stable = False
            else:
                print("---")
                print(f"✅ SYSTEM START: Initial temp is {real_temp}°C (Normal).")
                print("    Monitoring...")
                print("---")
                system_is_currently_stable = True
            first_check_done = True
        
        client.check_msg()
        
        if not is_system_broken:
            if current_time - last_reboot_time > 15:
                is_system_broken = True
                reboot_led.off()
                
                if real_temp > IDEAL_TEMP_MAX:
                    print("---")
                    print("🚨 EVENT: 'Reboot' fix wore off. Temp is STILL HIGH.")
                    print("    System unstable.")
                    print("---")
                    system_is_currently_stable = False
                else:
                    print("---")
                    print("✅ EVENT: 'Reboot' fix worked. Temp is now NORMAL.")
                    print("    System stable. ")
                    print("---")
                    system_is_currently_stable = True
                            
        if current_time - window_start_time > WINDOW_DURATION_SECS:
            if reboot_failure_count == 0 and system_is_currently_stable:
                print(f"✅ [Monitor] {WINDOW_DURATION_SECS}s window reset. System remains stable.")
            else:
                print(f"[Monitor] {WINDOW_DURATION_SECS}s window reset. Failure count was: {reboot_failure_count}")
            
            window_start_time = current_time
            reboot_failure_count = 0
            critical_alert_sent_this_window = False

        if is_system_broken:
            if real_temp > IDEAL_TEMP_MAX and system_is_currently_stable:
                print("---")
                print(f"🚨 EVENT: Temperature has risen to {real_temp}°C (OVER LIMIT).")
                print("    System is now unstable. Reboot if required.")
                print("---")
                system_is_currently_stable = False
            
            elif real_temp <= IDEAL_TEMP_MAX and not system_is_currently_stable:
                print("---")
                print(f"✅ EVENT: Temperature has returned to {real_temp}°C (Normal).")
                print("    System is stable again.")
                print("---")
                system_is_currently_stable = True

        # --- Apply reporting logic based on the "fix" state ---
        if is_system_broken:
            temp_to_publish = real_temp 
        else:
            temp_to_publish = random.uniform(0.0, 4.0)

        # --- Create Telemetry Payload (EVERY SECOND) ---
        telemetry_payload = {
            "timestamp": int(current_time), # Exact Unix timestamp
            "temp": round(temp_to_publish, 2),
            "door_open": is_door_open
        }
        
        # --- Publish Telemetry (EVERY SECOND) ---
        client.publish(TELEMETRY_TOPIC, json.dumps(telemetry_payload))
        
        # --- NEW: Location Publishing Logic (EVERY 5 SECONDS) ---
        if current_time - last_location_publish_time > 5:
            
            # Simulate movement
            current_lat += random.uniform(-0.0001, 0.0001)
            current_lon += random.uniform(-0.0001, 0.0001)

            location_payload = {
                "timestamp": int(current_time), # Exact Unix timestamp
                "location": { "lat": round(current_lat, 6), "lon": round(current_lon, 6) }
            }
            
            # Publish Location
            client.publish(LOCATION_TOPIC, json.dumps(location_payload))
            
            # Reset the timer
            last_location_publish_time = current_time
        
        # 7. Wait
        time.sleep(1)

    except Exception as e:
        print(f"Loop error: {e}")
        time.sleep(5)