import boto3
import json
import csv
from io import StringIO
from boto3.dynamodb.conditions import Key, Attr
import decimal

# Initialize AWS services
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

# Get the queue URLs from the queue names
request_queue_name = 'RequestSend'
response_queue_name = 'RequestReceive'
request_queue_url = sqs.get_queue_url(QueueName=request_queue_name)['QueueUrl']
response_queue_url = sqs.get_queue_url(QueueName=response_queue_name)['QueueUrl']

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def poll_request_queue():
    while True:
        try:
            response = sqs.receive_message(QueueUrl=request_queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=20)
            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        process_message(message)
                    except Exception as e:
                        print(f"Error processing message: {e}")
                    finally:
                        sqs.delete_message(QueueUrl=request_queue_url, ReceiptHandle=message['ReceiptHandle'])
        except boto3.exceptions.Boto3Error as e:
            print(f"Error receiving messages from SQS: {e}")

def process_message(message):
    try:
        body = json.loads(message['Body'])
        if all(key in body for key in ['startDate', 'endDate', 'id']):
            results = query_dynamodb(body)
            send_results_back(body['id'], results)
        else:
            print(f"Malformed message received: {body}")
    except Exception as e:
        print(f"Error processing message: {e}")


def query_dynamodb(data):
    try:
        table = dynamodb.Table('QualityAirTable')
        filtering_exp = build_filter_expression(data)
        response = table.scan(FilterExpression=filtering_exp)
        return convert_to_csv(response.get('Items', []))
    except boto3.exceptions.Boto3Error as e:
        print(f"Error querying DynamoDB: {e}")
        return "Error querying database"

def build_filter_expression(data):
    filtering_exp = Attr('timestamp').between(data['startDate'], data['endDate'])
    # Add more conditions based on 'data'
    return filtering_exp

def convert_to_csv(items):
    if not items:
        return "No data found for the given query parameters."
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(items[0].keys())  # Write headers
    for item in items:
        cw.writerow(item.values())  # Write item data
    return si.getvalue()

def send_results_back(id, results):
    try:
        payload = {'id': id, 'results': results}
        sqs.send_message(QueueUrl=response_queue_url, MessageBody=json.dumps(payload, cls=DecimalEncoder))
    except boto3.exceptions.Boto3Error as e:
        print(f"Error sending message back to SQS: {e}")

if __name__ == "__main__":
    poll_request_queue()