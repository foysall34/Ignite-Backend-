# chatbot_api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

# Import your LOGIC function from your logic file
from .chatbot_logic import chatbot

# The CSRF decorator belongs HERE, on the View class
@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(APIView):
    def post(self, request, *args, **kwargs):
        query = request.data.get('query')

        if not query:
            return Response({"error": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # The View calls the Logic
            response_data = chatbot(query)
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"An error occurred: {e}")
            return Response({"error": "An internal server error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)