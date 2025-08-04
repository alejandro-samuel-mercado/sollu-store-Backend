from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.db import transaction
from django.shortcuts import get_object_or_404
import json
import mercadopago
import paypalrestsdk
import logging
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
import os
from django.db.models import Count, Sum
from django.utils import timezone
from productos.permissions import SoloLecturaUsuario

logger = logging.getLogger(__name__)

# Configuración de PayPal
paypalrestsdk.configure({
    "mode": "live",
    "client_id": os.getenv('PAYPAL_CLIENT_ID'),
    "client_secret": os.getenv('PAYPAL_CLIENT_SECRET')
})

# Configuración de Mercado Pago
sdk = mercadopago.SDK(os.getenv('KEY_MP'))