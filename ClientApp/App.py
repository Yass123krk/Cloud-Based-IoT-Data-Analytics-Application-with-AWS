""" This is the Backend program of the ClientApp.
    It is used to query the data from the DynamoDB table and return the results in CSV format.
    Attention !! : You can find further information about the execution in the file "Instructions.pdf"
"""

from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key, Attr
import decimal
import json
import csv
from io import StringIO
import threading
import uuid
from threading import Lock

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Helper class to handle Decimal types in DynamoDB
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

# Initialize the DynamoDB client
dynamodb = boto3.resource(
                            'dynamodb',
                            aws_access_key_id='ASIAXPHZLJMCUPPKDH4N',
                            aws_secret_access_key='awBfOKJ4zJiWHYy1SY5Zlw4Uwb0/J0nLRw62P4R7',
                            aws_session_token='FwoGZXIvYXdzELX//////////wEaDEuGmcZV6CFqtVSTayLCAQsQNVrolT3MHb+BdBfVW4nPBNzUFnZmKsYub3Med3Tzy6p5g9U58FAU/kR/wyQTwRFEblmPmDKTWIHizwL3ffSQdkw6OfXTWXRqKagh+wKjEH0a7vPpz+RGL1y+qwkw5jo2sSvdnVQxoO2zR/2WDraqtrWsXu7xNKlRwtY5CgGEbhhemWT08wltz8G2C0CIgubowEfIIOjNdeqlJZjWfuHPALC15Zhp+GWiYPXS1DDU0MpVZ6ZtC4aWyQrkYrQ2Bl0WKMuTzqwGMi2xHVrlp4CoKGrGAiSGi14Yrp/a5/T/TdmOllVUv7fiPaHcGl1R8wVaaG6kcKk=', 
                            region_name='us-east-1'
)

sqs = boto3.client(         
                            'sqs', 
                            aws_access_key_id='ASIAXPHZLJMCUPPKDH4N',
                            aws_secret_access_key='awBfOKJ4zJiWHYy1SY5Zlw4Uwb0/J0nLRw62P4R7',
                            aws_session_token='FwoGZXIvYXdzELX//////////wEaDEuGmcZV6CFqtVSTayLCAQsQNVrolT3MHb+BdBfVW4nPBNzUFnZmKsYub3Med3Tzy6p5g9U58FAU/kR/wyQTwRFEblmPmDKTWIHizwL3ffSQdkw6OfXTWXRqKagh+wKjEH0a7vPpz+RGL1y+qwkw5jo2sSvdnVQxoO2zR/2WDraqtrWsXu7xNKlRwtY5CgGEbhhemWT08wltz8G2C0CIgubowEfIIOjNdeqlJZjWfuHPALC15Zhp+GWiYPXS1DDU0MpVZ6ZtC4aWyQrkYrQ2Bl0WKMuTzqwGMi2xHVrlp4CoKGrGAiSGi14Yrp/a5/T/TdmOllVUv7fiPaHcGl1R8wVaaG6kcKk=', 
                            region_name='us-east-1'
 )

request_queue_name = 'RequestSend'
response_queue_name = 'RequestReceive'
request_queue_url = sqs.get_queue_url(QueueName=request_queue_name)['QueueUrl']
response_queue_url = sqs.get_queue_url(QueueName=response_queue_name)['QueueUrl']
results = {}
active_requests = 0
active_requests_lock = Lock()
@app.route('/')
def index():
    return render_template('Request.html')

@app.route('/api/query', methods=['POST'])
def query_data():
    global active_requests
    with active_requests_lock:
        active_requests += 1

    try:
        data = request.json
        if active_requests > 100:
            unique_id = str(uuid.uuid4())
            data['id'] = unique_id
            try:
                sqs.send_message(QueueUrl=request_queue_url, MessageBody=json.dumps(data))
            except boto3.exceptions.Boto3Error as e:
                print(f"Error sending message to SQS: {e}")
                return jsonify({"error": "Error processing request"}), 500
            response = jsonify({"id": unique_id}), 202
        else:
            response = direct_query_processing(data)
    finally:
        with active_requests_lock:
            active_requests -= 1

    return response

def direct_query_processing(data):
    try:
        table = dynamodb.Table('QualityAirTable')
        filtering_exp = build_filter_expression(data)
        response = table.scan(FilterExpression=filtering_exp)
        return generate_csv_response(response.get('Items', []))
    except Exception as e:
        print(f"Error in direct query processing: {e}")
        return Response("Internal Server Error", status=500)

def build_filter_expression(data):
    filtering_exp = Attr('timestamp').between(data['startDate'], data['endDate'])
    if data.get('country'):
        filtering_exp &= Attr('loc_country').eq(data['country'])
    if data.get('range'):
        if data['range'] == 'All ranges':  # This should match the frontend exactly
            pass  # No filter applied for range if "All ranges" is selected
        else:
            filtering_exp &= Attr('Range').eq(data['range'])
    if data.get('minAqi') is not None:
        filtering_exp &= Attr('AQI').gte(int(data['minAqi']))
    if data.get('maxAqi') is not None:
        filtering_exp &= Attr('AQI').lte(int(data['maxAqi']))
    return filtering_exp


def generate_csv_response(items):
    if not items:
        return Response("No data found.", mimetype='text/plain', status=404)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(items[0].keys())  # Header
    for item in items:
        cw.writerow(item.values())  # Rows
    return Response(si.getvalue(), mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=query_results.csv"})


@app.route('/api/results/<query_id>', methods=['GET'])
def get_results(query_id):
    # Assuming 'results' is a dictionary holding the results temporarily
    if query_id in results:
        # Retrieve the message corresponding to the query_id
        message = results.pop(query_id)
        
        # Check if 'id' key is present in the message and remove it
        message.pop('id', None)
        
        # Convert the message back to JSON and return as response
        return jsonify(message)
    else:
        return jsonify({"status": "processing"}), 202

def poll_response_queue():
    while True:
        try:
            messages_response = sqs.receive_message(
                QueueUrl=response_queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20
            )

            if 'Messages' in messages_response:
                for message in messages_response['Messages']:
                    body = json.loads(message['Body'])
                    receipt_handle = message['ReceiptHandle']

                    with active_requests_lock:
                        query_id = body['id']
                        query_results = body['results']
                        results[query_id] = query_results

                    sqs.delete_message(
                        QueueUrl=response_queue_url,
                        ReceiptHandle=receipt_handle
                    )
        except Exception as e:
            print(f"Error polling response queue: {e}")

threading.Thread(target=poll_response_queue, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=False)
