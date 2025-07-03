
import unittest
from unittest.mock import patch, MagicMock

from src.backup import manager


class TestBackup(unittest.TestCase):
    @patch("src.backup.manager.boto3.client")
    def test_backup_creation(self, mock_boto3_client):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        backup_manager = manager.BackupManager(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            s3_bucket="test_bucket",
        )
        with patch("src.backup.manager.shutil.make_archive"):
            with patch("src.backup.manager.os.remove"):
                backup_key = backup_manager.create_backup("/tmp/test_data")
                self.assertIsNotNone(backup_key)
                mock_s3_client.upload_file.assert_called_once()

    @patch("src.backup.manager.boto3.client")
    def test_backup_restoration(self, mock_boto3_client):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        backup_manager = manager.BackupManager(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            s3_bucket="test_bucket",
        )
        with patch("src.backup.manager.shutil.unpack_archive"):
            with patch("src.backup.manager.os.remove"):
                backup_manager.restore_backup("test_backup.tar.gz", "/tmp/restore_data")
                mock_s3_client.download_file.assert_called_once()


if __name__ == "__main__":
    unittest.main()
