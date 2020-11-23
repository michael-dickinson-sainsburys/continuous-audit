import json
import pytest

from aws_cdk import core
from continuous_audit.prowler_stack import ProwlerStack


def get_template():
    app = core.App()
    ProwlerStack(app, "Prowler")
    return json.dumps(app.synth().get_stack("Prowler").template)


def test_sqs_queue_created():
    assert("AWS::SQS::Queue" in get_template())
