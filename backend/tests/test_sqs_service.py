import json
from unittest.mock import MagicMock

import pytest

from app.services.sqs_service import SQSService


@pytest.fixture
def sqs_client():
    return MagicMock()


@pytest.fixture
def sqs_service(sqs_client):
    service = SQSService(queue_url="http://localhost:4566/queue/test", region="eu-west-1")
    service.client = sqs_client
    return service


class TestSendMessage:
    def test_sends_json_body(self, sqs_service, sqs_client):
        body = {"job_id": "abc-123", "user_id": "def-456"}
        sqs_service.send_message(body)
        sqs_client.send_message.assert_called_once_with(
            QueueUrl="http://localhost:4566/queue/test",
            MessageBody=json.dumps(body),
        )

    def test_propagates_error(self, sqs_service, sqs_client):
        sqs_client.send_message.side_effect = Exception("QueueDoesNotExist")
        with pytest.raises(Exception, match="QueueDoesNotExist"):
            sqs_service.send_message({"key": "value"})
