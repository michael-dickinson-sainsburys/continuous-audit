from aws_cdk import (
    aws_iam as iam,
    core,
    pipelines
)

from pipeline.prowler_stage import ProwlerStage


class PipelineStack(core.Stack):
    def __init__(self,
                 scope: core.Construct,
                 id: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        developer_policy = iam.ManagedPolicy.from_managed_policy_name(self,
                                                                      "DeveloperPolicy",
                                                                      "ccoe/js-developer")

        pipeline = pipelines.CodePipeline(
            self,
            "ContinuousAuditPipeline",
            cross_account_keys=True,
            self_mutation=True,
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(
                    "michael-dickinson-sainsburys/continuous-audit",
                    "main",
                    connection_arn="arn:aws:codestar-connections:eu-west-1:584517481562:connection/fcad54c1-9817-4447-80f2-df51c5a4cd37"
                ),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install --upgrade pip",
                    "pip install -r requirements.txt",
                    "cdk synth"
                ]
            )
        )

        iam.PermissionsBoundary.of(pipeline).apply(developer_policy)
        pipeline.add_stage(ProwlerStage(
            self,
            "Test",
            cfn_exec_role_arn="arn:aws:iam::584517481562:role/ccoe/cdk-cfn-exec-role",
            env={"account": "584517481562",
                 "region": "eu-west-1"},
            fargate_task_role_arn="arn:aws:iam::584517481562:role/ccoe/prowler-task-definition-role",
            vpc_name="JS_SS_VPC_Outbound_Internet"
        ))
        pipeline.add_stage(ProwlerStage(
            self,
            "Prod",
            cfn_exec_role_arn="arn:aws:iam::057726927330:role/ccoe/cdk-cfn-exec-role",
            env={"account": "057726927330",
                 "region": "eu-west-1"},
            fargate_task_role_arn="arn:aws:iam::057726927330:role/ccoe/prowler-task-definition-role",
            vpc_name="JS_SS_VPC_Outbound_Internet"
        ))
