"""Симулятор двокімнатної квартири для демонстрації OpenHAB."""
import math
import os
import random
import time
import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USERNAME = os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("MQTT_PASSWORD", "")
CA_FILE = os.getenv("MQTT_CA_FILE")
PREFIX = "iotmodul"
state = {"living_light": 0, "bedroom_light": 0, "heater": False,
         "setpoint": 21.0, "overload": False, "away": False, "arrive_until": 0.0}
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="iotmodul-simulator",
                     protocol=mqtt.MQTTv311)
if USERNAME:
    client.username_pw_set(USERNAME, PASSWORD)
if CA_FILE:
    client.tls_set(ca_certs=CA_FILE)
client.will_set(f"{PREFIX}/status/simulator", "OFFLINE", qos=1, retain=True)

def pub(topic, value, retain=True):
    client.publish(f"{PREFIX}/{topic}", str(value), qos=1, retain=retain)

def on_connect(c, _userdata, _flags, reason_code, _properties):
    if reason_code == 0:
        c.subscribe([(f"{PREFIX}/+/light/set", 1), (f"{PREFIX}/heater/set", 1),
                     (f"{PREFIX}/heater/setpoint/set", 1), (f"{PREFIX}/demo/overload/set", 1),
                     (f"{PREFIX}/demo/away/set", 1)])
        pub("status/simulator", "ONLINE")
        pub("demo/overload/state", "OFF")
        pub("demo/away/state", "ON" if state["away"] else "OFF")

def on_message(_client, _userdata, msg):
    value = msg.payload.decode("utf-8", errors="replace").strip()
    if msg.topic.endswith("/living/light/set"):
        state["living_light"] = max(0, min(100, int(float(value))))
        pub("living/light/state", state["living_light"])
    elif msg.topic.endswith("/bedroom/light/set"):
        state["bedroom_light"] = max(0, min(100, int(float(value))))
        pub("bedroom/light/state", state["bedroom_light"])
    elif msg.topic.endswith("/heater/set"):
        state["heater"] = value.upper() == "ON"
        pub("heater/state", "ON" if state["heater"] else "OFF")
    elif msg.topic.endswith("/heater/setpoint/set"):
        state["setpoint"] = max(15.0, min(24.0, float(value)))
        pub("heater/setpoint/state", state["setpoint"])
    elif msg.topic.endswith("/demo/overload/set"):
        state["overload"] = value.upper() == "ON"
        pub("demo/overload/state", "ON" if state["overload"] else "OFF")
    elif msg.topic.endswith("/demo/away/set"):
        away = value.upper() == "ON"
        if state["away"] and not away:
            # Мешканець повернувся: короткий рух у вітальні
            state["arrive_until"] = time.monotonic() + 12
        state["away"] = away
        pub("demo/away/state", "ON" if away else "OFF")

client.on_connect = on_connect
client.on_message = on_message
for attempt in range(60):
    try:
        client.connect(HOST, PORT, keepalive=30)
        break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("Не вдалося під'єднатися до MQTT-брокера")
client.loop_start()
pub("heater/setpoint/state", state["setpoint"])
pub("heater/state", "OFF")
pub("living/light/state", 0)
pub("bedroom/light/state", 0)
start = time.monotonic()
temperature = 20.2
try:
    while True:
        t = time.monotonic() - start
        # Короткі цикли присутності для демонстрації; таймери правил OpenHAB
        # залишаються реальними: 5 хвилин для світла, 30 хвилин для режиму Eco.
        phase = int(t // 40) % 3
        living_motion = phase == 0 and (t % 40) < 15
        bedroom_motion = phase == 1 and (t % 40) < 15
        # Демо «Нікого вдома»: руху немає; після повернення — рух у вітальні
        if state["away"]:
            living_motion = bedroom_motion = False
        elif time.monotonic() < state["arrive_until"]:
            living_motion = True
        pub("living/motion/state", "ON" if living_motion else "OFF")
        pub("bedroom/motion/state", "ON" if bedroom_motion else "OFF")
        pub("living/lux/state", round(22 + 8 * math.sin(t / 13)) if living_motion else round(110 + 20 * math.sin(t / 25)))
        pub("bedroom/lux/state", round(18 + 7 * math.sin(t / 15)) if bedroom_motion else round(95 + 15 * math.sin(t / 23)))
        if state["heater"]:
            temperature = min(state["setpoint"] + 0.4, temperature + 0.035)
        else:
            temperature = max(18.0, temperature - 0.004)
        pub("climate/temperature/state", round(temperature, 1))
        pub("climate/humidity/state", round(43 + 4 * math.sin(t / 70), 1))
        power = 2700 if state["overload"] else 280 + (state["heater"] * 1750) + int((state["living_light"] + state["bedroom_light"]) * 2.5) + random.randint(0, 55)
        pub("power/state", power)
        time.sleep(2)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()
    client.disconnect()
