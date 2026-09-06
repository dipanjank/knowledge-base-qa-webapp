import boto3


class S3Service:
    """Downloads objects from an S3 bucket."""

    def __init__(self, bucket: str, region: str):
        self.client = boto3.client("s3", region_name=region)
        self.bucket = bucket

    def download_file(self, key: str) -> bytes:
        """Download a file from S3 and return its contents as bytes."""
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()
