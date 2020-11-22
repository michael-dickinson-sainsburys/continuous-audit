from aws_cdk import (
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
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

        source_artifact = codepipeline.Artifact()
        cloud_assembly_artifact = codepipeline.Artifact()

        pipeline = pipelines.CdkPipeline(
            self,
            "ContinuousAudit",
            cloud_assembly_artifact=cloud_assembly_artifact,
            pipeline_name="ContinuousAuditPipeline",
            source_action=codepipeline_actions.GitHubSourceAction(
                action_name="GitHub",
                branch="main",
                output=source_artifact,
                oauth_token=core.SecretValue.secrets_manager("github-token"),
                owner="michael-dickinson-sainsburys",
                repo="continuous-audit"
            ),
            synth_action=pipelines.SimpleSynthAction(
                source_artifact=source_artifact,
                cloud_assembly_artifact=cloud_assembly_artifact,
                install_commands=["npm install -g aws-cdk",
                                  "pip install -r requirements.txt"],
                synth_command="cdk synth"
            )
        )

        pipeline.add_application_stage(ProwlerStage(
            self,
            "Test",
            env={"account": "673792865749",
                 "region": "eu-west-2"}
        ))
