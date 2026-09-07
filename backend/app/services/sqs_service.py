import json

import boto3


class SQSService:
    def __init__(self, queue_url: str, region: str):
        self.client = boto3.client("sqs", region_name=region)
        self.queue_url = queue_url

    def send_message(self, body: dict) -> None:
        self.client.send_message(QueueUrl=self.queue_url, MessageBody=json.dumps(body))
