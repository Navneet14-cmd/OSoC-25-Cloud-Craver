
import os
import shutil
import tempfile
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import NoCredentialsError
from rich.console import Console

console = Console()


class BackupManager:
    """
    Manages the backup and restoration of application data.
    """

    def __init__(
        self,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        s3_bucket: str = None,
    ):
        self.aws_access_key_id = aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.environ.get(
            "AWS_SECRET_ACCESS_KEY"
        )
        self.s3_bucket = s3_bucket or os.environ.get("S3_BUCKET")

        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.s3_bucket]):
            raise ValueError(
                "AWS credentials and S3 bucket must be provided "
                "either as arguments or environment variables."
            )

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    def create_backup(self, data_path: str) -> Optional[str]:
        """
        Creates a backup of the application data and uploads it to S3.
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.gz") as tmpfile:
            backup_file = shutil.make_archive(
                base_name=tmpfile.name.replace(".tar.gz", ""),
                format="gztar",
                root_dir=data_path,
            )

            try:
                backup_key = f"backups/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.tar.gz"
                self.s3_client.upload_file(backup_file, self.s3_bucket, backup_key)
                console.print(f"[green]Successfully created and uploaded backup to s3://{self.s3_bucket}/{backup_key}[/green]")
                return backup_key
            except NoCredentialsError:
                console.print("[red]Error: AWS credentials not found.[/red]")
                return None
            except Exception as e:
                console.print(f"[red]Failed to upload backup to S3: {e}[/red]")
                return None
            finally:
                os.remove(backup_file)

    def restore_backup(self, backup_key: str, restore_path: str):
        """
        Restores a backup from S3 to the application data directory.
        """
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            try:
                self.s3_client.download_file(self.s3_bucket, backup_key, tmpfile.name)
                shutil.unpack_archive(tmpfile.name, restore_path, format="gztar")
                console.print(f"[green]Successfully restored backup from s3://{self.s3_bucket}/{backup_key} to {restore_path}[/green]")
            except Exception as e:
                console.print(f"[red]Failed to restore backup from S3: {e}[/red]")
            finally:
                os.remove(tmpfile.name)
