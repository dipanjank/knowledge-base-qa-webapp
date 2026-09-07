import boto3


class S3Service:
    def __init__(self, bucket: str, region: str):
        self.client = boto3.client("s3", region_name=region)
        self.bucket = bucket

    def upload_file(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
