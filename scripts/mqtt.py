#!/usr/bin/python3
import paho.mqtt.client as mqtt
import subprocess
import sys
import math
import os

# Initializing global variables
MQTT_SERVER = ""
MQTT_PORT = ""
MQTT_KEEPALIVE_INTERVAL = ""
MQTT_UPS_TOPIC = ""

MQTT_USERNAME = ""
MQTT_PASSWORD = ""

UPS_HOST = ""
UPS_USERNAME = ""
UPS_PASSWORD = ""

# UPS parameters (replace with actual values)
BATTERY_VOLTAGE = ""  # Adjust based on your UPS battery voltage
BATTERY_CAPACITY = ""  # Adjust based on your UPS battery capacity in Ah
UPS_EFFICIENCY = ""
UPS_LOW_BATTERY_THRESHOLD = ""

DEBUG = False  # Default debug setting


def on_connect(client, userdata, flags, rc):
    if DEBUG:
        print("Connected with result code " + str(rc))
    client.subscribe(MQTT_UPS_TOPIC)


def calculate_battery_runtime(power_total, current_state_of_charge):
    if power_total == 0:
        return 0
    return (
        ((BATTERY_VOLTAGE * BATTERY_CAPACITY) / (power_total * 1000))
        * UPS_EFFICIENCY
        * (current_state_of_charge / 100)
        * 60
        * 60
    )


def get_env_var(var_name):
    """Retrieves an environment variable and exits if it's not set.

    Args:
      var_name: The name of the environment variable.

    Returns:
      The value of the environment variable.

    Raises:
      SystemExit: If the environment variable is not set.
    """

    value = os.environ.get(var_name)
    if value is None:
        print(f"Error: Environment variable '{var_name}' is not set.")
        exit(1)
    return value


def convert_seconds_to_time_string(seconds):
    days = math.floor(seconds / (24 * 3600))
    hours = math.floor((seconds - days * 24 * 3600) / 3600)
    minutes = math.floor((seconds - days * 24 * 3600 - hours * 3600) / 60)
    seconds = seconds - days * 24 * 3600 - hours * 3600 - minutes * 60

    time_string = ""
    if days > 0:
        time_string += f"{days} days, "
    if hours > 0:
        time_string += f"{hours} hours, "
    if minutes > 0:
        time_string += f"{minutes} minutes, "
    time_string += f"{seconds:.0f} seconds"
    return time_string


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    if "state_of_charge" in userdata:
        stored_state_of_charge = userdata["state_of_charge"]
    else:
        stored_state_of_charge = (
            100  # Setting up initial value for Battery State of Charge
        )

    if payload.startswith("state_of_charge="):
        if DEBUG:
            print(f"Received message on topic {topic}: {payload}")
        try:
            state_of_charge = float(payload.split("=")[1])
            userdata["state_of_charge"] = state_of_charge
            result = subprocess.run(
                [
                    "upsrw",
                    "-s",
                    f"battery.charge={state_of_charge}",
                    "-u",
                    UPS_USERNAME,
                    "-p",
                    UPS_PASSWORD,
                    UPS_HOST,
                ],
                capture_output=True,
                text=True,
            )
            if DEBUG:
                if result.returncode == 0:
                    print(f"upsrw command result: {result.stderr}")
            if result.returncode != 0:
                print(
                    f"upsrw command failed with exit code {result.returncode}, {result.stderr}"
                )
        except subprocess.CalledProcessError as e:
            print(f"Error executing upsrw: {e}")

    elif payload.startswith("power_total="):
        if DEBUG:
            print(f"Received message on topic {topic}: {payload}")
        try:
            power_total = float(payload.split("=")[1])
        except ValueError:
            power_total = 0  # Handle invalid values as 0

        battery_runtime = int(
            calculate_battery_runtime(power_total, stored_state_of_charge)
        )
        if battery_runtime > 0:
            formatted_time = convert_seconds_to_time_string(battery_runtime)
            try:
                print(
                    f"Based on the current UPS load: {power_total*1000}W and Battery SoC: {stored_state_of_charge}%, setting up estimated battery runtime to {formatted_time}"
                )
                result = subprocess.run(
                    [
                        "upsrw",
                        "-s",
                        f"battery.runtime={battery_runtime}",
                        "-u",
                        UPS_USERNAME,
                        "-p",
                        UPS_PASSWORD,
                        UPS_HOST,
                    ],
                    capture_output=True,
                    text=True,
                )
                if DEBUG:
                    if result.returncode == 0:
                        print(f"upsrw command result: {result.stderr}")
                if result.returncode != 0:
                    print(
                        f"upsrw command failed with exit code {result.returncode}, {result.stderr}"
                    )
            except subprocess.CalledProcessError as e:
                print(f"Error executing upsrw: {e}")

    elif payload.startswith("battery_mode="):
        if DEBUG:
            print(f"Received message on topic {topic}: {payload}")

        battery_mode = payload.split("=")[1]

        if battery_mode == 1:
            if stored_state_of_charge > UPS_LOW_BATTERY_THRESHOLD:
                ups_status = "OB"
            else:
                ups_status = "OB LB"
        else:
            ups_status = "OL"

        try:
            result = subprocess.run(
                [
                    "upsrw",
                    "-s",
                    f"ups.status={ups_status}",
                    "-u",
                    UPS_USERNAME,
                    "-p",
                    UPS_PASSWORD,
                    UPS_HOST,
                ],
                capture_output=True,
                text=True,
            )
            if DEBUG:
                if result.returncode == 0:
                    print(result.stderr)
            if result.returncode != 0:
                print(
                    f"upsrw command failed with exit code {result.returncode}, {result.stderr}"
                )
        except subprocess.CalledProcessError as e:
            print(f"Error executing upsrw: {e}")


if __name__ == "__main__":
    # MQTT server details
    MQTT_SERVER = get_env_var("MQTT_SERVER")
    MQTT_PORT = int(get_env_var("MQTT_PORT"))
    MQTT_KEEPALIVE_INTERVAL = int(get_env_var("MQTT_KEEPALIVE_INTERVAL"))
    MQTT_UPS_TOPIC = get_env_var("MQTT_UPS_TOPIC")

    # MQTT server username and password
    MQTT_USERNAME = get_env_var("MQTT_USERNAME")
    MQTT_PASSWORD = get_env_var("MQTT_PASSWORD")

    # UPS configuration
    UPS_HOST = "ups@localhost"
    UPS_USERNAME = get_env_var("UPS_USERNAME")
    UPS_PASSWORD = get_env_var("UPS_PASSWORD")

    # UPS parameters
    BATTERY_VOLTAGE = 36  # Loxone specific
    BATTERY_CAPACITY = get_env_var("BATTERY_CAPACITY")
    UPS_EFFICIENCY = 0.94  # Loxone specific
    UPS_LOW_BATTERY_THRESHOLD = get_env_var("UPS_LOW_BATTERY_THRESHOLD")

    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    userdata = {}  # Set up an empty dictionary in userdata for storing state_of_charge
    client.user_data_set(userdata)  # Associate the dictionary with the client

    client.connect(MQTT_SERVER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)

    client.loop_forever()
