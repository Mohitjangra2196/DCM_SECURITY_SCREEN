# gatepass_app/urls.py
from django.urls import path, re_path, include # Import include
from . import views
from django.contrib.auth import views as auth_views

# DRF Imports
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'security-guards', views.SecurityGuardViewSet)
router.register(r'gatepasses', views.GatePassViewSet)


urlpatterns = [
    # Existing HTML-rendering URLs
    path('', views.home_screen, name='home_screen'),
    path('mark_out/', views.mark_out_screen, name='mark_out_screen'),
    path('mark_in/', views.mark_in_screen, name='mark_in_screen'),

    re_path(r'mark_out/(?P<gatepass_no>.+)/$', views.process_mark_out, name='process_mark_out'),
    re_path(r'mark_in/(?P<gatepass_no>.+)/$', views.process_mark_in, name='process_mark_in'),
    
    # Old get_employee_details API (can be removed if replaced by DRF version)
    # path('api/get_employee_details/<str:emp_code>/', views.get_employee_details, name='get_employee_details_api'),

    # New DRF API Endpoints
    path('api/', include(router.urls)), # Includes URLs for SecurityGuardViewSet and GatePassViewSet
    path('api/employee-details/<str:emp_code>/', views.api_get_employee_details, name='api_employee_details'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), # For DRF browsable API login/logout

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='gatepass_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]