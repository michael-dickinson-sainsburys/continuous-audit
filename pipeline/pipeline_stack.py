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
            self_mutation=True,
            synth=pipelines.ShellStep(
                "Synth",
                input=pipelines.CodePipelineSource.connection(
                    "michael-dickinson-sainsburys/continuous-audit",
                    "main",
                    connection_arn="arn:aws:codestar-connections:eu-west-1:532982424333:connection/069ffc23-fa4c-4b97-890b-b4711a443dc3"
                ),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install --upgrade pip",
                    "pip install -r requirements.txt",
                    "cdk synth"
                ]
            )
        )

        pipeline.add_stage(ProwlerStage(
            self,
            "Test",
            env={"account": "532982424333",
                 "region": "eu-west-1"}
        ))
        iam.PermissionsBoundary.of(pipeline).apply(developer_policy)
