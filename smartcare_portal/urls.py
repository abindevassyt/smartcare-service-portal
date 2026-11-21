"""
URL configuration for smartcare_portal project.
SmartCare Service Portal (MCSP-232)
Author: Abin Devassy Tharayil (Enrolment No: 2550779223)
Guide: Anchitha G Babu - IGNOU MCA 2026
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from services import views as services_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('services/', include('services.urls')),
    path('invoice/<int:invoice_id>/print/', services_views.print_service_invoice, name='root_print_service_invoice'),
]

# Custom HTTP Error Handlers
handler403 = 'accounts.views.custom_403_view'
handler404 = 'accounts.views.custom_404_view'

# Development media and static file serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


