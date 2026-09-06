from io import BytesIO
from unittest.mock import MagicMock

import pytest

from app.services.s3_service import S3Service


@pytest.fixture
def s3_client():
    return MagicMock()


@pytest.fixture
def s3_service(s3_client):
    service = S3Service(bucket="test-bucket", region="us-east-1")
    service.client = s3_client
    return service


class TestDownloadFile:
    def test_returns_file_bytes(self, s3_service, s3_client):
        body = MagicMock()
        body.read.return_value = b"hello world"
        s3_client.get_object.return_value = {"Body": body}

        result = s3_service.download_file("docs/test.txt")

        assert result == b"hello world"

    def test_calls_s3_with_correct_bucket_and_key(self, s3_service, s3_client):
        body = MagicMock()
        body.read.return_value = b""
        s3_client.get_object.return_value = {"Body": body}

        s3_service.download_file("path/to/file.txt")

        s3_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="path/to/file.txt")

    def test_reads_body_stream(self, s3_service, s3_client):
        body = MagicMock()
        body.read.return_value = b"content"
        s3_client.get_object.return_value = {"Body": body}

        s3_service.download_file("key")

        body.read.assert_called_once()

    def test_returns_binary_content(self, s3_service, s3_client):
        binary_data = bytes(range(256))
        body = MagicMock()
        body.read.return_value = binary_data
        s3_client.get_object.return_value = {"Body": body}

        result = s3_service.download_file("binary-file")

        assert result == binary_data

    def test_propagates_s3_error(self, s3_service, s3_client):
        s3_client.get_object.side_effect = Exception("NoSuchKey")

        with pytest.raises(Exception, match="NoSuchKey"):
            s3_service.download_file("missing-key")
