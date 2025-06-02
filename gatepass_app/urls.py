# gatepass_app/urls.py
from django.urls import path, re_path # Import re_path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home_screen, name='home_screen'),
    path('mark_out/', views.mark_out_screen, name='mark_out_screen'),
    path('mark_in/', views.mark_in_screen, name='mark_in_screen'),

    # CHANGE THIS LINE: Use re_path for custom regex that includes slashes
    # r'mark_out/(?P<gatepass_no>.+)/' will match anything for gatepass_no until the next slash or end
    # Use re_path if you want to explicitly allow '/' in the parameter
    re_path(r'mark_out/(?P<gatepass_no>.+)/$', views.process_mark_out, name='process_mark_out'),
    
    re_path(r'mark_in/(?P<gatepass_no>.+)/$', views.process_mark_in, name='process_mark_in'), # Also change this for consistency
    
    path('api/get_employee_details/<str:emp_code>/', views.get_employee_details, name='get_employee_details_api'),

    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='gatepass_app/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]