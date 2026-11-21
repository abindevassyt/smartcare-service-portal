from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import admin_required, tech_required, consumer_required
from .models import ProductCat, Product, SparePart


# ==============================================================================
# PRODUCT CATEGORIES CRUD
# ==============================================================================

@admin_required
def manage_categories(request):
    if request.method == 'POST':
        cat_name = request.POST.get('category', '').strip()
        if not cat_name:
            messages.error(request, 'Category name cannot be empty.')
        elif ProductCat.objects.filter(category__iexact=cat_name).exists():
            messages.error(request, f'Category "{cat_name}" already exists.')
        else:
            ProductCat.objects.create(category=cat_name)
            messages.success(request, f'Category "{cat_name}" added successfully.')
        return redirect('products:manage_categories')

    q = request.GET.get('q', '').strip()
    categories = ProductCat.objects.all().order_by('category')
    if q:
        categories = categories.filter(category__icontains=q)

    return render(request, 'products/manage_categories.html', {
        'categories': categories,
        'query': q
    })


@admin_required
def edit_category(request, pcatid):
    cat = get_object_or_404(ProductCat, pcatid=pcatid)
    if request.method == 'POST':
        new_name = request.POST.get('category', '').strip()
        if not new_name:
            messages.error(request, 'Category name cannot be empty.')
        else:
            cat.category = new_name
            cat.save()
            messages.success(request, f'Category updated to "{new_name}".')
            return redirect('products:manage_categories')
    return render(request, 'products/edit_category.html', {'category': cat})


@admin_required
def delete_category(request, pcatid):
    cat = get_object_or_404(ProductCat, pcatid=pcatid)
    if request.method == 'POST':
        try:
            name = cat.category
            cat.delete()
            messages.success(request, f'Category "{name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Cannot delete category: Associated products exist. ({str(e)})')
    return redirect('products:manage_categories')


# ==============================================================================
# PRODUCTS CRUD
# ==============================================================================

@admin_required
def manage_products(request):
    categories = ProductCat.objects.all().order_by('category')

    if request.method == 'POST':
        pcatid = request.POST.get('pcatid', '').strip()
        prname = request.POST.get('prname', '').strip()
        model = request.POST.get('model', '').strip()
        price = request.POST.get('price', '').strip()
        srno = request.POST.get('srno', '').strip()
        des = request.POST.get('des', '').strip()
        img = request.FILES.get('img')

        if not (pcatid and prname and model and price and srno and des):
            messages.error(request, 'Please fill in all mandatory product fields.')
        elif Product.objects.filter(srno=srno).exists():
            messages.error(request, f'Product with Serial Number "{srno}" already exists.')
        else:
            cat_obj = get_object_or_404(ProductCat, pcatid=pcatid)
            Product.objects.create(
                pcatid=cat_obj,
                prname=prname,
                model=model,
                price=float(price),
                srno=srno,
                img=img,
                des=des
            )
            messages.success(request, f'Product "{prname}" ({model}) added to catalog.')
            return redirect('products:manage_products')

    q = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('cat', '').strip()
    products = Product.objects.select_related('pcatid').all().order_by('-prid')

    if cat_filter:
        products = products.filter(pcatid_id=cat_filter)
    if q:
        products = products.filter(prname__icontains=q) | products.filter(model__icontains=q) | products.filter(srno__icontains=q)

    return render(request, 'products/manage_products.html', {
        'products': products,
        'categories': categories,
        'query': q,
        'cat_filter': cat_filter
    })


@admin_required
def edit_product(request, prid):
    product = get_object_or_404(Product, prid=prid)
    categories = ProductCat.objects.all().order_by('category')

    if request.method == 'POST':
        pcatid = request.POST.get('pcatid', '').strip()
        product.prname = request.POST.get('prname', '').strip()
        product.model = request.POST.get('model', '').strip()
        product.price = float(request.POST.get('price', product.price))
        product.srno = request.POST.get('srno', '').strip()
        product.des = request.POST.get('des', '').strip()

        if request.FILES.get('img'):
            product.img = request.FILES.get('img')

        if pcatid:
            product.pcatid = get_object_or_404(ProductCat, pcatid=pcatid)

        product.save()
        messages.success(request, f'Product "{product.prname}" updated successfully.')
        return redirect('products:manage_products')

    return render(request, 'products/edit_product.html', {
        'product': product,
        'categories': categories
    })


@admin_required
def delete_product(request, prid):
    product = get_object_or_404(Product, prid=prid)
    if request.method == 'POST':
        try:
            name = product.prname
            product.delete()
            messages.success(request, f'Product "{name}" removed from catalog.')
        except Exception as e:
            messages.error(request, f'Cannot delete product: Associated consumer registrations or spare parts exist. ({str(e)})')
    return redirect('products:manage_products')


# ==============================================================================
# SPARE PARTS CRUD
# ==============================================================================

@admin_required
def manage_spare_parts(request):
    products = Product.objects.all().order_by('prname')

    if request.method == 'POST':
        prid = request.POST.get('prid', '').strip()
        partsname = request.POST.get('partsname', '').strip()
        price = request.POST.get('price', '').strip()
        qty = request.POST.get('qty', '0').strip()

        if not (prid and partsname and price):
            messages.error(request, 'Please complete all required fields.')
        else:
            prod_obj = get_object_or_404(Product, prid=prid)
            SparePart.objects.create(
                prid=prod_obj,
                partsname=partsname,
                price=float(price),
                qty=int(qty or 0)
            )
            messages.success(request, f'Spare part "{partsname}" added with quantity {qty}.')
            return redirect('products:manage_spare_parts')

    q = request.GET.get('q', '').strip()
    prod_filter = request.GET.get('prid', '').strip()
    spare_parts = SparePart.objects.select_related('prid').all().order_by('-spareid')

    if prod_filter:
        spare_parts = spare_parts.filter(prid_id=prod_filter)
    if q:
        spare_parts = spare_parts.filter(partsname__icontains=q)

    return render(request, 'products/manage_spare_parts.html', {
        'spare_parts': spare_parts,
        'products': products,
        'query': q,
        'prod_filter': prod_filter
    })


@admin_required
def edit_spare_part(request, spareid):
    spare = get_object_or_404(SparePart, spareid=spareid)
    products = Product.objects.all().order_by('prname')

    if request.method == 'POST':
        prid = request.POST.get('prid', '').strip()
        spare.partsname = request.POST.get('partsname', '').strip()
        spare.price = float(request.POST.get('price', spare.price))
        spare.qty = int(request.POST.get('qty', spare.qty))

        if prid:
            spare.prid = get_object_or_404(Product, prid=prid)

        spare.save()
        messages.success(request, f'Spare part "{spare.partsname}" updated successfully.')
        return redirect('products:manage_spare_parts')

    return render(request, 'products/edit_spare_part.html', {
        'spare': spare,
        'products': products
    })


@admin_required
def delete_spare_part(request, spareid):
    spare = get_object_or_404(SparePart, spareid=spareid)
    if request.method == 'POST':
        try:
            name = spare.partsname
            spare.delete()
            messages.success(request, f'Spare part "{name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Cannot delete spare part: Associated service records exist. ({str(e)})')
    return redirect('products:manage_spare_parts')


# ==============================================================================
# TECHNICIAN & CONSUMER READ-ONLY CATALOG VIEWS
# ==============================================================================

@tech_required
def tech_products(request):
    q = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('cat', '').strip()

    products = Product.objects.select_related('pcatid').all().order_by('prname')
    categories = ProductCat.objects.all().order_by('category')

    if cat_filter:
        products = products.filter(pcatid_id=cat_filter)
    if q:
        products = products.filter(prname__icontains=q) | products.filter(model__icontains=q) | products.filter(srno__icontains=q)

    return render(request, 'products/tech_products.html', {
        'products': products,
        'categories': categories,
        'query': q,
        'cat_filter': cat_filter
    })


@tech_required
def tech_spare_parts(request):
    q = request.GET.get('q', '').strip()
    prod_filter = request.GET.get('prod', '').strip()

    spare_parts = SparePart.objects.select_related('prid').all().order_by('partsname')
    products = Product.objects.all().order_by('prname')

    if prod_filter:
        spare_parts = spare_parts.filter(prid_id=prod_filter)
    if q:
        spare_parts = spare_parts.filter(partsname__icontains=q)

    return render(request, 'products/tech_spare_parts.html', {
        'spare_parts': spare_parts,
        'products': products,
        'query': q,
        'prod_filter': prod_filter
    })


def consumer_catalog(request):
    products = Product.objects.select_related('pcatid').all().order_by('prname')
    categories = ProductCat.objects.all().order_by('category')
    return render(request, 'products/consumer_catalog.html', {
        'products': products,
        'categories': categories
    })
