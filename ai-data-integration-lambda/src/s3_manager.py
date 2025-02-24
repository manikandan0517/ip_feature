import boto3
import os
import logging
from botocore.exceptions import ClientError
import time
import botocore


class S3Manager:
    def __init__(self, bucket_name, secret_key, access_key, s3_region):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=s3_region
        )
        self.bucket_name = bucket_name
    
    def download_file(self, key: str) -> str:
        local_path = f"/tmp/{os.path.basename(key)}"
        max_retries = 3
        delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                with open(local_path, "wb") as f:
                    self.s3_client.download_fileobj(self.bucket_name, key, f)
                return local_path  # Success, return the file path

            except ClientError as e:
                error_code = e.response["Error"].get("Code", "")
                if error_code == "403":
                    print(f"Permission error (403) downloading file {key} from S3: {e}")
                    raise  # No retry for permission errors

                print(f"Attempt {attempt}: Error downloading file {key} from S3: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    raise  # Exhausted retries, re-raise the exception

            except botocore.exceptions.BotoCoreError as e:
                print(f"Attempt {attempt}: Network error or unknown error: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    raise  # Exhausted retries, re-raise the exception

    def upload_file(self, file_content: str, s3_key: str) -> str:
        max_retries = 3
        delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                self.s3_client.put_object(Body=file_content, Bucket=self.bucket_name, Key=s3_key)
                return f"s3://{self.bucket_name}/{s3_key}"  # Success

            except ClientError as e:
                error_code = e.response["Error"].get("Code", "")
                if error_code == "403":
                    print(f"Permission error (403) uploading file {s3_key} to S3: {e}")
                    raise  # No retry for permission errors

                print(f"Attempt {attempt}: Error uploading file {s3_key} to S3: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    raise  # Exhausted retries, re-raise the exception

            except botocore.exceptions.BotoCoreError as e:
                print(f"Attempt {attempt}: Network error or unknown error: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    raise  # Exhausted retries, re-raise the exception
