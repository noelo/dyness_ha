# Dyness Battery - Home Assistant Custom Integration

[NOTE] Original Code from usamamughal97@gmail.com

## What you get (27 sensors)

| Sensor | Unit | Notes |
|--------|------|-------|
| Battery Power | W | Positive = charging, negative = discharging |
| Battery Current | A | |
| Battery Status | | Charging / Discharging / Standby |
| Battery SOC | % | State of Charge |
| Battery SOH | % | State of Health |
| Pack Voltage | V | Overall pack voltage |
| Cell Voltage Max | V | Highest cell voltage |
| Cell Voltage Min | V | Lowest cell voltage |
| Cell Voltage Spread | V | Max - Min (>20mV = imbalance warning) |
| Max Voltage Cell # | | Which cell has highest voltage |
| Min Voltage Cell # | | Which cell has lowest voltage |
| Charge Voltage Upper Limit | V | |
| Charge Voltage Lower Limit | V | |
| Cell Temperature Max | °C | |
| Cell Temperature Min | °C | |
| MOSFET Temperature | °C | |
| BMS Temperature Max | °C | |
| BMS Temperature Min | °C | |
| Max Charge Current | A | BMS-reported limit |
| Max Discharge Current | A | BMS-reported limit |
| Charge Enable | | Enabled / Disabled |
| Discharge Enable | | Enabled / Disabled |
| Alarm Status | | OK / ALARM |
| Communication Status | | Online / Offline |
| Firmware Version | | |
| Signal Strength | dBm | Data logger WiFi/cellular signal |
| Last Data Update | timestamp | |

Data updates every **5 minutes** (matching Dyness API refresh rate).

---

## Installation

### Step 1 — Copy files to Home Assistant

Copy the entire `custom_components/dyness/` folder into your Home Assistant
`config` directory so the structure looks like:

```
/config/
  custom_components/
    dyness/
      __init__.py
      api.py
      config_flow.py
      coordinator.py
      sensor.py
      manifest.json
      strings.json
      const.py
```

**Easy ways to copy:**

**Option A — Samba / File Share**
If you have the Samba add-on enabled, copy the folder via Windows Explorer
to `\\homeassistant\config\custom_components\dyness\`

**Option B — SSH**
```bash
scp -r custom_components/dyness/ root@<HA_IP>:/config/custom_components/
```

**Option C — File Editor add-on**
Create each file manually via the HA File Editor add-on.

---

### Step 2 — Restart Home Assistant

Settings → System → Restart

---

### Step 3 — Add Integration

1. Settings → Devices & Services → **+ Add Integration**
2. Search for **"Dyness Battery"**
3. Fill in:
   - **API ID**: `44380949851452`
   - **API Secret**: `f19f9df9d0398f7c5b39f860aaf5d8d`
   - **Device SN (BMS)**: `R07E884668285328-BMS`
   - **Dongle SN**: `R07E884668285328`
4. Click Submit

---

### Step 4 — Verify

Go to Settings → Devices & Services → Dyness Battery
All 27 sensors should appear and populate within 5 minutes.

---

## Troubleshooting

**Sensors show "Unavailable"**
- Check HA logs: Settings → System → Logs → filter "dyness"
- Verify your internet connection from the HA VM
- The Dyness API allows max 1 request per minute — don't reduce the poll interval

**"Cannot connect" during setup**
- Double-check your API ID and Secret in the Dyness portal
- Make sure your HA VM can reach `open-api.dyness.com`

**Cell Voltage Spread > 0.020 V**
This indicates cell imbalance. Monitor over time — if it persists or grows,
the battery may need balancing or servicing.
