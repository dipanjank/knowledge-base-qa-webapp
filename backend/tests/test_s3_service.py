from unittest.mock import MagicMock

import pytest

from app.services.s3_service import S3Service


@pytest.fixture
def s3_client():
    return MagicMock()


@pytest.fixture
def s3_service(s3_client):
    service = S3Service(bucket="test-bucket", region="eu-west-1")
    service.client = s3_client
    return service


class TestUploadFile:
    def test_calls_put_object(self, s3_service, s3_client):
        s3_service.upload_file("path/to/file.txt", b"hello", "text/plain")
        s3_client.put_object.assert_called_once_with(
            Bucket="test-bucket", Key="path/to/file.txt", Body=b"hello", ContentType="text/plain"
        )

    def test_default_content_type(self, s3_service, s3_client):
        s3_service.upload_file("key", b"data")
        call_kwargs = s3_client.put_object.call_args[1]
        assert call_kwargs["ContentType"] == "application/octet-stream"

    def test_propagates_error(self, s3_service, s3_client):
        s3_client.put_object.side_effect = Exception("AccessDenied")
        with pytest.raises(Exception, match="AccessDenied"):
            s3_service.upload_file("key", b"data")
