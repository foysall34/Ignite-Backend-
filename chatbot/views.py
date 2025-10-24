from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser

from .models import UploadFile
from .serializers import UploadFileSerializer


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_file_view(request):
    # 🔹 POST request: file upload
    if request.method == 'POST':
        serializer = UploadFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "File uploaded successfully!",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 🔹 GET request: list all uploaded files
    elif request.method == 'GET':
        files = UploadFile.objects.all().order_by('-uploaded_at')
        serializer = UploadFileSerializer(files, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
