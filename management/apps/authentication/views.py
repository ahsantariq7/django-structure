
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.shortcuts import render

# Create your views here.


@extend_schema(
    tags=["authentication"],
    summary="Test API endpoint for authentication",
    description="This is a test API endpoint for the authentication app",
    responses={200: {'type': 'object', 'properties': {'app': {'type': 'string'}, 'status': {'type': 'string'}, 'message': {'type': 'string'}}}}
)
@api_view(['GET'])
def api_test_view(request):
    data = {
        "app": "authentication",
        "status": "ok",
        "message": "This is a test API endpoint for the authentication app."
    }
    return Response(data)

def index_view(request):
    """Index view for authentication app."""
    context = {
        "app_name": "authentication",
        "message": "Welcome to the authentication app."
    }
    return render(request, "base.html", context)

def test_view(request):
    """Test view for authentication app."""
    context = {
        "app_name": "authentication",
        "message": "This is a test view for the authentication app."
    }
    return render(request, "base.html", context)
