import os

import boto3


def lambda_handler(event, context):
    sqs = boto3.client("sqs")
    for record in event['Records']:
        sqs.delete_message(
            QueueUrl=os.environ["QUEUE_URL"],
            ReceiptHandle=record['receiptHandle']
        )
