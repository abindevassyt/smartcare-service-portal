from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product Categories
    path('manage/categories/', views.manage_categories, name='manage_categories'),
    path('manage/categories/edit/<int:pcatid>/', views.edit_category, name='edit_category'),
    path('manage/categories/delete/<int:pcatid>/', views.delete_category, name='delete_category'),

    # Products
    path('manage/products/', views.manage_products, name='manage_products'),
    path('manage/products/edit/<int:prid>/', views.edit_product, name='edit_product'),
    path('manage/products/delete/<int:prid>/', views.delete_product, name='delete_product'),

    # Spare Parts
    path('manage/spare-parts/', views.manage_spare_parts, name='manage_spare_parts'),
    path('manage/spare-parts/edit/<int:spareid>/', views.edit_spare_part, name='edit_spare_part'),
    path('manage/spare-parts/delete/<int:spareid>/', views.delete_spare_part, name='delete_spare_part'),

    # Catalogs
    path('tech/products/', views.tech_products, name='tech_products'),
    path('tech/spare-parts/', views.tech_spare_parts, name='tech_spare_parts'),
    path('consumer/catalog/', views.consumer_catalog, name='consumer_catalog'),
]
