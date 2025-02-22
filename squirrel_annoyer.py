# run by calling `nuts` on terminal. 
# Alias configured in C:\Users\PC\OneDrive\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
# view aliases with `$profile`
import os
import time
import datetime
import logging
import cv2
import base64
import requests
import urllib3
import pygame
import numpy as np
import random
import shutil  # Import this to move files
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from openai import OpenAI
from colorama import Fore, Back, Style, init
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, timedelta
from pytz import timezone

# ==========================
# Configuration
# ==========================
load_dotenv("/home/eli/git/scripts/squirrel_anoyer/.env")
CAMERA_IP = os.getenv("CAMERA_IP")
CAMERA_USER = os.getenv("CAMERA_USER")
CAMERA_PASS = os.getenv("CAMERA_PASS")
CAPTURE_INTERVAL = 60  # seconds between captures
DATA_FOLDER = "C:\\Users\\PC\\squirreldata"
IMAGES_FOLDER = os.path.join(DATA_FOLDER, "images")
POSITIVE_DETECTION_FOLDER = os.path.join(IMAGES_FOLDER, "positive_detection")
LOG_FILE = os.path.join(DATA_FOLDER, "log.txt")

# MQTT Configuration
MQTT_BROKER = os.getenv("MQTT_BROKER")  
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME") 
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")  

iteration = 0
urllib3.disable_warnings() # disable HTTPS cert warnings. See:https://urllib3.readthedocs.io/en/latest/advanced-usage.html#tls-warnings

# Set to True for verbose print statements
DEBUG_DEFAULT = False

# Crop coordinates (left, top, right, bottom) 
CROP_COORDS = (1700, 375, 2000, 812)  

# ==========================
# Setup
# ==========================
os.makedirs(POSITIVE_DETECTION_FOLDER, exist_ok=True) 
os.makedirs(IMAGES_FOLDER, exist_ok=True)

logging.basicConfig(filename=LOG_FILE,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    level=logging.INFO)
# Initialize colorama
init(autoreset=True)

# ==========================
# Helper Functions
# ==========================

def debug_print(msg, debug=DEBUG_DEFAULT, style="normal"):
    """
    Prints debug messages with styled formatting based on the style parameter.
    Supported styles: highlight, danger, warn, muted, whimsylicious
    """
    if not debug:
        return

    # Define styles
    if style == "highlight":
        formatted_msg = Fore.GREEN + Style.BRIGHT + msg
    elif style == "danger":
        formatted_msg = Fore.RED + Style.BRIGHT + msg
    elif style == "warn":
        formatted_msg = Fore.YELLOW + Style.BRIGHT + msg
    elif style == "muted":
        formatted_msg = Fore.WHITE + Style.DIM + msg
    elif style == "whimsylicious":
        # Generate a random mix of colors for each character
        formatted_msg = "".join(
            random.choice([
                Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE,
                Fore.MAGENTA, Fore.CYAN, Back.RED, Back.GREEN,
                Back.YELLOW, Back.BLUE, Back.MAGENTA, Back.CYAN
            ]) + Style.BRIGHT + char
            for char in msg
        )
    else:  # Default style
        formatted_msg = msg

    print(formatted_msg)

def encode_image(image_path):
    """
    Encodes the image at the given path to a base64 string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def capture_snapshot(debug=DEBUG_DEFAULT):
    """
    Downloads a single snapshot JPEG from the camera’s snapshot URL 
    and returns it as a CV2 image (numpy array).
    """
    # Use your camera’s IP and credentials from .env
    snapshot_url = f"https://{CAMERA_IP}/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user={CAMERA_USER}&password={CAMERA_PASS}"

    if debug:
        print(f"Fetching snapshot from camera") #{snapshot_url}")

    # Disable SSL certificate verification for now; 
    # can add a proper certificate or turn verification on if desired.
    response = requests.get(snapshot_url, verify=False)
    response.raise_for_status()  # Raise an error if request failed

    # Convert JPEG bytes to a numpy array
    img_array = np.frombuffer(response.content, np.uint8)
    # Decode the image using OpenCV
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode the image from the camera.")

    if debug:
        print("Snapshot captured successfully.")

    return img
    # """Captures a single snapshot from the Reolink camera."""
    # # Using the reolinkapi
    # cam = Camera(CAMERA_IP, CAMERA_USER, CAMERA_PASS, https=True)
    # # This gets a stream generator; we'll just grab a single frame.
    # stream = cam.open_video_stream()
    # img = next(stream)
    # debug_print("Captured image from camera.", debug)
    # return img

def crop_image(img, coords, debug=DEBUG_DEFAULT):
    """Crops the image using the given coordinates. 
       Coordinates are (left, top, right, bottom)."""
    left, top, right, bottom = coords
    cropped_img = img[top:bottom, left:right]
    debug_print(f"Cropped image with coords: {coords}", debug, "muted")
    return cropped_img

def save_image(img, timestamp, debug=DEBUG_DEFAULT):
    """Saves the image with a filename based on the timestamp."""
    filename = os.path.join(IMAGES_FOLDER, f"{timestamp}.jpg")
    cv2.imwrite(filename, img)
    debug_print(f"Saved image to {filename}", debug, "muted")
    return filename

def log_event(message):
    """Logs the given message with a timestamp."""
    logging.info(message)

def submit_to_model(image_path, debug=DEBUG_DEFAULT):
    """
    Submits the image to the OpenAI model to detect squirrels.
    Returns True if a squirrel is detected, False otherwise.
    """
    debug_print(f"Submitting {image_path} to model.", debug)

    # Initialize OpenAI client
    client = OpenAI()

    try:
        # Encode the image to base64
        base64_image = encode_image(image_path)
        if debug:
            debug_print(f"Image successfully encoded to base64.", debug)

        # Create the API request
        response = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Is there a squirrel in the image? Answer with one word: yes or no.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            max_tokens=1000,
        )

        # Extract the response
        answer = response.choices[0].message.content.strip().lower()
        answer = answer.rstrip(".")
        debug_print(f"Model response: {repr(answer)}", debug, "highlight")
        

        return answer == "yes"

    except Exception as e:
        debug_print(f"Error querying OpenAI API: {str(e)}", debug)
        return False


def confirm_detection(debug=DEBUG_DEFAULT):
    """After a positive detection, take 2 more snapshots quickly and confirm if at least one more is also positive."""
    debug_print("Confirming detection with 2 additional shots.", debug)

    for i in range(2):
        img = capture_snapshot(debug)
        # Crop the image
        cropped = crop_image(img, CROP_COORDS, debug)
        # Save the image
        ts = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_f{i}"
        image_path = save_image(cropped, ts, debug)
        # Submit to model
        if submit_to_model(image_path, debug):
            debug_print(f"Snapshot {i+1}: Model response - yes", debug, "warn")
            # Move file to the "positive_detection" sub-folder
            new_path = os.path.join(POSITIVE_DETECTION_FOLDER, os.path.basename(image_path))
            shutil.move(image_path, new_path)
            debug_print(f"Image moved to {new_path}", debug)
            return True
        else:
            debug_print(f"Snapshot {i+1}: Model response - no", debug, "warn")
            
        # Small delay between confirmation shots if needed
        # time.sleep(0.5)

    return False

def play_alert(debug=DEBUG_DEFAULT):
    """
    Plays an alert sound located in the DATA_FOLDER.
    """
    alert_file = os.path.join(DATA_FOLDER, "scream.wav")  

    if not os.path.exists(alert_file):
        raise FileNotFoundError(f"Alert sound file not found: {alert_file}")

    if debug:
        print(f"Playing alert sound from {alert_file}")

    # Initialize the mixer
    pygame.mixer.init()
    try:
        # Load and play the sound
        pygame.mixer.music.load(alert_file)
        pygame.mixer.music.play()
        
        # Wait until the sound finishes
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    except Exception as e:
        print(f"Error playing alert sound: {e}")
    finally:
        pygame.mixer.quit()

# Function to publish MQTT alert
def send_mqtt_alert(message, debug=DEBUG_DEFAULT):
    """
    Publishes an alert message to the configured MQTT broker and topic.
    """
    if not MQTT_BROKER or not MQTT_TOPIC:
        raise ValueError("MQTT_BROKER or MQTT_TOPIC is not set. Check your .env file.")

    if debug:
        print(f"Connecting to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        print(f"MQTT_USER: {MQTT_USERNAME}, MQTT_PASS: {MQTT_PASSWORD}")
        print(f"MQTT_BROKER: {MQTT_BROKER}, MQTT_PORT: {MQTT_PORT} (type: {type(MQTT_PORT)})")

    client = mqtt.Client()
    
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    else:
        print("MQTT username or password is missing. Check your .env file.")

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        if debug:
            print(f"Publishing message to topic {MQTT_TOPIC}: {message}")

        client.publish(MQTT_TOPIC, message)
        client.disconnect()

        if debug:
            print("MQTT message sent successfully.")
    except Exception as e:
        if debug:
            print(f"Failed to send MQTT message: {e}")
                    
def is_within_daylight():
    city = LocationInfo("Hilton Head Island", "US", "America/New_York", 32.155705183279615, -80.76296652972201)
    s = sun(city.observer, date=datetime.now())

    # Get the local timezone
    local_tz = timezone(city.timezone)

    # Convert current time to offset-aware in the same timezone as `sun` results
    now = datetime.now(local_tz)

    return s['sunrise'] <= now <= s['sunset']

def suns_out_buns_out():
    """
    Prints a colorful 'Suns Out, Buns Out' message with emojis using Colorama.
    """
    sun_emoji = "☀️"
    peach_emoji = "🍑"

    # The obnoxious message with colors
    message = (
        Fore.YELLOW + Style.BRIGHT + sun_emoji +
        Fore.MAGENTA + Style.BRIGHT + " Suns Out, " +
        Fore.YELLOW + Style.BRIGHT + sun_emoji +
        Fore.CYAN + Style.BRIGHT + " Buns Out! " +
        Fore.MAGENTA + peach_emoji +
        Fore.YELLOW + sun_emoji
    )
    print(message)

def sleepy_desk_art(debug=DEBUG_DEFAULT, ai=False):
    """
    Makes an OpenAI call to generate a fun sleepy phrase, then displays it with emojis.
    Debugging is added to trace potential issues with the API call.
    """
    if ai:
        client = OpenAI()
        debug_print("Starting OpenAI call to generate a sleepy phrase...", debug, "muted")
        try:
            # Make the OpenAI API call to get a sleepy phrase
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": "Write a fun and sleepy phrase in less than 50 characters."
                    }
                ],
                max_tokens=20,
            )
            # Extract the phrase from the API response
            phrase = response.choices[0].message.content.strip()
            debug_print(f"OpenAI API response: {repr(phrase)}", debug, "highlight")

        except Exception as e:
            # Log error details for debugging
            error_message = f"OpenAI call failed: {str(e)}"
            debug_print(error_message, debug, "danger")
            # Use a default phrase in case of failure
            phrase = "Dreaming of squirrels... 💤"
    else:
        phrase = "nut in my pussy daddy... 💤"

    # Display the phrase with emojis
    art = (
        Fore.MAGENTA + Style.BRIGHT +
        f"""
        🛌💤 {phrase} 💤😴
        😴🌙
        """
    )
    debug_print("Displaying sleepy art message.", debug, "highlight")
    print(art)



# ==========================
# Main Loop
# ==========================

def main(debug=True):
    global iteration
    iteration += 1
    print("Current iteration: " + str(iteration) + ".")

    debug_print("Starting single capture test...", debug)
    debug_print("user is " + CAMERA_USER, debug)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Capture one image
    img = capture_snapshot(debug)

    # Crop the image
    cropped_img = crop_image(img, CROP_COORDS, debug)

    # Save the image
    image_path = save_image(cropped_img, timestamp, debug)

    # Send to OpenAI for Processing
    squirrel_detected = submit_to_model(image_path, debug)
    debug_print(f"Squirrel detected status = {squirrel_detected} ", debug)

    debug_print(f"Test complete. Image saved at {image_path}", debug)

    if squirrel_detected:
        debug_print("Squirrel detected. Initiating confirmation steps.", debug)
        # Log preliminary detection
        log_event(f"{timestamp}: Preliminary squirrel detection.")
        
        # Move file to the "positive_detection" sub-folder
        new_path = os.path.join(POSITIVE_DETECTION_FOLDER, os.path.basename(image_path))
        shutil.move(image_path, new_path)
        debug_print(f"Image moved to {new_path}", debug)

        # Confirm detection
        if confirm_detection(debug):
            log_event(f"{timestamp}: Confirmed squirrel detection.")
            play_alert()
            debug_print("Squirrel detection confirmed.", debug)

            # Send MQTT alert
            alert_message = f"fire"
            send_mqtt_alert(alert_message, debug)

        else:
            log_event(f"{timestamp}: Detection not confirmed.")
            debug_print("Squirrel detection not confirmed after additional checks.", debug)
    else:
        log_event(f"{timestamp}: No squirrel detected.")


if __name__ == "__main__":
    
    while True:
        if is_within_daylight():
            suns_out_buns_out()
            main()
        else:
            sleepy_desk_art()
        
        # Wait before next capture
        time.sleep(CAPTURE_INTERVAL)
   

