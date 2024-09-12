""" This script fetches the sensor data from the luftdaten.info 
    API and stores it in a DynamoDB table. 
    Attention !! : You can find further information about the execution in the file "Instructions.pdf"
"""
# Import necessary libraries
import requests
import boto3
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging
import time

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize a DynamoDB client
dynamodb = boto3.resource('dynamodb',
                            aws_access_key_id='xxx',
                            aws_secret_access_key='xxx',
                            aws_session_token='xxx', 
                            region_name='us-east-1')

# Define our DynamoDB table ,"QualityAirTable"
table = dynamodb.Table('QualityAirTable')

# Define a function to calculate the AQI and range label
def calculate_aqi(p1, p2):
    aqi_sensors = {
        'PM2.5': [
            (0, 11, 1), (12, 23, 2), (24, 35, 3), (36, 41, 4), (42, 47, 5),
            (48, 53, 6), (54, 58, 7), (59, 64, 8), (65, 70, 9), (71, float('inf'), 10)
        ],
        'PM10': [
            (0, 16, 1), (17, 33, 2), (34, 50, 3), (51, 58, 4), (59, 66, 5),
            (67, 75, 6), (76, 83, 7), (84, 91, 8), (92, 100, 9), (101, float('inf'), 10)
        ]
    }
    
    # Define the AQI ranges for PM2.5 and PM10
    aqi_p1 = next((aqi for low, high, aqi in aqi_sensors['PM2.5'] if p1 is not None and low <= p1 <= high), None)
    aqi_p2 = next((aqi for low, high, aqi in aqi_sensors['PM10'] if p2 is not None and low <= p2 <= high), None)
      
    if aqi_p1 is not None or aqi_p2 is not None:
        aqi = max(filter(lambda x: x is not None, [aqi_p1, aqi_p2]))
        range_label = 'Low' if aqi <= 3 else 'Medium' if aqi <= 6 else 'High' if aqi <= 9 else 'Very High'
        return aqi, range_label
    else:
        logging.error("Both PM values are None, cannot calculate AQI.")
        return None, None

# Define a function to convert floats to decimals
def float_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [float_to_decimal(x) for x in obj]
    return obj

# Define a function to store the data in DynamoDB
def store_data(data):
    logging.info("Storing data in DynamoDB...")
    for index, entry in enumerate(data):
        try:
            entry = float_to_decimal(entry)
            p1_value = next((Decimal(sdv['value']) for sdv in entry['sensordatavalues'] if sdv['value_type'] == 'P1'), None)
            p2_value = next((Decimal(sdv['value']) for sdv in entry['sensordatavalues'] if sdv['value_type'] == 'P2'), None)

            if p1_value is None and p2_value is None:
                logging.info(f"Skipping entry {index} as it doesn't contain P1 or P2 values.")
                continue

            aqi, range_label = calculate_aqi(p1_value, p2_value)
            if aqi is None or range_label is None:
                continue

            item = {
                'id': str(entry['id']),
                'timestamp': entry['timestamp'],
                'P1': p1_value,
                'P2': p2_value,
                'loc_id': str(entry['location']['id']),
                'loc_lat': entry['location']['latitude'],
                'loc_long': entry['location']['longitude'],
                'loc_alt': entry['location']['altitude'],
                'loc_country': entry['location']['country'],
                'AQI': aqi,
                'Range': range_label
            }

            table.put_item(Item=item)
            logging.info(f"Stored entry {index} with ID {item['id']} in DynamoDB.")

        except Exception as e:
            logging.error(f"Error at entry {index}: {e}")

# Define a function to fetch the sensor data
def fetch_sensor_data():
    url = "https://data.sensor.community/static/v2/data.24h.json"
    try:
        logging.info("Fetching sensor data...")
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching sensor data: {e}")
        raise

def main():
    logging.info("Script started.")
    sensor_data = fetch_sensor_data()
    store_data(sensor_data)
    logging.info("Data fetch and store completed.")

if __name__ == "__main__":
    main()