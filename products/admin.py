from django.contrib import admin
from .models import ProductCat, Product, SparePart


@admin.register(ProductCat)
class ProductCatAdmin(admin.ModelAdmin):
    list_display = ('pcatid', 'category')
    search_fields = ('category',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('prid', 'prname', 'model', 'price', 'srno', 'pcatid')
    list_filter = ('pcatid',)
    search_fields = ('prname', 'model', 'srno')


@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ('spareid', 'partsname', 'prid', 'price', 'qty')
    list_filter = ('prid',)
    search_fields = ('partsname',)

