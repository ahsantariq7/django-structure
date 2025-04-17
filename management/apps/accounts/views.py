from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render

# Create your views here.

def index_view(request):
    """Index view for authentication app."""
    data = {
        "app": "authentication",
        "status": "ok",
        "message": "Welcome to the authentication API."
    }
    return JsonResponse(data)

def test_view(request):
    """Test view for authentication app."""
    context = {
        "app_name": "authentication",
        "message": "This is a test view for the authentication app."
    }
    return render(request, "base.html", context)

def api_test_view(request):
    """API test view for authentication app."""
    data = {
        "app": "authentication",
        "status": "ok",
        "message": "This is a test API endpoint for the authentication app."
    }
    return JsonResponse(data)
