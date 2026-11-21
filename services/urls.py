from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Statuses
    path('manage/statuses/', views.manage_statuses, name='manage_statuses'),
    path('manage/statuses/edit/<int:Wo_stid>/', views.edit_status, name='edit_status'),
    path('manage/statuses/delete/<int:Wo_stid>/', views.delete_status, name='delete_status'),

    # Admin Operations
    path('admin/consumer-products/', views.admin_consumer_products, name='admin_consumer_products'),
    path('admin/consumer-products/toggle/<int:reg_id>/', views.admin_toggle_product_activation, name='admin_toggle_product_activation'),
    path('admin/work-orders/', views.admin_work_orders, name='admin_work_orders'),
    path('admin/work-orders/assign/<int:w_orderid>/', views.admin_assign_work_order, name='admin_assign_work_order'),
    path('admin/work-orders/<int:w_orderid>/details/', views.admin_work_order_details, name='admin_work_order_details'),
    path('admin/complaints/', views.admin_complaints, name='admin_complaints'),
    path('admin/complaints/reply/<int:com_id>/', views.admin_reply_complaint, name='admin_reply_complaint'),
    path('admin/reports/', views.admin_reports, name='admin_reports'),

    # Tech Queues & Operations
    path('tech/activate-products/', views.tech_activate_products, name='tech_activate_products'),
    path('tech/activate-products/toggle/<int:reg_id>/', views.tech_activate_product_toggle, name='tech_activate_product_toggle'),
    path('tech/work-order/<int:w_orderid>/', views.tech_work_order_detail, name='tech_work_order_detail'),
    path('tech/generate-invoice/<int:w_orderid>/', views.tech_generate_invoice, name='tech_generate_invoice'),
    path('invoice/<int:invoice_id>/print/', views.print_service_invoice, name='print_service_invoice'),

    # Consumer Actions
    path('consumer/products/', views.consumer_register_product, name='consumer_register_product'),
    path('consumer/book-service/', views.consumer_book_service, name='consumer_book_service'),
    path('consumer/track-orders/', views.consumer_track_orders, name='consumer_track_orders'),
    path('consumer/track-order/<int:w_orderid>/', views.consumer_track_order_detail, name='consumer_track_order_detail'),
    path('consumer/work-order/<int:w_orderid>/estimate/', views.consumer_respond_estimate, name='consumer_respond_estimate'),
    path('consumer/history/', views.consumer_history, name='consumer_history'),
    path('consumer/complaints/', views.consumer_complaints, name='consumer_complaints'),
]
