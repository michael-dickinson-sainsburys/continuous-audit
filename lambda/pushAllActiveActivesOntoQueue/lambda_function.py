import json
import os

import boto3


def lambda_handler(event, context):
    sqs = boto3.client("sqs")
    for account_id in get_account_ids():
        print(f"Processing {account_id}...")
        sqs.send_message(QueueUrl=os.environ["SQS_QUEUE_URL"],
                         MessageBody=json.dumps(format_payload(account_id,
                                                               "prowler")))
        print(f"Processed {account_id}.")
    return


def get_account_ids():
    return ["673792865749"]


def format_payload(account_id, role_path_and_name, session_duration=3600):
    if session_duration > 3600:
        raise Exception("The requested session_duration exceeds the 1 hour "
                        "session limit for roles assumed by role chaining. "
                        "Expected an integer less than 3601, got: "
                        f"{session_duration}")
    return {
        "AccountId": account_id,
        "RoleToAssume": role_path_and_name,
        "SessionDuration": str(session_duration)
    }
