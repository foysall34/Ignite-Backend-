import uuid
import boto3
from django.conf import settings

def upload_to_s3(file_obj):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


    file_extension = file_obj.name.split('.')[-1]
    file_key = f"uploads/{uuid.uuid4()}.{file_extension}"

  
    s3.upload_fileobj(
        Fileobj=file_obj,
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=file_key,
        ExtraArgs={
            "ContentType": file_obj.content_type,
            "ACL": "private", 
        },
    )


    presigned_url = s3.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Key': file_key,
        },
        ExpiresIn=3600,  # valid for 1 hour
    )

    return {
        "key": file_key,
        "url": presigned_url
    }
