import os
import time
import board
import ipaddress
import wifi
import socketpool
import pwmio
from time import sleep
from adafruit_minimqtt.adafruit_minimqtt import MQTT
from adafruit_motorkit import MotorKit

print("Connecting to WiFi")
wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'), os.getenv('CIRCUITPY_WIFI_PASSWORD'))
print("Connected to WiFi")

pool = socketpool.SocketPool(wifi.radio)
print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])
print("My IP address is", wifi.radio.ipv4_address)
ipv4 = ipaddress.ip_address("8.8.4.4")
print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4)*1000))

# MQTT broker details
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'squirrel/speaker')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')

# Initialize the speaker pin
SPEAKER_PIN = board.A0

def play_tone(frequency, duration):
    speaker = pwmio.PWMOut(SPEAKER_PIN, frequency=frequency, duty_cycle=0x4000)
    sleep(duration)
    speaker.deinit()

def activate_speaker():
    print("Activating speaker!")
    play_tone(440, 0.5)  # A4
    sleep(0.1)
    play_tone(880, 0.5)  # A5
    sleep(0.1)
    play_tone(660, 0.5)  # E5

# Callback for incoming MQTT messages
def message_callback(client, topic, message):
    print(f"Received message on topic {topic}: {message}")
    # Existing behavior for speaker activation
    if topic == MQTT_TOPIC and message == "fire":
        activate_speaker()
    # New behavior for heater/bedroom motor control
    elif topic == "heater/bedroom":
        if message == "on":
            print("Heater on command received: rotating motor forward")
            kit.motor1.throttle = 1
            time.sleep(1)  # adjust duration as needed
            kit.motor1.throttle = 0
        elif message == "off":
            print("Heater off command received: rotating motor in reverse")
            kit.motor1.throttle = -1
            time.sleep(1)
            kit.motor1.throttle = 0

mqtt_client = MQTT(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    username=MQTT_USERNAME,
    password=MQTT_PASSWORD,
    socket_pool=pool,
    is_ssl=False,
)

mqtt_client.on_message = message_callback

print("Connecting to MQTT broker...")
try:
    mqtt_client.connect()
    print("Connected to MQTT broker!")
except Exception as e:
    print(f"Failed to connect to MQTT broker: {e}")

# Subscribe to both topics
mqtt_client.subscribe(MQTT_TOPIC)
mqtt_client.subscribe("heater/bedroom")

print("Listening for messages...")
while True:
    try:
        mqtt_client.loop()
        time.sleep(0.1)
    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(5)

