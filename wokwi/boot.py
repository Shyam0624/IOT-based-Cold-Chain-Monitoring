import network
import time
import secrets

print("Booting... (Simulated Wi-Fi)")

try:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASS)

    for _ in range(10):
        if wlan.isconnected():
            break
        time.sleep(1)

    if wlan.isconnected():
        print("✅ Connected (simulated) IP:", wlan.ifconfig()[0])
    else:
        print("⚠️ Wi-Fi not available, continuing offline (simulation mode)")
except Exception as e:
    print("⚠️ Wi-Fi simulation failed:", e)
