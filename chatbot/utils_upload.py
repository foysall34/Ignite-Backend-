import uuid
import boto3
import os
from django.conf import settings

def upload_to_s3(file_obj):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    original_name = os.path.splitext(file_obj.name)[0]
    file_extension = os.path.splitext(file_obj.name)[1]
    file_key = f"uploads/{uuid.uuid4()}_{original_name}{file_extension}"

    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_key,
        ExtraArgs={
            "ContentType": file_obj.content_type,
            "ACL": "private",
        },
    )

    # we return key (not public url). signed URL can be generated later if needed.
    return file_key
