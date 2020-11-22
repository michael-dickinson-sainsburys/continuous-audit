#!/usr/bin/env python3

from aws_cdk import core
from pipeline.pipeline_stack import PipelineStack


app = core.App()
PipelineStack(app,
              "ProwlerPipeline",
              env={"account": "673792865749",
                   "region": "eu-west-2"})

app.synth()
