import json
import os

import boto3


def lambda_handler(event, context):
    print(json.dumps(event))
    sqs = boto3.client("sqs")
    queue_attributes = sqs.get_queue_attributes(
        QueueUrl=os.environ['QUEUE_URL'],
        AttributeNames=['ApproximateNumberOfMessages']
    )
    number_of_messages_in_queue = \
        int(queue_attributes['Attributes']['ApproximateNumberOfMessages'])
    ecs = boto3.client("ecs")
    while number_of_messages_in_queue > 0:
        tasks = ecs.run_task(
            cluster=os.environ['CLUSTER_ARN'],
            count=min(number_of_messages_in_queue, 10),
            enableECSManagedTags=True,
            launchType="FARGATE",
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": json.loads(os.environ['SUBNET_IDS'])
                }
            },
            taskDefinition=os.environ['TASK_DEFINITION_ARN'],
        )
        print(f"Launched {len(tasks['tasks'])} tasks.")
        number_of_messages_in_queue -= min(number_of_messages_in_queue, 10)
