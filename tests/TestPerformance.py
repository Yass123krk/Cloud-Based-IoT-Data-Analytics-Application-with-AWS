""" This program is used to test the performance of the Flask app. 
    It sends a number of requests to the Flask app and measures the response time
    Attention !! : You can find further information about the execution in the file "Instructions.pdf" """


# Import necessary libraries
import requests
from concurrent.futures import ThreadPoolExecutor
import time

# Endpoint URL of the Flask app that was already printed out in the "CC_Initialisation.ipynb" program 
endpoint_url = 'http://3.84.104.185:8501/api/query'  #you should change this IP address to the IP address of your Flask app

# Sample payload for your Flask app's expected input
payload = {
    'startDate': '2023-12-25 00:00:00',
    'endDate': '2023-12-25 23:59:59',
    'country': 'DE',
    'minAqi': 0,
    'maxAqi': 10,
    'range': 'Low'
}

# Function to make a POST request and measure response time
def make_request():
    start_time = time.time()
    try:
        response = requests.post(endpoint_url, json=payload)
        end_time = time.time()

        # Calculate the response time in seconds  
        response_time = end_time - start_time

        if response.status_code == 200 or response.status_code == 202:
            return {'status': 'success', 'response_time': response_time}
        else:
            return {'status': 'error', 'response_time': response_time, 'error_message': response.text}
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        response_time = end_time - start_time
        return {'status': 'error', 'response_time': response_time, 'error_message': str(e)}

# Number of requests and concurrency level
num_requests = 1000  
concurrency_level = 100  

# Using ThreadPoolExecutor to simulate concurrent requests
success_count = 0
error_count = 0
total_response_time = 0
max_response_time = 0
min_response_time = float('inf')

with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
    futures = [executor.submit(make_request) for _ in range(num_requests)]

    for future in futures:
        result = future.result()
        total_response_time += result['response_time']
        max_response_time = max(max_response_time, result['response_time'])
        min_response_time = min(min_response_time, result['response_time'])

        if result['status'] == 'success':
            success_count += 1
        else:
            error_count += 1
            print(f"Error: {result['error_message']}")

# Calculating average response time
average_response_time = total_response_time / num_requests if num_requests else 0

# Output the results
print(f"Completed {num_requests} requests to the Flask app with a concurrency level of {concurrency_level}.")
print(f"Success Count: {success_count}, Error Count: {error_count}")
print(f"Average Response Time: {average_response_time:.4f} seconds")
print(f"Max Response Time: {max_response_time:.4f} seconds, Min Response Time: {min_response_time:.4f} seconds")
