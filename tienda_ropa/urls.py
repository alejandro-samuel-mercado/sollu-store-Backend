from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('productos.urls')),  # Incluye las rutas de la app "productos"
    #path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
