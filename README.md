
# Vaccine Cold‑Chain Monitoring — Mini Project

> Small IoT prototype for monitoring refrigerated vaccine trucks using a MicroPython device (Wokwi simulation), MQTT, Node‑RED dashboard and a Python alert backend.

---

## Quick overview

- Device simulation and MicroPython code: `wokwi/` (connects to MQTT and publishes telemetry, location and alerts).
- Node‑RED dashboard flow: `node-red/node-red-flow.json` (visualization, world map, charts, notifications).
- Python alert handler: `python-backend/alert_service.py` (subscribes to alerts and can further process/forward them).
- Broker: default configured to `broker.hivemq.com` via `.env` / `wokwi/secrets.py` (do NOT commit secrets).

## Features

- Periodic telemetry publishing (temperature, door state, battery, etc.).
- Location publishing for map visualization.
- Local alert generation in device code and processing by a Python backend.
- Node‑RED dashboard for live monitoring and operator commands.

## What you need (prerequisites)

- Python 3.8+ (Windows, macOS, Linux)
- pip
- Node‑RED (for dashboard preview)
- Optionally: Wokwi or a MicroPython device to run `wokwi/` scripts

## Install & setup (Windows PowerShell examples)

1. Clone the repo:

```powershell
git clone <your-repo-url>
cd "mini-project"
```

2. Create and activate a venv (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install Python dependencies:

```powershell
pip install -r requirements.txt
```

4. Configure MQTT broker and secrets

- Copy `.env` locally or create one with your broker settings (this repo includes a sample `.env`):

```
# .env
BROKER_HOST=broker.hivemq.com
```

- For the Wokwi/MicroPython device, keep `wokwi/secrets.py` locally and do NOT commit real credentials. Use placeholders like `WIFI_SSID = "REPLACE_ME"`.

## Running components

1. Start Node‑RED and import the flow `node-red/node-red-flow.json` to view dashboard widgets (charts, gauges, world map).

2. Run the Python alert handler (uses `paho-mqtt`):

```powershell
# Ensure .env is set or environment variables are configured
python python-backend/alert_service.py
```

3. Device simulation

- Use Wokwi to run the scripts in `wokwi/` (these are MicroPython files: `main.py`, `mqtt_simple.py`, etc.). The code publishes telemetry and alerts to MQTT topics used by the dashboard and backend.

## Typical MQTT topics & payloads

- Telemetry: `coldchain/truck_001/telemetry` — JSON e.g. `{ "temp": 4.5, "door_open": false }`
- Location: `coldchain/truck_001/location` — JSON e.g. `{ "lat": 12.3, "lon": 76.5 }`
- Alert: `coldchain/truck_001/alert` — JSON with timestamp, truck_id, error, message
- Command: `coldchain/truck_001/command` — commands sent from dashboard to device

## Dashboard behavior & real-time interactions

The Node‑RED dashboard shows live data and supports operator actions:

- Gauge: shows the current temperature in real time.
- Temperature trend graph: plots recent temperature points so you can spot warming or cooling trends.
- Door status indicator: shows whether the truck door is open or closed.
- Reboot button: when clicked, the dashboard publishes a `reboot` command to `coldchain/truck_001/command`. In the Wokwi ESP32 simulation this command triggers the device logic that resets the simulated fridge to normal (nominal) temperature. You can then drag the NTC slider back into the normal range to observe recovery and stable operation.
- Alerts & acknowledgements: the Python `alert_service.py` analyzes telemetry and publishes acknowledgement messages (e.g., `warning`, `critical`, `recovery`) which are routed to the dashboard notifications panel. This keeps the operator aware of the alert state and confirmations.

There are three MQTT clients involved:

1. The ESP32 device (MicroPython) — publishes telemetry, location and receives commands.
2. Node‑RED dashboard — subscribes to telemetry and alerts, publishes operator commands (e.g., reboot).
3. Python alert service (`python-backend/alert_service.py`) — subscribes to telemetry and issues alert/acknowledgement messages.

Because all three connect to the same broker (configured in `.env` / `wokwi/secrets.py`), messages flow in real time between device, dashboard and backend.

## System architecture & value proposition

The IoT‑Based Vaccine Cold Chain Monitoring System in this project combines embedded sensing, cloud connectivity, and lightweight analytics to solve real challenges in vaccine transport. An ESP32 reads temperature and door status and pushes data to a public MQTT broker (HiveMQ by default). Node‑RED provides a central monitoring interface with live widgets, trends, and location maps, while a Python alert service applies simple analytics to generate immediate alerts and acknowledgements.

Unlike passive data loggers, this system is interactive: it not only notifies operators about anomalies but also enables remote control (reboot) and contextual insights (e.g., open door vs cooling failure). This makes it suitable for both urban and rural networks where timely intervention is critical for vaccine integrity.

## How to run this project (detailed)

This section provides explicit, step‑by‑step instructions to run the whole prototype locally and in Wokwi. Follow the order below.

File layout (root of repo)

```
./
├─ node-red/
│  └─ node-red-flow.json
├─ python-backend/
│  └─ alert_service.py
├─ wokwi/
│  ├─ boot.py
│  ├─ diagram.json
│  ├─ main.py
│  ├─ mqtt_simple.py
│  └─ secrets.py   # keep local, do NOT commit real credentials
├─ requirements.txt
├─ .env
└─ README.md
```

Run steps (high level)

1) Open VS Code (or any development environment) in the project root.
2) Open two terminal panes (PowerShell recommended):
	- Terminal A: run the Python backend alert handler
	- Terminal B: run Node‑RED (dashboard + MQTT flow)
3) Start the Wokwi simulation in the browser (ESP32 MicroPython) and use the NTC sensor slider to vary temperature in real time.
4) Import and wire the Node‑RED flow from `node-red/node-red-flow.json`, configure MQTT, and observe the dashboard.

Terminal commands (PowerShell examples)

```powershell
# Terminal A: start the backend alert handler
python python-backend/alert_service.py

# Terminal B: start Node-RED (assumes node-red is installed globally)
node-red
```

Notes:
- If `node-red` is not in your PATH, install Node‑RED (https://nodered.org/) and follow platform install instructions. On Windows you can install via npm: `npm install -g --unsafe-perm node-red`.
- Make sure your `.env` is configured (or set BROKER_HOST env var). The included example `.env` uses `broker.hivemq.com`.

Wokwi (MicroPython ESP32) — detailed

1. Open https://wokwi.com/ in your browser.
2. Create a new project and choose the ESP32 MicroPython template.
3. Add the files from the repo's `wokwi/` folder to the Wokwi project (create `boot.py`, `main.py`, `mqtt_simple.py`, `secrets.py`, etc.).
	- For `wokwi/secrets.py`, use placeholder values or your local broker creds. Do NOT paste real secrets to the repo.
4. Click Start Simulation (or Run). The circuit diagram includes an NTC sensor component.
5. Click the NTC sensor component in the circuit view — a slider will appear. Move the slider to change the simulated temperature. The MicroPython code reads the NTC value and publishes telemetry over MQTT; the dashboard and backend should react in real time.

Node‑RED — setup and import

1. With Node‑RED running (Terminal B), open the editor at http://localhost:1880.
2. Import the flow: from the menu choose `Import` -> `Local file` and load `node-red/node-red-flow.json`.
3. Configure the MQTT broker node(s) to point to the broker defined in your `.env` (e.g., `broker.hivemq.com`) or to your local broker.
4. Ensure dashboard nodes (charts, gauges, notification) and `worldmap` nodes are installed in your Node‑RED instance. If missing, install via the Palette Manager or npm (for example `node-red-dashboard` and `node-red-contrib-web-worldmap`).
5. Deploy the flow. You should see telemetry on charts, gauge and map; notifications will appear when the device publishes alerts.

Which nodes to create/configure (summary)

- MQTT in/out nodes for the topics used by the device
- Function nodes to parse messages and map fields
- Dashboard nodes: chart, gauge, text, notification
- Worldmap node to display `location` payloads
- Switch or change nodes to filter/route alert messages

Troubleshooting tips

- If telemetry doesn't appear, verify the device is connected to the broker by checking Wokwi serial console output.
- Confirm Node‑RED MQTT nodes are pointing to the same broker host and port.
- Use a lightweight MQTT client (e.g., MQTT Explorer) to inspect messages on the topics.


## Contributing

We welcome contributions. For small changes:

1. Fork the repository
2. Create a feature branch
3. Open a pull request with a clear description of changes

If you plan larger changes, please open an issue first to discuss the approach.

Note: Keep secrets out of commits. Use `.env` and local-only `wokwi/secrets.py`.

## Where to get help

- Open an issue in this repository for bugs or feature requests.
- For quick questions, add a short description in an issue mentioning which component (Wokwi, Node‑RED, or Python backend).

## Maintainers

- Current maintainer: (replace with your name and contact) — add details in `MAINTAINERS.md` or repo description.

## Recommended next steps (pre‑push checklist)

- Add or verify `.gitignore` excludes `.env`, `.vscode/`, `wokwi/secrets.py`, `__pycache__/` and other local files.
- Replace any real credentials with placeholders before committing.
- Consider pinning versions in `requirements.txt` for reproducible installs.
- Optionally add `CONTRIBUTING.md`, `LICENSE`, and CI badges (GitHub Actions) for build/test status.

## Technologies used

- Python (paho-mqtt, python-dotenv)
- MicroPython (Wokwi simulation files)
- Node‑RED dashboard (flow JSON included)
- MQTT broker (user configurable; sample uses broker.hivemq.com)

