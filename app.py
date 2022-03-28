#!/usr/bin/env python3

from aws_cdk import core
from pipeline.pipeline_stack import PipelineStack


app = core.App()
PipelineStack(app,
              "ProwlerPipeline",
              env={"account": "532982424333",
                   "region": "eu-west-1"})

app.synth()
