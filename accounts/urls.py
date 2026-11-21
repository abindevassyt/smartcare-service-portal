from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth & Landing
    path('', views.login_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_consumer, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('api/districts/<int:statid>/', views.districts_api, name='districts_api'),

    # Role Dashboards
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('tech-dashboard/', views.tech_dashboard_view, name='tech_dashboard'),
    path('consumer-dashboard/', views.consumer_dashboard_view, name='consumer_dashboard'),

    # Admin Management
    path('manage/states/', views.manage_states, name='manage_states'),
    path('manage/states/edit/<int:statid>/', views.edit_state, name='edit_state'),
    path('manage/states/delete/<int:statid>/', views.delete_state, name='delete_state'),

    path('manage/districts/', views.manage_districts, name='manage_districts'),
    path('manage/districts/edit/<int:Distid>/', views.edit_district, name='edit_district'),
    path('manage/districts/delete/<int:Distid>/', views.delete_district, name='delete_district'),

    path('manage/service-centers/', views.manage_service_centers, name='manage_service_centers'),
    path('manage/service-centers/edit/<int:serv_centid>/', views.edit_service_center, name='edit_service_center'),
    path('manage/service-centers/delete/<int:serv_centid>/', views.delete_service_center, name='delete_service_center'),

    path('manage/technicians/', views.manage_technicians, name='manage_technicians'),
    path('manage/technicians/edit/<int:techid>/', views.edit_technician, name='edit_technician'),
    path('manage/technicians/delete/<int:techid>/', views.delete_technician, name='delete_technician'),

    path('admin/consumers/', views.admin_consumers, name='admin_consumers'),
    path('admin/consumers/toggle/<int:consumer_id>/', views.admin_consumer_toggle_status, name='admin_consumer_toggle_status'),

    # Tech Operations
    path('tech/activate-consumers/', views.tech_activate_consumers, name='tech_activate_consumers'),
    path('tech/activate-consumers/toggle/<int:consumer_id>/', views.tech_activate_consumer_toggle, name='tech_activate_consumer_toggle'),
    path('tech/service-centers/', views.tech_service_centers, name='tech_service_centers'),
    path('tech/technicians/', views.tech_technicians, name='tech_technicians'),

    # Consumer Stubs
    path('consumer/profile/', views.consumer_profile, name='consumer_profile'),
    path('consumer/service-centers/', views.consumer_service_centers, name='consumer_service_centers'),
]

