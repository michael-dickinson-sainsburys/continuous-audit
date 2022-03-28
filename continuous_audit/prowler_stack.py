import json
from os import path

from aws_cdk import (
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cloudwatch_actions,
    aws_ec2 as ec2,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_event_sources,
    aws_logs as logs,
    aws_s3 as s3,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_sqs as sqs,
    core
)


class ProwlerStack(core.Stack):
    def __init__(self,
                 scope: core.Construct,
                 id: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        developer_policy = iam.ManagedPolicy.from_managed_policy_name(self,
                                                                      "DeveloperPolicy",
                                                                      "ccoe/js-developer")
        iam.PermissionsBoundary.of(self).apply(developer_policy)

        queue = sqs.Queue(
            self,
            "StartProwlerScan",
            receive_message_wait_time=core.Duration.seconds(20),
            visibility_timeout=core.Duration.seconds(7200))
        push_all_active_accounts_onto_queue = lambda_.Function(
            self,
            "PushAllActiveAccountsOntoQueue",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset("lambda/pushAllActiveActivesOntoQueue"),
            handler="lambda_function.lambda_handler",
            environment={"SQS_QUEUE_URL": queue.queue_url,
                         "GLOBAL_READ_ONLY_ROLE": "/ccoe/ccoe-read-only"}
        )
        event_lambda_target = events_targets.LambdaFunction(
            handler=push_all_active_accounts_onto_queue
        )
        queue.grant_send_messages(push_all_active_accounts_onto_queue)
        schedule = events.Schedule.rate(core.Duration.days(1))
        events.Rule(self,
                    "DailyTrigger",
                    schedule=schedule,
                    targets=[event_lambda_target])

        vpc = ec2.Vpc.from_lookup(self, "VPC", is_default=False, vpc_name="sharedservices-dev")
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)
        logging = ecs.AwsLogDriver(stream_prefix="ProwlerTask",
                                   log_retention=logs.RetentionDays.ONE_DAY)
        results_bucket = s3.Bucket(self, "ResultsBucket")
        dockerfile_directory = path.join(
            path.dirname(path.realpath(__file__)),
            "docker"
        )
        image = ecr_assets.DockerImageAsset(self,
                                            "ProwlerImageBuild",
                                            directory=dockerfile_directory)
        prowler_task = ecs.FargateTaskDefinition(self,
                                                 "ProwlerTaskDefinition",
                                                 cpu=256,
                                                 memory_limit_mib=512)
        prowler_task.add_container(
            "Prowler_image",
            image=ecs.ContainerImage.from_docker_image_asset(image),
            logging=logging,
            environment={
                "RESULTS_BUCKET": results_bucket.bucket_name,
                "SQS_QUEUE_URL": queue.queue_url
            }
        )
        task_role = prowler_task.task_role
        task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("ReadOnlyAccess")
        )
        queue.grant(task_role, "sqs:DeleteMessage")
        results_bucket.grant_put(task_role)
        task_role.attach_inline_policy(
            iam.Policy(self,
                       "AssumeRolePermissions",
                       statements=[
                           iam.PolicyStatement(
                               actions=["sts:AssumeRole"],
                               effect=iam.Effect.ALLOW,
                               resources=["*"]
                           )
                       ])
        )
        run_fargate_task = lambda_.Function(
            self,
            "RunFargateTask",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset("lambda/runFargateTask"),
            handler="lambda_function.lambda_handler",
            environment={
                "CLUSTER_ARN": cluster.cluster_arn,
                "SUBNET_IDS": json.dumps(
                    [subnet.subnet_id for subnet in vpc.private_subnets]
                ),
                "QUEUE_URL": queue.queue_url,
                "TASK_DEFINITION_ARN": prowler_task.task_definition_arn
            }
        )
        queue.grant(run_fargate_task, "sqs:GetQueueAttributes")
        sqs_alarm_topic = sns.Topic(self, "SqsAlarmTopic")
        sqs_alarm_topic.grant_publish(run_fargate_task)
        sqs_alarm_queue = sqs.Queue(self,
                                    "SqsAlarmQueue",
                                    retention_period=core.Duration.days(14),
                                    visibility_timeout=core.Duration.minutes(3))
        sqs_alarm_topic.add_subscription(sns_subscriptions.SqsSubscription(
            sqs_alarm_queue
        ))
        run_fargate_task.add_event_source(
            lambda_event_sources.SqsEventSource(sqs_alarm_queue)
        )
        run_fargate_task.add_to_role_policy(
            iam.PolicyStatement(actions=["ecs:RunTask"],
                                effect=iam.Effect.ALLOW,
                                resources=[prowler_task.task_definition_arn])
        )
        run_fargate_task.add_to_role_policy(
            iam.PolicyStatement(actions=["iam:PassRole"],
                                effect=iam.Effect.ALLOW,
                                resources=[
                                    prowler_task.execution_role.role_arn,
                                    prowler_task.task_role.role_arn
                                ])
        )
        sqs_ok_topic = sns.Topic(self, "SqsOkTopic")
        clear_alarm_queue = lambda_.Function(
            self,
            "ClearAlarmQueue",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset("lambda/clearAlarmQueue"),
            handler="lambda_function.lambda_handler",
            environment={
                "QUEUE_URL": sqs_alarm_queue.queue_url
            }
        )
        clear_alarm_queue.add_event_source(
            lambda_event_sources.SnsEventSource(sqs_ok_topic)
        )
        sqs_alarm_queue.grant(clear_alarm_queue, "sqs:DeleteMessage")

        alarm = cloudwatch.Alarm(
            self,
            "FargateTaskTrigger",
            metric=queue.metric_approximate_number_of_messages_visible(
                period=core.Duration.seconds(60),
                statistic="max"
            ),
            evaluation_periods=1,
            threshold=1,
            alarm_description="Run a fargate task when there "
                              "are messages in the queue",
            treat_missing_data=cloudwatch.TreatMissingData.IGNORE
        )
        alarm.add_alarm_action(cloudwatch_actions.SnsAction(sqs_alarm_topic))
        alarm.add_ok_action(cloudwatch_actions.SnsAction(sqs_ok_topic))
