# Databricks notebook source
# MAGIC %md
# MAGIC
# MAGIC ## Sending a test event to the Event HUB

# COMMAND ----------

from azure.eventhub import EventHubProducerClient, EventData
import json

# Event Hub configuration

# Getting secret value from Key Vault
eventhub_connection_string = dbutils.secrets.get(scope="key-vault-scope", key="eventhub-connection-string")

EVENT_HUB_NAME = "weatherstreamingeventhub"

# Initialize the Event Hub producer
producer = EventHubProducerClient.from_connection_string(conn_str=eventhub_connection_string, eventhub_name=EVENT_HUB_NAME)

# Function to send events to Event Hub
def send_event(event):
    event_data_batch = producer.create_batch()
    event_data_batch.add(EventData(json.dumps(event)))
    producer.send_batch(event_data_batch)

# Sample JSON event
event = {
    "event_id": 2222,
    "event_name": "Key Vault Test",
}

# Send the event
send_event(event)

# Close the producer
producer.close()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### API Testing

# COMMAND ----------

import requests
import json

# Getting secret value from Key Vault
weatherapikey = dbutils.secrets.get(scope="key-vault-scope", key="weatherapikey")
location = "Chennai"  # You can replace with city name based on your preference

base_url = "http://api.weatherapi.com/v1/"

current_weather_url = f"{base_url}/current.json"

params = {
    'key': weatherapikey,
    'q': location,
}
response = requests.get(current_weather_url, params=params)

if response.status_code == 200:
    current_weather = response.json()
    print("Current Weather:")
    print(json.dumps(current_weather, indent=3))
else:
    print(f"Error: {response.status_code}, {response.text}")

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### Complete code for getting weather data

# COMMAND ----------

import requests
import json

# Function to handle the API response
def handle_response(response):
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Function to get current weather and air quality data
def get_current_weather(base_url, api_key, location):
    current_weather_url = f"{base_url}/current.json"
    params = {
        'key': api_key,
        'q': location,
        "aqi": 'yes'
    }
    response = requests.get(current_weather_url, params=params)
    return handle_response(response)

# Function to get Forecast Data
def get_forecast_weather(base_url, api_key, location, days):
    forecast_url = f"{base_url}/forecast.json"
    params = {
        "key": api_key,
        "q": location,
        "days": days,
    }
    response = requests.get(forecast_url, params=params)
    return handle_response(response)

# Function to get Alerts
def get_alerts(base_url, api_key, location):
    alerts_url = f"{base_url}/alerts.json"
    params = {
        'key': api_key,
        'q': location,
        "alerts": 'yes'
    }
    response = requests.get(alerts_url, params=params)
    return handle_response(response)

# Flatten and merge the data
def flatten_data(current_weather, forecast_weather, alerts):
    location_data = current_weather.get("location", {})
    current = current_weather.get("current", {})
    condition = current.get("condition", {})
    air_quality = current.get("air_quality", {})
    forecast = forecast_weather.get("forecast", {}).get("forecastday", [])
    alert_list = alerts.get("alerts", {}).get("alert", [])

    flattened_data = {
        'name': location_data.get('name'),
        'region': location_data.get('region'),
        'country': location_data.get('country'),
        'lat': location_data.get('lat'),
        'lon': location_data.get('lon'),
        'localtime': location_data.get('localtime'),
        'temp_c': current.get('temp_c'),
        'is_day': current.get('is_day'),
        'condition_text': condition.get('text'),
        'condition_icon': condition.get('icon'),
        'wind_kph': current.get('wind_kph'),
        'wind_degree': current.get('wind_degree'),
        'wind_dir': current.get('wind_dir'),
        'pressure_in': current.get('pressure_in'),
        'precip_in': current.get('precip_in'),
        'humidity': current.get('humidity'),
        'cloud': current.get('cloud'),
        'feelslike_c': current.get('feelslike_c'),
        'uv': current.get('uv'),
        'air_quality': {
            'co': air_quality.get('co'),
            'no2': air_quality.get('no2'),
            'o3': air_quality.get('o3'),
            'so2': air_quality.get('so2'),
            'pm2_5': air_quality.get('pm2_5'),
            'pm10': air_quality.get('pm10'),
            'us-epa-index': air_quality.get('us-epa-index'),
            'gb-defra-index': air_quality.get('gb-defra-index')
        },
        'alerts': [
            {
                'headline': alert.get('headline'),
                'severity': alert.get('severity'),
                'description': alert.get('desc'),
                'instruction': alert.get('instruction')
            }
            for alert in alert_list
        ],
        'forecast': [
            {
                'date': day.get('date'),
                'maxtemp_c': day.get('day', {}).get('maxtemp_c'),
                'mintemp_c': day.get('day', {}).get('mintemp_c'),
                'condition': day.get('day', {}).get('condition', {}).get('text')
            }
            for day in forecast
        ]
    }
    return flattened_data

# Main program
def fetch_weather_data():

    base_url = "http://api.weatherapi.com/v1/"
    location = "Chennai"  # You can replace with any city name based on your preference
    weatherapikey = dbutils.secrets.get(scope="key-vault-scope", key="weatherapikey")

    # Get data from API
    current_weather = get_current_weather(base_url, weatherapikey, location)
    forecast_weather = get_forecast_weather(base_url, weatherapikey, location, 3)
    alerts = get_alerts(base_url, weatherapikey, location)

    # Flatten and merge data
    merged_data = flatten_data(current_weather, forecast_weather, alerts)
    print("Weather Data:", json.dumps(merged_data, indent=3))

# Calling the Main Program
fetch_weather_data()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Sending the complete weather data to the Event HUB

# COMMAND ----------

import requests
import json
from azure.eventhub import EventHubProducerClient, EventData

# Event Hub configuration

# Getting secret value from Key Vault
eventhub_connection_string = dbutils.secrets.get(scope="key-vault-scope", key="eventhub-connection-string")

EVENT_HUB_NAME = "weatherstreamingeventhub"

# Initialize the Event Hub producer
producer = EventHubProducerClient.from_connection_string(conn_str=eventhub_connection_string, eventhub_name=EVENT_HUB_NAME)

# Function to send events to Event Hub
def send_event(event):
    event_data_batch = producer.create_batch()
    event_data_batch.add(EventData(json.dumps(event)))
    producer.send_batch(event_data_batch)

# Function to handle the API response
def handle_response(response):
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Function to get current weather and air quality data
def get_current_weather(base_url, api_key, location):
    current_weather_url = f"{base_url}/current.json"
    params = {
        'key': api_key,
        'q': location,
        "aqi": 'yes'
    }
    response = requests.get(current_weather_url, params=params)
    return handle_response(response)

# Function to get Forecast Data
def get_forecast_weather(base_url, api_key, location, days):
    forecast_url = f"{base_url}/forecast.json"
    params = {
        "key": api_key,
        "q": location,
        "days": days,
    }
    response = requests.get(forecast_url, params=params)
    return handle_response(response)

# Function to get Alerts
def get_alerts(base_url, api_key, location):
    alerts_url = f"{base_url}/alerts.json"
    params = {
        'key': api_key,
        'q': location,
        "alerts": 'yes'
    }
    response = requests.get(alerts_url, params=params)
    return handle_response(response)

# Flatten and merge the data
def flatten_data(current_weather, forecast_weather, alerts):
    location_data = current_weather.get("location", {})
    current = current_weather.get("current", {})
    condition = current.get("condition", {})
    air_quality = current.get("air_quality", {})
    forecast = forecast_weather.get("forecast", {}).get("forecastday", [])
    alert_list = alerts.get("alerts", {}).get("alert", [])

    flattened_data = {
        'name': location_data.get('name'),
        'region': location_data.get('region'),
        'country': location_data.get('country'),
        'lat': location_data.get('lat'),
        'lon': location_data.get('lon'),
        'localtime': location_data.get('localtime'),
        'temp_c': current.get('temp_c'),
        'is_day': current.get('is_day'),
        'condition_text': condition.get('text'),
        'condition_icon': condition.get('icon'),
        'wind_kph': current.get('wind_kph'),
        'wind_degree': current.get('wind_degree'),
        'wind_dir': current.get('wind_dir'),
        'pressure_in': current.get('pressure_in'),
        'precip_in': current.get('precip_in'),
        'humidity': current.get('humidity'),
        'cloud': current.get('cloud'),
        'feelslike_c': current.get('feelslike_c'),
        'uv': current.get('uv'),
        'air_quality': {
            'co': air_quality.get('co'),
            'no2': air_quality.get('no2'),
            'o3': air_quality.get('o3'),
            'so2': air_quality.get('so2'),
            'pm2_5': air_quality.get('pm2_5'),
            'pm10': air_quality.get('pm10'),
            'us-epa-index': air_quality.get('us-epa-index'),
            'gb-defra-index': air_quality.get('gb-defra-index')
        },
        'alerts': [
            {
                'headline': alert.get('headline'),
                'severity': alert.get('severity'),
                'description': alert.get('desc'),
                'instruction': alert.get('instruction')
            }
            for alert in alert_list
        ],
        'forecast': [
            {
                'date': day.get('date'),
                'maxtemp_c': day.get('day', {}).get('maxtemp_c'),
                'mintemp_c': day.get('day', {}).get('mintemp_c'),
                'condition': day.get('day', {}).get('condition', {}).get('text')
            }
            for day in forecast
        ]
    }
    return flattened_data

# Main program
def fetch_weather_data():

    base_url = "http://api.weatherapi.com/v1/"
    location = "Chennai"  # You can replace with any city name based on your preference
    weatherapikey = dbutils.secrets.get(scope="key-vault-scope", key="weatherapikey")

    # Get data from API
    current_weather = get_current_weather(base_url, weatherapikey, location)
    forecast_weather = get_forecast_weather(base_url, weatherapikey, location, 3)
    alerts = get_alerts(base_url, weatherapikey, location)

    # Flatten and merge data
    merged_data = flatten_data(current_weather, forecast_weather, alerts)

    # Sending the weather data to Event HUB
    send_event(merged_data)
    

# Calling the Main Program
fetch_weather_data()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ## Sending the weather data in streaming fashion

# COMMAND ----------

from azure.eventhub import EventHubProducerClient, EventData
import json
import requests

# Event Hub configuration
EVENT_HUB_NAME = "weatherstreamingeventhub"
eventhub_connection_string = dbutils.secrets.get(scope="key-vault-scope", key="eventhub-connection-string")
weatherapikey = dbutils.secrets.get(scope="key-vault-scope", key="weatherapikey")

# Initialize the Event Hub producer
producer = EventHubProducerClient.from_connection_string(conn_str=eventhub_connection_string, eventhub_name=EVENT_HUB_NAME)

# Function to send events to Event Hub
def send_event(event):
    event_data_batch = producer.create_batch()
    event_data_batch.add(EventData(json.dumps(event)))
    producer.send_batch(event_data_batch)

# Function to handle the API response
def handle_response(response):
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Function to get current weather and air quality data
def get_current_weather(base_url, api_key, location):
    current_weather_url = f"{base_url}/current.json"
    params = {
        'key': api_key,
        'q': location,
        "aqi": 'yes'
    }
    response = requests.get(current_weather_url, params=params)
    return handle_response(response)

# Function to get Forecast Data
def get_forecast_weather(base_url, api_key, location, days):
    forecast_url = f"{base_url}/forecast.json"
    params = {
        "key": api_key,
        "q": location,
        "days": days,
    }
    response = requests.get(forecast_url, params=params)
    return handle_response(response)

# Function to get Alerts
def get_alerts(base_url, api_key, location):
    alerts_url = f"{base_url}/forecast.json"
    params = {
        'key': api_key,
        'q': location,
        "alerts": 'yes'
    }
    response = requests.get(alerts_url, params=params)
    return handle_response(response)

# Flatten and merge the data
def flatten_data(current_weather, forecast_weather, alerts):
    location_data = current_weather.get("location", {})
    current = current_weather.get("current", {})
    condition = current.get("condition", {})
    air_quality = current.get("air_quality", {})
    forecast = forecast_weather.get("forecast", {}).get("forecastday", [])
    alert_list = alerts.get("alerts", {}).get("alert", [])

    flattened_data = {
        'name': location_data.get('name'),
        'region': location_data.get('region'),
        'country': location_data.get('country'),
        'lat': location_data.get('lat'),
        'lon': location_data.get('lon'),
        'localtime': location_data.get('localtime'),
        'temp_c': current.get('temp_c'),
        'is_day': current.get('is_day'),
        'condition_text': condition.get('text'),
        'condition_icon': condition.get('icon'),
        'wind_kph': current.get('wind_kph'),
        'wind_degree': current.get('wind_degree'),
        'wind_dir': current.get('wind_dir'),
        'pressure_in': current.get('pressure_in'),
        'precip_in': current.get('precip_in'),
        'humidity': current.get('humidity'),
        'cloud': current.get('cloud'),
        'feelslike_c': current.get('feelslike_c'),
        'uv': current.get('uv'),
        'air_quality': {
            'co': air_quality.get('co'),
            'no2': air_quality.get('no2'),
            'o3': air_quality.get('o3'),
            'so2': air_quality.get('so2'),
            'pm2_5': air_quality.get('pm2_5'),
            'pm10': air_quality.get('pm10'),
            'us-epa-index': air_quality.get('us-epa-index'),
            'gb-defra-index': air_quality.get('gb-defra-index')
        },
        'alerts': [
            {
                'headline': alert.get('headline'),
                'severity': alert.get('severity'),
                'description': alert.get('desc'),
                'instruction': alert.get('instruction')
            }
            for alert in alert_list
        ],
        'forecast': [
            {
                'date': day.get('date'),
                'maxtemp_c': day.get('day', {}).get('maxtemp_c'),
                'mintemp_c': day.get('day', {}).get('mintemp_c'),
                'condition': day.get('day', {}).get('condition', {}).get('text')
            }
            for day in forecast
        ]
    }
    return flattened_data


def fetch_weather_data():

    base_url = "http://api.weatherapi.com/v1/"
    location = "Chennai" # You can replace with any city name based on your preference
    weatherapikey = dbutils.secrets.get(scope="key-vault-scope", key="weatherapikey")

    # Get data from API
    current_weather = get_current_weather(base_url, weatherapikey, location)
    forecast_weather = get_forecast_weather(base_url, weatherapikey, location, 3)
    alerts = get_alerts(base_url, weatherapikey, location)

    # Flatten and merge data
    merged_data = flatten_data(current_weather, forecast_weather, alerts)
    return merged_data

# Main program
def process_batch(batch_df, batch_id):
    try:     
        # Fetch weather data
        weather_data = fetch_weather_data()
        
        # Send the weather data (current weather part)
        send_event(weather_data)

    except Exception as e:
        print(f"Error sending events in batch {batch_id}: {str(e)}")
        raise e

# Set up a streaming source (for example, rate source for testing purposes)
streaming_df = spark.readStream.format("rate").option("rowsPerSecond", 1).load()

# Write the streaming data using foreachBatch to send weather data to Event Hub
query = streaming_df.writeStream.foreachBatch(process_batch).start()

query.awaitTermination()

# Close the producer after termination
producer.close()

# COMMAND ----------

# MAGIC %md
# MAGIC
# MAGIC ### Sending the weather data to Event HUB in every 30 seconds

# COMMAND ----------

from azure.eventhub import EventHubProducerClient, EventData
import json
import requests
from datetime import datetime, timedelta

# Event Hub configuration
EVENT_HUB_NAME = "weatherstreamingeventhub"
eventhub_connection_string = dbutils.secrets.get(scope="key-vault-scope", key="eventhub-connection-string")
weatherapikey = dbutils.secrets.get(scope="key-vault-scope", key="weatherapikey")

# Initialize the Event Hub producer
producer = EventHubProducerClient.from_connection_string(conn_str=eventhub_connection_string, eventhub_name=EVENT_HUB_NAME)

# Function to send events to Event Hub
def send_event(event):
    event_data_batch = producer.create_batch()
    event_data_batch.add(EventData(json.dumps(event)))
    producer.send_batch(event_data_batch)

# Function to handle the API response
def handle_response(response):
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}, {response.text}"

# Function to get current weather and air quality data
def get_current_weather(base_url, api_key, location):
    current_weather_url = f"{base_url}/current.json"
    params = {
        'key': api_key,
        'q': location,
        "aqi": 'yes'
    }
    response = requests.get(current_weather_url, params=params)
    return handle_response(response)

# Function to get Forecast Data
def get_forecast_weather(base_url, api_key, location, days):
    forecast_url = f"{base_url}/forecast.json"
    params = {
        "key": api_key,
        "q": location,
        "days": days,
    }
    response = requests.get(forecast_url, params=params)
    return handle_response(response)

# Function to get Alerts
def get_alerts(base_url, api_key, location):
    alerts_url = f"{base_url}/forecast.json"
    params = {
        'key': api_key,
        'q': location,
        "alerts": 'yes'
    }
    response = requests.get(alerts_url, params=params)
    return handle_response(response)

# Flatten and merge the data
def flatten_data(current_weather, forecast_weather, alerts):
    location_data = current_weather.get("location", {})
    current = current_weather.get("current", {})
    condition = current.get("condition", {})
    air_quality = current.get("air_quality", {})
    forecast = forecast_weather.get("forecast", {}).get("forecastday", [])
    alert_list = alerts.get("alerts", {}).get("alert", [])

    flattened_data = {
        'name': location_data.get('name'),
        'region': location_data.get('region'),
        'country': location_data.get('country'),
        'lat': location_data.get('lat'),
        'lon': location_data.get('lon'),
        'localtime': location_data.get('localtime'),
        'temp_c': current.get('temp_c'),
        'is_day': current.get('is_day'),
        'condition_text': condition.get('text'),
        'condition_icon': condition.get('icon'),
        'wind_kph': current.get('wind_kph'),
        'wind_degree': current.get('wind_degree'),
        'wind_dir': current.get('wind_dir'),
        'pressure_in': current.get('pressure_in'),
        'precip_in': current.get('precip_in'),
        'humidity': current.get('humidity'),
        'cloud': current.get('cloud'),
        'feelslike_c': current.get('feelslike_c'),
        'uv': current.get('uv'),
        'air_quality': {
            'co': air_quality.get('co'),
            'no2': air_quality.get('no2'),
            'o3': air_quality.get('o3'),
            'so2': air_quality.get('so2'),
            'pm2_5': air_quality.get('pm2_5'),
            'pm10': air_quality.get('pm10'),
            'us-epa-index': air_quality.get('us-epa-index'),
            'gb-defra-index': air_quality.get('gb-defra-index')
        },
        'alerts': [
            {
                'headline': alert.get('headline'),
                'severity': alert.get('severity'),
                'description': alert.get('desc'),
                'instruction': alert.get('instruction')
            }
            for alert in alert_list
        ],
        'forecast': [
            {
                'date': day.get('date'),
                'maxtemp_c': day.get('day', {}).get('maxtemp_c'),
                'mintemp_c': day.get('day', {}).get('mintemp_c'),
                'condition': day.get('day', {}).get('condition', {}).get('text')
            }
            for day in forecast
        ]
    }
    return flattened_data


def fetch_weather_data():

    base_url = "http://api.weatherapi.com/v1/"
    location = "Chennai"  # You can replace with any city name based on your preference
    weatherapikey = dbutils.secrets.get(scope="key-vault-scope", key="weatherapikey")

    # Get data from API
    current_weather = get_current_weather(base_url, weatherapikey, location)
    forecast_weather = get_forecast_weather(base_url, weatherapikey, location, 3)
    alerts = get_alerts(base_url, weatherapikey, location)

    # Flatten and merge data
    merged_data = flatten_data(current_weather, forecast_weather, alerts)
    return merged_data

# Function to process each batch of streaming data
last_sent_time = datetime.now() - timedelta(seconds=30)  # Initialize last sent time


# Main program
def process_batch(batch_df, batch_id):
    global last_sent_time
    try:
        # Get current time
        current_time = datetime.now()
        
        # Check if 30 seconds have passed since last event was sent
        if (current_time - last_sent_time).total_seconds() >= 30:
            # Fetch weather data
            weather_data = fetch_weather_data()
            
            # Send the weather data (current weather part)
            send_event(weather_data)

            # Update last sent time
            last_sent_time = current_time
            print(f'Event Sent at {last_sent_time}')

    except Exception as e:
        print(f"Error sending events in batch {batch_id}: {str(e)}")
        raise e

# Set up a streaming source (for example, rate source for testing purposes)
streaming_df = spark.readStream.format("rate").option("rowsPerSecond", 1).load()

# Write the streaming data using foreachBatch to send weather data to Event Hub
query = streaming_df.writeStream.foreachBatch(process_batch).start()

query.awaitTermination()

# Close the producer after termination
producer.close()
