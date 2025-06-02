# gatepass_project/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gatepass_app.urls')), # Include app-specific URLs
]