# gatepass_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse 

def devtools_json_silencer(request):
    return HttpResponse("", content_type="application/json", status=200)

urlpatterns = [
    path('.well-known/appspecific/com.chrome.devtools.json', devtools_json_silencer),

    path('admin/', admin.site.urls),
    path('', include('gatepass_app.urls')), # This line should exist as per your setup
]