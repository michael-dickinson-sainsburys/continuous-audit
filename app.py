#!/usr/bin/env python3

from aws_cdk import core

from continuous_audit.continuous_audit_stack import ContinuousAuditStack


app = core.App()
ContinuousAuditStack(app, "continuous-audit")

app.synth()
