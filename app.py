#!/usr/bin/env python3

from aws_cdk import core

from continuous_audit.prowler_stack import ProwlerStack


app = core.App()
ProwlerStack(app, "prowler")

app.synth()
