import uuid
import boto3
from botocore.client import Config
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import UploadedFile
from .serializers import UploadedFileSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_presigned_post(request):
    """
    Client sends JSON: { "filename": "myvideo.mp4", "content_type": "video/mp4", "max_file_size": 104857600 }
    Response: { url, fields, key }
    """
    filename = request.data.get('filename')
    content_type = request.data.get('content_type', '')
    max_size = int(request.data.get('max_file_size', 1024 * 1024 * 1024)) 

    if not filename:
        return Response({"detail": "filename is required"}, status=status.HTTP_400_BAD_REQUEST)


    unique_name = f"{uuid.uuid4().hex}_{filename}"
    key = f"uploads/{request.user.id}/{unique_name}"

    s3_client = boto3.client(
        's3',
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version='s3v4')
    )

    conditions = [
        ["content-length-range", 1, max_size],
    ]
    fields = {}
    if content_type:

        fields['Content-Type'] = content_type

    presigned_post = s3_client.generate_presigned_post(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=3600  # 1 hour
    )

    return Response({
        'url': presigned_post['url'],
        'fields': presigned_post['fields'],
        'key': key
    })


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import UploadedFile
from .serializers import UploadedFileSerializer
import boto3
import mimetypes

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_upload(request):
    """
    Confirm uploaded file metadata after uploading to S3.
    Client JSON example:
    {
      "key": "uploads/2/uuid_filename.jpg",
      "filename": "cartoon.jpg",
      "content_type": "image/jpeg",
      "size": 12345
    }
    """
    key = request.data.get('key')
    filename = request.data.get('filename')
    content_type = request.data.get('content_type', '')
    size = request.data.get('size')

    if not key or not filename:
        return Response({"detail": "key and filename required"}, status=status.HTTP_400_BAD_REQUEST)

    if hasattr(filename, 'name'):
        filename = filename.name

    if not content_type:
        try:
            content_type = mimetypes.guess_type(str(filename))[0] or ''
        except Exception as e:
            print("MIME guess error:", e)
            content_type = 'application/octet-stream'

  
    try:
        size = int(size) if size is not None else 0
    except ValueError:
        size = 0

    actual_size = None
    try:
        s3 = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        metadata = s3.head_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
        actual_size = metadata.get('ContentLength')
    except Exception as e:
        print("⚠️ S3 head_object error:", e)

    final_size = actual_size if actual_size is not None else size or 0

    uploaded = UploadedFile.objects.create(
        uploader=request.user,
        s3_key=key,
        filename=filename,
        content_type=content_type,
        size=final_size
    )

    try:
        uploaded.file.name = key
        uploaded.save(update_fields=['file'])
    except Exception as e:
        print("File assign error:", e)

    serializer = UploadedFileSerializer(uploaded, context={'request': request})
    return Response(serializer.data, status=status.HTTP_201_CREATED)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_presigned_download(request):
    """
    Generate a temporary presigned URL for downloading from S3.
    Example:
    GET /chatbot/download/?key=uploads/2/your_file.jpg
    """
    key = request.query_params.get('key')


    if not key or key.strip() == "":
        return Response(
            {"detail": "Missing 'key' parameter. Example: /chatbot/download/?key=uploads/2/your_file.jpg"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        s3 = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': key},
            ExpiresIn=3600
        )

        return Response({'url': url})

    except Exception as e:
        print("⚠️ Presigned download error:", e)
        return Response(
            {"detail": f"Failed to generate presigned URL: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )