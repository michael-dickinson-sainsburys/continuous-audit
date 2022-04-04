#!/usr/bin/env python3

from aws_cdk import core
from pipeline.pipeline_stack import PipelineStack


app = core.App()
PipelineStack(app,
              "ProwlerPipeline",
              env={"account": "584517481562",
                   "region": "eu-west-1"},
              synthesizer=core.DefaultStackSynthesizer(
                  deploy_role_arn="arn:aws:iam::584517481562:role/ccoe/cdk-cfn-deploy-role",
                  cloud_formation_execution_role="arn:aws:iam::584517481562:role/ccoe/cdk-cfn-exec-role"
              ))

app.synth()
