from os import path

from aws_cdk import (
    aws_ecs as ecs,
    core
)


class ProwlerStack(core.Stack):
    def __init__(self,
                 scope: core.Construct,
                 id: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        prowler_task = ecs.FargateTaskDefinition(self,
                                                 "prowlerTaskDefinition",
                                                 cpu=256,
                                                 memory_limit_mib=512)
