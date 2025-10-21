import json
import requests
import os
from dotenv import load_dotenv
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.forms.models import model_to_dict
from . import models

#* FILE WITH CALENDAR FUNCTIONS

@csrf_exempt
def get_user_api(request, user_id):
    """HTTP API view that returns the user's bookings as JSON.

    Accepts GET and returns a JSON object: {"bookings": [ ... ]}.
    Each booking is serialized with django.forms.models.model_to_dict().
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed, use GET'}, status=405)

    # Load the single user or return 404 if it doesn't exist.
    user = get_object_or_404(models.User, id=user_id)

    # Convert the model instance to a dict. This produces simple serializable data
    # (FKs become id values). Adjust fields if you need nested data.
    data = model_to_dict(user)

    return JsonResponse({'user': data})