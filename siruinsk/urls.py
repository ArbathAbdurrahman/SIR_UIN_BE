from django.contrib import admin
from django.urls import path, include
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf.urls.static import static
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from utils.permissions import IsSwaggerAllowed
from django.views.generic import TemplateView

schema_view = get_schema_view(
    openapi.Info(
        title="Teknohole API",
        default_version='v1',
        description="Dokumentasi REST API Teknohole",
        contact=openapi.Contact(email="teknohole@gmail.com"),
    ),
    public=True,
    permission_classes=[IsSwaggerAllowed],
    authentication_classes=[SessionAuthentication],
)

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('admin/', admin.site.urls),
    path('api/login', LoginView.as_view(), name='login'),
    path('api/logout', LogoutView.as_view(), name='logout'),
    path('api/register', RegistrationView.as_view(), name='register'),
    path('api/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/reset-password', ResetPasswordView.as_view(), name='reset_password'),
    path('api/', include('ruang.urls')),
    path('api/profile/', include('profil.urls')),

    # Dokumentasi Swagger & Redoc
    path('api/doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

