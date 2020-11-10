import json
import os

import boto3


def lambda_handler(event, context):
    sqs = boto3.client("sqs")
    active_accounts = get_active_accounts("139288480916",
                                          os.environ['GLOBAL_READ_ONLY_ROLE'])
    for account in active_accounts:
        print(f"Processing {account['Id']}...")
        sqs.send_message(QueueUrl=os.environ["SQS_QUEUE_URL"],
                         MessageBody=json.dumps(format_payload(
                             account['Id'],
                             os.environ['GLOBAL_READ_ONLY_ROLE']
                         )))
        print(f"Processed {account['Id']}.")
    return


def get_active_accounts(orgs_master_account_id: str,
                        orgs_master_role: str) -> list:
    orgs_master_session = get_session_in(orgs_master_account_id,
                                         orgs_master_role)
    orgs_client = orgs_master_session.client("organizations")
    paginator = orgs_client.get_paginator("list_accounts")
    return [
        account
        for page in paginator.paginate()
        for account in page['Accounts']
        if account['Status'] == "ACTIVE"
    ]


def get_session_in(account_id: str,
                   role_path_and_name: str,
                   session: boto3.Session = None) -> boto3.Session:
    if session is None:
        client = boto3.client("sts")
    else:
        client = session.client("sts")
    assumed_creds = client.assume_role(
        RoleArn=f"arn:aws:sts::{account_id}:role{role_path_and_name}",
        RoleSessionName="SSM_Reporting"
    )['Credentials']
    return boto3.Session(aws_access_key_id=assumed_creds['AccessKeyId'],
                         aws_secret_access_key=assumed_creds['SecretAccessKey'],
                         aws_session_token=assumed_creds['SessionToken'])


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
