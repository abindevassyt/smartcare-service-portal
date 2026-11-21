from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.db import transaction

from .models import AuthUser, ConsumerReg, State, District, Technician, ServCenter
from .decorators import login_required_custom, admin_required, tech_required, consumer_required


def login_view(request):
    # If user is already logged in, redirect to respective dashboard
    if request.session.get('username') and request.session.get('role'):
        role = request.session.get('role')
        if role == 'Admin':
            return redirect('accounts:admin_dashboard')
        elif role == 'Technician':
            return redirect('accounts:tech_dashboard')
        elif role == 'Consumer':
            return redirect('accounts:consumer_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'accounts/login.html')

        auth_user = (
            AuthUser.objects.filter(username__iexact=username).first() or
            (AuthUser.objects.filter(username__iexact=username.split('@')[0]).first() if '@' in username else None) or
            (AuthUser.objects.filter(username__istartswith=username + '@').first() if '@' not in username else None)
        )

        if auth_user:
            # Check hashed password first, fallback to plain for compatibility
            password_valid = check_password(password, auth_user.password) or (auth_user.password == password)
            if password_valid:
                session_user = auth_user.username
                if auth_user.role == 'Consumer':
                    c = ConsumerReg.objects.filter(email__iexact=auth_user.username).first() or ConsumerReg.objects.filter(email__istartswith=auth_user.username + '@').first()
                    if c:
                        session_user = c.email
                elif auth_user.role == 'Technician':
                    t = Technician.objects.filter(Email__iexact=auth_user.username).first() or Technician.objects.filter(Email__istartswith=auth_user.username + '@').first()
                    if t:
                        session_user = t.Email

                request.session['username'] = session_user
                request.session['role'] = auth_user.role

                messages.success(request, f'Welcome back, {session_user}! Logged in as {auth_user.role}.')

                if auth_user.role == 'Admin':
                    return redirect('accounts:admin_dashboard')
                elif auth_user.role == 'Technician':
                    return redirect('accounts:tech_dashboard')
                elif auth_user.role == 'Consumer':
                    return redirect('accounts:consumer_dashboard')
                else:
                    return redirect('accounts:login')
            else:
                messages.error(request, 'Invalid password. Please check your credentials and try again.')
        else:
            messages.error(request, 'User does not exist with the given username or email.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'You have been successfully logged out.')
    return redirect('accounts:login')


def register_consumer(request):
    states = State.objects.all().order_by('state')

    if request.method == 'POST':
        fname = request.POST.get('fname', '').strip()
        lname = request.POST.get('lname', '').strip()
        dob = request.POST.get('dob', '').strip()
        address = request.POST.get('address', '').strip()
        statid = request.POST.get('statid', '').strip()
        Distid = request.POST.get('Distid', '').strip()
        phone = request.POST.get('phone', '').strip()
        mob = request.POST.get('mob', '').strip()
        pin = request.POST.get('pin', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        remarks = request.POST.get('remarks', '').strip()
        consumertype = request.POST.get('consumertype', 'Regular').strip()

        # Validation
        if not (fname and lname and dob and address and statid and Distid and mob and email and password):
            messages.error(request, 'Please fill in all mandatory fields.')
            return render(request, 'accounts/register.html', {'states': states, 'form_data': request.POST})

        if password != confirm_password:
            messages.error(request, 'Passwords do not match. Please verify.')
            return render(request, 'accounts/register.html', {'states': states, 'form_data': request.POST})

        # Check for existing email in AuthUser or ConsumerReg
        if AuthUser.objects.filter(username=email).exists() or ConsumerReg.objects.filter(email=email).exists():
            messages.error(request, f'An account with email "{email}" is already registered. Please sign in or use Forgot Password.')
            return render(request, 'accounts/register.html', {'states': states, 'form_data': request.POST})

        state_obj = get_object_or_404(State, statid=statid)
        dist_obj = get_object_or_404(District, Distid=Distid)

        try:
            with transaction.atomic():
                hashed_pw = make_password(password)

                # 1. Create ConsumerReg record
                consumer = ConsumerReg.objects.create(
                    fname=fname,
                    lname=lname,
                    dob=dob,
                    address=address,
                    statid=state_obj,
                    Distid=dist_obj,
                    regmode='Online',
                    phone=phone or mob,
                    mob=mob,
                    pin=pin,
                    email=email,
                    password=hashed_pw,
                    remarks=remarks or 'Registered via Online Portal',
                    status='Pending',
                    consumertype=consumertype or 'Regular'
                )

                # 2. Create AuthUser record
                AuthUser.objects.create(
                    username=email,
                    password=hashed_pw,
                    role='Consumer'
                )

            messages.success(request, f'Registration successful for {fname} {lname}! Your account is pending technician verification. You can now log in.')
            return redirect('accounts:login')

        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'accounts/register.html', {'states': states, 'form_data': request.POST})

    return render(request, 'accounts/register.html', {'states': states})


def districts_api(request, statid):
    districts = District.objects.filter(statid_id=statid).order_by('District')
    data = [{'id': d.Distid, 'name': d.District} for d in districts]
    return JsonResponse({'districts': data})


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not email or not new_password:
            messages.error(request, 'Please provide registered email and new password.')
            return render(request, 'accounts/forgot_password.html')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/forgot_password.html')

        auth_user = AuthUser.objects.filter(username=email).first()
        if not auth_user:
            messages.error(request, 'No registered user found with that email address.')
            return render(request, 'accounts/forgot_password.html')

        hashed_pw = make_password(new_password)
        auth_user.password = hashed_pw
        auth_user.save()

        # If it was a Consumer, also update ConsumerReg
        consumer = ConsumerReg.objects.filter(email=email).first()
        if consumer:
            consumer.password = hashed_pw
            consumer.save()

        messages.success(request, 'Your password has been successfully reset! Please log in with your new password.')
        return redirect('accounts:login')

    return render(request, 'accounts/forgot_password.html')


# Initial Dashboard Placeholders for Stage 4 (Full modules expanded in Stages 5, 6, 7)
@admin_required
def admin_dashboard_view(request):
    from products.models import Product, SparePart
    from services.models import WorkOrder, ConsProductReg

    context = {
        'total_consumers': ConsumerReg.objects.count(),
        'total_service_centers': ServCenter.objects.filter(status='Active').count(),
        'pending_work_orders': WorkOrder.objects.filter(w_stid__W_status='Pending').count(),
        'total_technicians': Technician.objects.filter(Status='Active').count(),
        'low_stock_parts': SparePart.objects.filter(qty__lt=5).count(),
        'recent_orders': WorkOrder.objects.select_related('techid', 'w_stid', 'reg_id__consumer_id')[:5],
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@tech_required
def tech_dashboard_view(request):
    from services.models import WorkOrder, ConsProductReg
    from django.utils import timezone

    username = request.session.get('username')
    tech = (
        Technician.objects.filter(Email__iexact=username).first() or
        Technician.objects.filter(Mob=username).first() or
        Technician.objects.filter(Email__istartswith=username + '@').first() or
        Technician.objects.filter(Status='Active').first()
    )
    today = timezone.now().date()

    assigned_orders = []
    orders_assigned = []
    orders_in_progress = []
    orders_spare_pending = []
    orders_completed = []
    orders_other = []

    if tech:
        all_orders = WorkOrder.objects.filter(techid=tech).select_related(
            'w_stid', 'reg_id__consumer_id', 'reg_id__prid'
        ).order_by('-W_orderid')

        for o in all_orders:
            # Annotate warranty
            in_warranty = (o.cre_date <= o.reg_id.warnt_enddate) if (o.reg_id and o.reg_id.warnt_enddate) else False
            o.is_warranty_covered = in_warranty
            assigned_orders.append(o)

            st = o.w_stid.W_status if o.w_stid else 'Pending'
            if st == 'Assigned':
                orders_assigned.append(o)
            elif st in ['In Progress', 'In-Progress']:
                orders_in_progress.append(o)
            elif 'Spare' in st:
                orders_spare_pending.append(o)
            elif st == 'Completed':
                orders_completed.append(o)
            else:
                orders_other.append(o)

    active_tickets_count = len(orders_assigned) + len(orders_in_progress) + len(orders_spare_pending)

    context = {
        'technician': tech,
        'assigned_orders': assigned_orders,
        'orders_assigned': orders_assigned,
        'orders_in_progress': orders_in_progress,
        'orders_spare_pending': orders_spare_pending,
        'orders_completed': orders_completed,
        'orders_other': orders_other,
        'active_tickets_count': active_tickets_count,
        'completed_tickets_count': len(orders_completed),
        'pending_consumer_activations': ConsumerReg.objects.filter(status='Pending').count(),
        'pending_product_activations': ConsProductReg.objects.filter(Isactive='Pending').count(),
        'today': today,
    }
    return render(request, 'accounts/tech_dashboard.html', context)



@consumer_required
def consumer_dashboard_view(request):
    from services.models import ConsProductReg, WorkOrder
    from django.utils import timezone
    from datetime import timedelta

    email = request.session.get('username')
    consumer = (
        ConsumerReg.objects.filter(email__iexact=email).first() or
        ConsumerReg.objects.filter(email__istartswith=email + '@').first() or
        ConsumerReg.objects.first()
    )

    registered_appliances = []
    work_orders = []
    today = timezone.now().date()
    expiring_soon_count = 0

    if consumer:
        apps_qs = ConsProductReg.objects.filter(consumer_id=consumer).select_related('prid', 'prid__pcatid').order_by('-Reg_id')
        for a in apps_qs:
            is_valid = (a.warnt_enddate >= today)
            days_left = (a.warnt_enddate - today).days if is_valid else 0
            if is_valid and days_left <= 30:
                expiring_soon_count += 1
            registered_appliances.append({
                'app': a,
                'is_warranty_valid': is_valid,
                'days_left': days_left,
            })

        work_orders = WorkOrder.objects.filter(
            reg_id__consumer_id=consumer
        ).select_related('w_stid', 'techid', 'reg_id__prid').order_by('-W_orderid')

    context = {
        'consumer': consumer,
        'registered_appliances': registered_appliances,
        'work_orders': work_orders,
        'active_tickets_count': len([o for o in work_orders if o.w_stid.W_status != 'Completed']),
        'expiring_soon_count': expiring_soon_count,
        'today': today
    }
    return render(request, 'accounts/consumer_dashboard.html', context)

# ==============================================================================
# ADMINISTRATOR MASTER DATA CRUD VIEWS
# ==============================================================================

@admin_required
def manage_states(request):
    if request.method == 'POST':
        state_name = request.POST.get('state', '').strip()
        if not state_name:
            messages.error(request, 'State name cannot be empty.')
        elif State.objects.filter(state__iexact=state_name).exists():
            messages.error(request, f'State "{state_name}" already exists.')
        else:
            State.objects.create(state=state_name)
            messages.success(request, f'State "{state_name}" created successfully.')
        return redirect('accounts:manage_states')

    q = request.GET.get('q', '').strip()
    states = State.objects.all()
    if q:
        states = states.filter(state__icontains=q)
    return render(request, 'accounts/manage_states.html', {'states': states, 'query': q})


@admin_required
def edit_state(request, statid):
    state_obj = get_object_or_404(State, statid=statid)
    if request.method == 'POST':
        new_name = request.POST.get('state', '').strip()
        if not new_name:
            messages.error(request, 'State name cannot be empty.')
        else:
            state_obj.state = new_name
            state_obj.save()
            messages.success(request, f'State updated to "{new_name}".')
        return redirect('accounts:manage_states')
    return render(request, 'accounts/edit_state.html', {'state': state_obj})


@admin_required
def delete_state(request, statid):
    state_obj = get_object_or_404(State, statid=statid)
    if request.method == 'POST':
        try:
            name = state_obj.state
            state_obj.delete()
            messages.success(request, f'State "{name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Cannot delete state: Dependent districts or records exist. ({str(e)})')
    return redirect('accounts:manage_states')


@admin_required
def manage_districts(request):
    states = State.objects.all().order_by('state')
    if request.method == 'POST':
        dist_name = request.POST.get('District', '').strip()
        statid = request.POST.get('statid', '').strip()
        if not dist_name or not statid:
            messages.error(request, 'District name and State are required.')
        else:
            state_obj = get_object_or_404(State, statid=statid)
            if District.objects.filter(District__iexact=dist_name, statid=state_obj).exists():
                messages.error(request, f'District "{dist_name}" already exists in {state_obj.state}.')
            else:
                District.objects.create(District=dist_name, statid=state_obj)
                messages.success(request, f'District "{dist_name}" added to {state_obj.state}.')
        return redirect('accounts:manage_districts')

    q = request.GET.get('q', '').strip()
    selected_state = request.GET.get('statid', '').strip()
    districts = District.objects.select_related('statid').all()

    if selected_state:
        districts = districts.filter(statid_id=selected_state)
    if q:
        districts = districts.filter(District__icontains=q)

    return render(request, 'accounts/manage_districts.html', {
        'districts': districts,
        'states': states,
        'selected_state': selected_state,
        'query': q
    })


@admin_required
def edit_district(request, Distid):
    district_obj = get_object_or_404(District, Distid=Distid)
    states = State.objects.all().order_by('state')
    if request.method == 'POST':
        dist_name = request.POST.get('District', '').strip()
        statid = request.POST.get('statid', '').strip()
        if not dist_name or not statid:
            messages.error(request, 'District name and State are required.')
        else:
            state_obj = get_object_or_404(State, statid=statid)
            district_obj.District = dist_name
            district_obj.statid = state_obj
            district_obj.save()
            messages.success(request, f'District updated successfully.')
            return redirect('accounts:manage_districts')
    return render(request, 'accounts/edit_district.html', {'district': district_obj, 'states': states})


@admin_required
def delete_district(request, Distid):
    district_obj = get_object_or_404(District, Distid=Distid)
    if request.method == 'POST':
        try:
            name = district_obj.District
            district_obj.delete()
            messages.success(request, f'District "{name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Cannot delete district: Dependent service centers or consumers exist. ({str(e)})')
    return redirect('accounts:manage_districts')


@admin_required
def manage_service_centers(request):
    states = State.objects.all().order_by('state')
    if request.method == 'POST':
        serv_cent = request.POST.get('serv_cent', '').strip()
        statid = request.POST.get('statid', '').strip()
        Distid = request.POST.get('Distid', '').strip()
        place = request.POST.get('place', '').strip()
        pin = request.POST.get('pin', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        Contact_per = request.POST.get('Contact_per', '').strip()
        phone = request.POST.get('phone', '').strip()
        mob = request.POST.get('mob', '').strip()
        email = request.POST.get('email', '').strip()
        username = request.POST.get('username', '').strip()
        pwd = request.POST.get('pwd', '').strip()
        status = request.POST.get('status', 'Active').strip()

        if not (serv_cent and statid and Distid and place and phone and mob and email and username and pwd):
            messages.error(request, 'Please complete all required fields.')
        elif ServCenter.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken by another service center.')
        else:
            state_obj = get_object_or_404(State, statid=statid)
            dist_obj = get_object_or_404(District, Distid=Distid)
            ServCenter.objects.create(
                serv_cent=serv_cent,
                statid=state_obj,
                Distid=dist_obj,
                place=place,
                pin=pin,
                landmark=landmark,
                Contact_per=Contact_per,
                phone=phone,
                mob=mob,
                email=email,
                username=username,
                pwd=make_password(pwd),
                status=status
            )
            messages.success(request, f'Service Center "{serv_cent}" registered successfully.')
            return redirect('accounts:manage_service_centers')

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    centers = ServCenter.objects.select_related('statid', 'Distid').all()

    if q:
        centers = centers.filter(serv_cent__icontains=q)
    if status_filter:
        centers = centers.filter(status=status_filter)

    return render(request, 'accounts/manage_service_centers.html', {
        'centers': centers,
        'states': states,
        'query': q,
        'status_filter': status_filter
    })


@admin_required
def edit_service_center(request, serv_centid):
    center = get_object_or_404(ServCenter, serv_centid=serv_centid)
    states = State.objects.all().order_by('state')
    districts = District.objects.filter(statid=center.statid).order_by('District')

    if request.method == 'POST':
        center.serv_cent = request.POST.get('serv_cent', '').strip()
        statid = request.POST.get('statid', '').strip()
        Distid = request.POST.get('Distid', '').strip()
        center.place = request.POST.get('place', '').strip()
        center.pin = request.POST.get('pin', '').strip()
        center.landmark = request.POST.get('landmark', '').strip()
        center.Contact_per = request.POST.get('Contact_per', '').strip()
        center.phone = request.POST.get('phone', '').strip()
        center.mob = request.POST.get('mob', '').strip()
        center.email = request.POST.get('email', '').strip()
        center.status = request.POST.get('status', 'Active').strip()

        pwd = request.POST.get('pwd', '').strip()
        if pwd:
            center.pwd = make_password(pwd)

        if statid and Distid:
            center.statid = get_object_or_404(State, statid=statid)
            center.Distid = get_object_or_404(District, Distid=Distid)

        center.save()
        messages.success(request, f'Service Center "{center.serv_cent}" updated successfully.')
        return redirect('accounts:manage_service_centers')

    return render(request, 'accounts/edit_service_center.html', {
        'center': center,
        'states': states,
        'districts': districts
    })


@admin_required
def delete_service_center(request, serv_centid):
    center = get_object_or_404(ServCenter, serv_centid=serv_centid)
    if request.method == 'POST':
        name = center.serv_cent
        center.delete()
        messages.success(request, f'Service Center "{name}" deleted successfully.')
    return redirect('accounts:manage_service_centers')


@admin_required
def manage_technicians(request):
    states = State.objects.all().order_by('state')
    if request.method == 'POST':
        tech_name = request.POST.get('tech_name', '').strip()
        Address = request.POST.get('Address', '').strip()
        statid = request.POST.get('statid', '').strip()
        Distid = request.POST.get('Distid', '').strip()
        Gender = request.POST.get('Gender', 'Male').strip()
        Quali = request.POST.get('Quali', '').strip()
        Exp = request.POST.get('Exp', '').strip()
        Mob = request.POST.get('Mob', '').strip()
        Email = request.POST.get('Email', '').strip().lower()
        Status = request.POST.get('Status', 'Active').strip()
        pwd = request.POST.get('password', '').strip() or 'tech123'

        if not (tech_name and Address and statid and Distid and Mob and Email):
            messages.error(request, 'Please provide all required technician details.')
        elif Technician.objects.filter(Email=Email).exists() or AuthUser.objects.filter(username=Email).exists():
            messages.error(request, f'Technician with email "{Email}" already exists.')
        else:
            state_obj = get_object_or_404(State, statid=statid)
            dist_obj = get_object_or_404(District, Distid=Distid)

            with transaction.atomic():
                tech = Technician.objects.create(
                    tech_name=tech_name,
                    Address=Address,
                    statid=state_obj,
                    Distid=dist_obj,
                    Gender=Gender,
                    Quali=Quali,
                    Exp=Exp,
                    Mob=Mob,
                    Email=Email,
                    Status=Status
                )
                AuthUser.objects.create(
                    username=Email,
                    password=make_password(pwd),
                    role='Technician'
                )

            messages.success(request, f'Technician "{tech_name}" registered successfully with login username "{Email}".')
            return redirect('accounts:manage_technicians')

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    technicians = Technician.objects.select_related('statid', 'Distid').all()

    if q:
        technicians = technicians.filter(tech_name__icontains=q)
    if status_filter:
        technicians = technicians.filter(Status=status_filter)

    return render(request, 'accounts/manage_technicians.html', {
        'technicians': technicians,
        'states': states,
        'query': q,
        'status_filter': status_filter
    })


@admin_required
def edit_technician(request, techid):
    tech = get_object_or_404(Technician, techid=techid)
    states = State.objects.all().order_by('state')
    districts = District.objects.filter(statid=tech.statid).order_by('District')

    if request.method == 'POST':
        tech.tech_name = request.POST.get('tech_name', '').strip()
        tech.Address = request.POST.get('Address', '').strip()
        statid = request.POST.get('statid', '').strip()
        Distid = request.POST.get('Distid', '').strip()
        tech.Gender = request.POST.get('Gender', 'Male').strip()
        tech.Quali = request.POST.get('Quali', '').strip()
        tech.Exp = request.POST.get('Exp', '').strip()
        tech.Mob = request.POST.get('Mob', '').strip()
        new_email = request.POST.get('Email', '').strip().lower()
        tech.Status = request.POST.get('Status', 'Active').strip()
        pwd = request.POST.get('password', '').strip()

        old_email = tech.Email

        if statid and Distid:
            tech.statid = get_object_or_404(State, statid=statid)
            tech.Distid = get_object_or_404(District, Distid=Distid)

        with transaction.atomic():
            # If email changed, update AuthUser username
            if new_email != old_email:
                if AuthUser.objects.filter(username=new_email).exclude(username=old_email).exists():
                    messages.error(request, f'Email "{new_email}" is already used by another account.')
                    return render(request, 'accounts/edit_technician.html', {'tech': tech, 'states': states, 'districts': districts})
                
                auth_user = AuthUser.objects.filter(username=old_email).first()
                if auth_user:
                    auth_user.delete()
                    AuthUser.objects.create(
                        username=new_email,
                        password=make_password(pwd) if pwd else auth_user.password,
                        role='Technician'
                    )
                tech.Email = new_email
            elif pwd:
                auth_user = AuthUser.objects.filter(username=old_email).first()
                if auth_user:
                    auth_user.password = make_password(pwd)
                    auth_user.save()

            tech.save()

        messages.success(request, f'Technician "{tech.tech_name}" updated successfully.')
        return redirect('accounts:manage_technicians')

    return render(request, 'accounts/edit_technician.html', {
        'tech': tech,
        'states': states,
        'districts': districts
    })


@admin_required
def delete_technician(request, techid):
    tech = get_object_or_404(Technician, techid=techid)
    if request.method == 'POST':
        try:
            email = tech.Email
            name = tech.tech_name
            with transaction.atomic():
                tech.delete()
                AuthUser.objects.filter(username=email, role='Technician').delete()
            messages.success(request, f'Technician "{name}" and associated credentials removed.')
        except Exception as e:
            messages.error(request, f'Cannot delete technician: Associated work orders exist. ({str(e)})')
    return redirect('accounts:manage_technicians')


@admin_required
def admin_consumers(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    consumers = ConsumerReg.objects.select_related('statid', 'Distid').all().order_by('-consumer_id')

    if q:
        consumers = consumers.filter(fname__icontains=q) | consumers.filter(lname__icontains=q) | consumers.filter(email__icontains=q) | consumers.filter(mob__icontains=q)
    if status_filter:
        consumers = consumers.filter(status=status_filter)

    return render(request, 'accounts/admin_consumers.html', {
        'consumers': consumers,
        'query': q,
        'status_filter': status_filter
    })


@admin_required
def admin_consumer_toggle_status(request, consumer_id):
    consumer = get_object_or_404(ConsumerReg, consumer_id=consumer_id)
    if request.method == 'POST':
        new_status = 'Active' if consumer.status != 'Active' else 'Pending'
        consumer.status = new_status
        consumer.save()
        messages.success(request, f'Consumer {consumer.fname} {consumer.lname} status changed to {new_status}.')
    return redirect('accounts:admin_consumers')


# ==============================================================================
# TECHNICIAN MODULE VIEWS (ACTIVATION & DIRECTORIES)
# ==============================================================================

@tech_required
def tech_activate_consumers(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'Pending').strip()

    consumers = ConsumerReg.objects.select_related('statid', 'Distid').all().order_by('-consumer_id')

    if status_filter and status_filter != 'All':
        consumers = consumers.filter(status=status_filter)

    if q:
        consumers = consumers.filter(
            fname__icontains=q
        ) | consumers.filter(
            lname__icontains=q
        ) | consumers.filter(
            email__icontains=q
        ) | consumers.filter(
            mob__icontains=q
        )

    pending_count = ConsumerReg.objects.filter(status='Pending').count()
    active_count = ConsumerReg.objects.filter(status='Active').count()

    return render(request, 'accounts/tech_activate_consumers.html', {
        'consumers': consumers,
        'query': q,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'active_count': active_count,
    })


@tech_required
def tech_activate_consumer_toggle(request, consumer_id):
    consumer = get_object_or_404(ConsumerReg, consumer_id=consumer_id)
    if request.method == 'POST':
        new_status = 'Active' if consumer.status != 'Active' else 'Pending'
        consumer.status = new_status
        consumer.save()
        messages.success(request, f'Consumer account for {consumer.fname} {consumer.lname} ({consumer.email}) set to {new_status}.')
    return redirect('accounts:tech_activate_consumers')


@tech_required
def tech_service_centers(request):
    states = State.objects.all().order_by('state')
    selected_state = request.GET.get('statid', '').strip()
    selected_dist = request.GET.get('Distid', '').strip()
    q = request.GET.get('q', '').strip()

    centers = ServCenter.objects.filter(status='Active').select_related('statid', 'Distid').order_by('serv_cent')

    if selected_state:
        centers = centers.filter(statid_id=selected_state)
    if selected_dist:
        centers = centers.filter(Distid_id=selected_dist)
    if q:
        centers = centers.filter(serv_cent__icontains=q) | centers.filter(place__icontains=q) | centers.filter(Contact_per__icontains=q)

    districts = District.objects.none()
    if selected_state:
        districts = District.objects.filter(statid_id=selected_state).order_by('District')

    return render(request, 'accounts/tech_service_centers.html', {
        'centers': centers,
        'states': states,
        'districts': districts,
        'selected_state': selected_state,
        'selected_dist': selected_dist,
        'query': q
    })


@tech_required
def tech_technicians(request):
    q = request.GET.get('q', '').strip()
    techs = Technician.objects.select_related('statid', 'Distid').filter(Status='Active').order_by('tech_name')

    if q:
        techs = techs.filter(
            tech_name__icontains=q
        ) | techs.filter(
            Mob__icontains=q
        ) | techs.filter(
            Email__icontains=q
        ) | techs.filter(
            Quali__icontains=q
        )

    return render(request, 'accounts/tech_technicians.html', {
        'techs': techs,
        'query': q
    })

# ==============================================================================
# CONSUMER MODULE VIEWS (PROFILE & SERVICE CENTERS)
# ==============================================================================

@consumer_required
def consumer_profile(request):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)
    states = State.objects.all().order_by('state')
    districts = District.objects.filter(statid=consumer.statid).order_by('District')

    if request.method == 'POST':
        consumer.fname = request.POST.get('fname', '').strip()
        consumer.lname = request.POST.get('lname', '').strip()
        dob = request.POST.get('dob', '').strip()
        if dob:
            consumer.dob = dob
        consumer.address = request.POST.get('address', '').strip()
        statid = request.POST.get('statid', '').strip()
        Distid = request.POST.get('Distid', '').strip()
        consumer.phone = request.POST.get('phone', '').strip()
        consumer.mob = request.POST.get('mob', '').strip()
        consumer.pin = request.POST.get('pin', '').strip()
        consumer.remarks = request.POST.get('remarks', '').strip()
        consumer.consumertype = request.POST.get('consumertype', 'Regular').strip()

        new_password = request.POST.get('new_password', '').strip()

        if statid and Distid:
            consumer.statid = get_object_or_404(State, statid=statid)
            consumer.Distid = get_object_or_404(District, Distid=Distid)

        with transaction.atomic():
            if new_password:
                hashed_pw = make_password(new_password)
                consumer.password = hashed_pw
                auth_user = AuthUser.objects.filter(username=email).first()
                if auth_user:
                    auth_user.password = hashed_pw
                    auth_user.save()

            consumer.save()

        messages.success(request, 'Your consumer profile details have been updated.')
        return redirect('accounts:consumer_profile')

    return render(request, 'accounts/consumer_profile.html', {
        'consumer': consumer,
        'states': states,
        'districts': districts
    })


@consumer_required
def consumer_service_centers(request):
    states = State.objects.all().order_by('state')
    selected_state = request.GET.get('statid', '').strip()
    selected_dist = request.GET.get('Distid', '').strip()
    q = request.GET.get('q', '').strip()

    centers = ServCenter.objects.filter(status='Active').select_related('statid', 'Distid')

    if selected_state:
        centers = centers.filter(statid_id=selected_state)
    if selected_dist:
        centers = centers.filter(Distid_id=selected_dist)
    if q:
        centers = centers.filter(serv_cent__icontains=q) | centers.filter(place__icontains=q)

    districts = District.objects.none()
    if selected_state:
        districts = District.objects.filter(statid_id=selected_state).order_by('District')

    return render(request, 'accounts/consumer_service_centers.html', {
        'centers': centers,
        'states': states,
        'districts': districts,
        'selected_state': selected_state,
        'selected_dist': selected_dist,
        'query': q
    })


def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)



