from aws_cdk import core

from prowler_stack import ProwlerStack


class ProwlerStage(core.Stage):
    def __init__(self,
                 scope: core.Construct,
                 id: str,
                 fargate_task_role_arn: str,
                 vpc_name: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        prowler = ProwlerStack(self,
                               "Prowler",
                               fargate_task_role_arn=fargate_task_role_arn,
                               vpc_name=vpc_name)
