import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse, HttpResponseForbidden

from accounts.decorators import admin_required, tech_required, consumer_required
from accounts.models import Technician, ConsumerReg, State, District, ServCenter
from products.models import ProductCat, Product, SparePart
from .models import (
    WorkStatus,
    ConsProductReg,
    WorkOrder,
    ActivityDtls,
    DefectsSymptom,
    ServicePart,
    ServicePartDtls,
    ServiceInvoice,
    Complaint,
)


# ==============================================================================
# WORK ORDER STATUSES CRUD
# ==============================================================================

@admin_required
def manage_statuses(request):
    if request.method == 'POST':
        status_name = request.POST.get('W_status', '').strip()
        if not status_name:
            messages.error(request, 'Status name cannot be empty.')
        elif WorkStatus.objects.filter(W_status__iexact=status_name).exists():
            messages.error(request, f'Status "{status_name}" already exists.')
        else:
            WorkStatus.objects.create(W_status=status_name)
            messages.success(request, f'Work Status "{status_name}" created.')
        return redirect('services:manage_statuses')

    statuses = WorkStatus.objects.all().order_by('Wo_stid')
    return render(request, 'services/manage_statuses.html', {'statuses': statuses})


@admin_required
def edit_status(request, Wo_stid):
    status_obj = get_object_or_404(WorkStatus, Wo_stid=Wo_stid)
    if request.method == 'POST':
        new_name = request.POST.get('W_status', '').strip()
        if not new_name:
            messages.error(request, 'Status name cannot be empty.')
        else:
            status_obj.W_status = new_name
            status_obj.save()
            messages.success(request, f'Status updated to "{new_name}".')
            return redirect('services:manage_statuses')
    return render(request, 'services/edit_status.html', {'status': status_obj})


@admin_required
def delete_status(request, Wo_stid):
    status_obj = get_object_or_404(WorkStatus, Wo_stid=Wo_stid)
    if request.method == 'POST':
        try:
            name = status_obj.W_status
            status_obj.delete()
            messages.success(request, f'Status "{name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f'Cannot delete status: Associated work orders exist. ({str(e)})')
    return redirect('services:manage_statuses')


# ==============================================================================
# OPERATIONS & OVERSIGHT: REGISTERED PRODUCTS & WORK ORDERS
# ==============================================================================

@admin_required
def admin_consumer_products(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    products_reg = ConsProductReg.objects.select_related('consumer_id', 'prid', 'prid__pcatid').all().order_by('-Reg_id')

    if q:
        products_reg = products_reg.filter(
            consumer_id__fname__icontains=q
        ) | products_reg.filter(
            prid__prname__icontains=q
        ) | products_reg.filter(
            prod_no__icontains=q
        ) | products_reg.filter(
            warnt_cardno__icontains=q
        )

    if status_filter:
        products_reg = products_reg.filter(Isactive=status_filter)

    today = timezone.now().date()
    # Annotate warranty validity
    records = []
    for reg in products_reg:
        is_warranty_valid = (reg.warnt_enddate >= today)
        records.append({
            'reg': reg,
            'is_warranty_valid': is_warranty_valid,
        })

    return render(request, 'services/admin_consumer_products.html', {
        'records': records,
        'query': q,
        'status_filter': status_filter,
        'today': today
    })


@admin_required
def admin_toggle_product_activation(request, reg_id):
    reg = get_object_or_404(ConsProductReg, Reg_id=reg_id)
    if request.method == 'POST':
        reg.Isactive = 'Active' if reg.Isactive != 'Active' else 'Pending'
        reg.save()
        messages.success(request, f'Registration #{reg.Reg_id} ({reg.prid.prname}) status changed to {reg.Isactive}.')
    return redirect('services:admin_consumer_products')


@admin_required
def admin_work_orders(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    tech_filter = request.GET.get('tech', '').strip()

    orders_qs = WorkOrder.objects.select_related(
        'techid', 'w_stid', 'reg_id__consumer_id', 'reg_id__prid'
    ).all().order_by('-W_orderid')

    if q:
        orders_qs = orders_qs.filter(
            Serv_req_no__icontains=q
        ) | orders_qs.filter(
            reg_id__consumer_id__fname__icontains=q
        ) | orders_qs.filter(
            reg_id__prid__prname__icontains=q
        )

    if status_filter:
        orders_qs = orders_qs.filter(w_stid_id=status_filter)
    if tech_filter:
        orders_qs = orders_qs.filter(techid_id=tech_filter)

    today = timezone.now().date()
    orders_data = []
    for o in orders_qs:
        # Business logic rule: Compare cre_date or today with warnt_enddate
        in_warranty = (o.cre_date <= o.reg_id.warnt_enddate)
        orders_data.append({
            'order': o,
            'in_warranty': in_warranty,
        })

    technicians = Technician.objects.filter(Status='Active').order_by('tech_name')
    statuses = WorkStatus.objects.all().order_by('Wo_stid')

    return render(request, 'services/admin_work_orders.html', {
        'orders_data': orders_data,
        'technicians': technicians,
        'statuses': statuses,
        'query': q,
        'status_filter': status_filter,
        'tech_filter': tech_filter
    })


@admin_required
def admin_assign_work_order(request, w_orderid):
    order = get_object_or_404(
        WorkOrder.objects.select_related('techid', 'w_stid', 'reg_id__consumer_id', 'reg_id__prid'),
        W_orderid=w_orderid
    )
    technicians = Technician.objects.filter(Status='Active').order_by('tech_name')
    statuses = WorkStatus.objects.all().order_by('Wo_stid')
    in_warranty = (order.cre_date <= order.reg_id.warnt_enddate)

    if request.method == 'POST':
        techid = request.POST.get('techid', '').strip()
        w_stid = request.POST.get('w_stid', '').strip()
        Inv_amt = request.POST.get('Inv_amt', '0.0').strip()
        prom_del_date = request.POST.get('prom_del_date', '').strip()
        jobsheet_type = request.POST.get('jobsheet_type', 'Standard').strip()
        calltype = request.POST.get('calltype', 'Repair').strip()
        loc_type = request.POST.get('loc_type', 'Home Service').strip()
        assignment_remark = request.POST.get('remark', '').strip()

        with transaction.atomic():
            if techid:
                order.techid = get_object_or_404(Technician, techid=techid)
            if w_stid:
                order.w_stid = get_object_or_404(WorkStatus, Wo_stid=w_stid)
            
            order.Inv_amt = float(Inv_amt or 0.0)
            if prom_del_date:
                order.prom_del_date = prom_del_date
            order.jobsheet_type = jobsheet_type
            order.calltype = calltype
            order.loc_type = loc_type
            order.save()

            # Record in Activity Details
            remark_text = assignment_remark or f"Assigned to {order.techid.tech_name if order.techid else 'technician'}. Status: {order.w_stid.W_status}."
            ActivityDtls.objects.create(
                W_orderid=order,
                act_status=order.w_stid.W_status,
                Remark=remark_text
            )

        messages.success(request, f'Work Order #{order.W_orderid} updated and assigned successfully.')
        return redirect('services:admin_work_orders')

    return render(request, 'services/admin_assign_work_order.html', {
        'order': order,
        'technicians': technicians,
        'statuses': statuses,
        'in_warranty': in_warranty
    })


@admin_required
def admin_work_order_details(request, w_orderid):
    order = get_object_or_404(
        WorkOrder.objects.select_related('techid', 'w_stid', 'reg_id__consumer_id', 'reg_id__prid'),
        W_orderid=w_orderid
    )
    activities = ActivityDtls.objects.filter(W_orderid=order).order_by('-Activityno')
    defects = DefectsSymptom.objects.filter(W_orderid=order)
    service_parts = ServicePart.objects.filter(W_orderid=order).prefetch_related('details__spareid')
    invoice = ServiceInvoice.objects.filter(W_orderid=order).first()
    in_warranty = (order.cre_date <= order.reg_id.warnt_enddate)

    return render(request, 'services/admin_work_order_details.html', {
        'order': order,
        'activities': activities,
        'defects': defects,
        'service_parts': service_parts,
        'invoice': invoice,
        'in_warranty': in_warranty
    })


# ==============================================================================
# PORTAL COMPLAINTS MANAGEMENT
# ==============================================================================

@admin_required
def admin_complaints(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    complaints = Complaint.objects.select_related('Reg_id__consumer_id', 'Reg_id__prid').all().order_by('-com_id')

    if q:
        complaints = complaints.filter(
            Complaint__icontains=q
        ) | complaints.filter(
            Reg_id__consumer_id__fname__icontains=q
        )

    if status_filter:
        complaints = complaints.filter(Status=status_filter)

    return render(request, 'services/admin_complaints.html', {
        'complaints': complaints,
        'query': q,
        'status_filter': status_filter
    })


@admin_required
def admin_reply_complaint(request, com_id):
    complaint = get_object_or_404(Complaint, com_id=com_id)
    if request.method == 'POST':
        reply_text = request.POST.get('Reply', '').strip()
        status = request.POST.get('Status', 'Resolved').strip()
        if not reply_text:
            messages.error(request, 'Reply message cannot be empty.')
        else:
            complaint.Reply = reply_text
            complaint.Status = status
            complaint.save()
            messages.success(request, f'Reply submitted for Complaint #{complaint.com_id}.')
        return redirect('services:admin_complaints')
    return render(request, 'services/admin_reply_complaint.html', {'complaint': complaint})


# ==============================================================================
# PRINTABLE SERVICE INVOICE & ADMIN REPORTS
# ==============================================================================

def print_service_invoice(request, invoice_id):
    session_role = request.session.get('role')
    username = request.session.get('username')

    if not session_role or not username:
        messages.error(request, 'Please log in to view invoices.')
        return redirect('accounts:login')

    invoice = get_object_or_404(
        ServiceInvoice.objects.select_related(
            'W_orderid',
            'W_orderid__reg_id',
            'W_orderid__reg_id__consumer_id',
            'W_orderid__reg_id__consumer_id__statid',
            'W_orderid__reg_id__consumer_id__Distid',
            'W_orderid__reg_id__prid',
            'W_orderid__reg_id__prid__pcatid',
            'W_orderid__techid',
            'W_orderid__w_stid'
        ),
        Invoice_id=invoice_id
    )

    order = invoice.W_orderid
    consumer = order.reg_id.consumer_id

    # If role is Consumer, verify ownership
    if session_role == 'Consumer' and consumer.email != username:
        return HttpResponseForbidden('You do not have permission to view this invoice.')

    in_warranty = (order.cre_date <= order.reg_id.warnt_enddate) if (order.reg_id and order.reg_id.warnt_enddate) else False
    service_parts = ServicePart.objects.filter(W_orderid=order).prefetch_related('details__spareid')
    defects = DefectsSymptom.objects.filter(W_orderid=order)

    # Calculate itemized parts breakdown
    parts_breakdown = []
    parts_total = 0.0
    for sp in service_parts:
        for dt in sp.details.all():
            line_total = dt.Qty * dt.spareid.price
            parts_total += line_total
            parts_breakdown.append({
                'part_name': dt.spareid.partsname,
                'section': sp.Section,
                'position': sp.Position,
                'reason': sp.Reason,
                'price': dt.spareid.price,
                'qty': dt.Qty,
                'subtotal': line_total,
            })

    # Labor / service charge
    if in_warranty:
        labor_charge = 0.0
        warranty_discount = parts_total
    elif invoice.Amount == 0.0:
        labor_charge = 0.0
        warranty_discount = 0.0
    else:
        labor_charge = max(0.0, invoice.Amount - parts_total)
        warranty_discount = 0.0

    center = ServCenter.objects.filter(status='Active').select_related('statid', 'Distid').first()

    return render(request, 'services/print_service_invoice.html', {
        'invoice': invoice,
        'order': order,
        'consumer': consumer,
        'in_warranty': in_warranty,
        'parts_breakdown': parts_breakdown,
        'parts_total': parts_total,
        'labor_charge': labor_charge,
        'warranty_discount': warranty_discount,
        'defects': defects,
        'center': center,
        'session_role': session_role,
    })


@admin_required
def admin_reports(request):
    tab = request.GET.get('tab', 'service_centers').strip()
    export_csv = (request.GET.get('export', '') == 'csv')
    today = timezone.now().date()

    states = State.objects.all().order_by('state')
    categories = ProductCat.objects.all().order_by('category')
    technicians = Technician.objects.filter(Status='Active').order_by('tech_name')
    statuses = WorkStatus.objects.all().order_by('Wo_stid')

    # 1. SERVICE CENTERS REPORT
    if tab == 'service_centers':
        statid = request.GET.get('statid', '').strip()
        distid = request.GET.get('Distid', '').strip()
        status_val = request.GET.get('status', '').strip()

        qs = ServCenter.objects.select_related('statid', 'Distid').all().order_by('serv_cent')
        if statid:
            qs = qs.filter(statid_id=statid)
        if distid:
            qs = qs.filter(Distid_id=distid)
        if status_val and status_val != 'All':
            qs = qs.filter(status=status_val)

        if export_csv:
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="service_centers_report_{today}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Center ID', 'Center Name', 'Place', 'District', 'State', 'PIN', 'Contact Person', 'Phone', 'Mobile', 'Email', 'Status'])
            for c in qs:
                writer.writerow([c.serv_centid, c.serv_cent, c.place, c.Distid.District, c.statid.state, c.pin, c.Contact_per, c.phone, c.mob, c.email, c.status])
            return response

        districts = District.objects.filter(statid_id=statid).order_by('District') if statid else District.objects.none()

        return render(request, 'services/admin_reports.html', {
            'tab': tab,
            'report_data': qs,
            'total_count': qs.count(),
            'active_count': qs.filter(status='Active').count(),
            'states': states,
            'districts': districts,
            'selected_state': statid,
            'selected_dist': distid,
            'selected_status': status_val,
            'today': today,
        })

    # 2. CONSUMER REGISTRATIONS REPORT
    elif tab == 'consumers':
        statid = request.GET.get('statid', '').strip()
        status_val = request.GET.get('status', '').strip()
        from_date = request.GET.get('from_date', '').strip()
        to_date = request.GET.get('to_date', '').strip()

        qs = ConsumerReg.objects.select_related('statid', 'Distid').all().order_by('-consumer_id')
        if statid:
            qs = qs.filter(statid_id=statid)
        if status_val and status_val != 'All':
            qs = qs.filter(status=status_val)
        if from_date:
            qs = qs.filter(regdate__gte=from_date)
        if to_date:
            qs = qs.filter(regdate__lte=to_date)

        if export_csv:
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="consumer_report_{today}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Consumer ID', 'First Name', 'Last Name', 'Email', 'Mobile', 'District', 'State', 'PIN', 'DOB', 'Registered Date', 'Status'])
            for c in qs:
                writer.writerow([c.consumer_id, c.fname, c.lname, c.email, c.mob, c.Distid.District, c.statid.state, c.pin, c.dob, c.regdate, c.status])
            return response

        return render(request, 'services/admin_reports.html', {
            'tab': tab,
            'report_data': qs,
            'total_count': qs.count(),
            'active_count': qs.filter(status='Active').count(),
            'pending_count': qs.filter(status='Pending').count(),
            'states': states,
            'selected_state': statid,
            'selected_status': status_val,
            'from_date': from_date,
            'to_date': to_date,
            'today': today,
        })

    # 3. APPLIANCES & WARRANTY REPORT
    elif tab == 'products':
        pcatid = request.GET.get('pcatid', '').strip()
        status_val = request.GET.get('status', '').strip()
        warranty_val = request.GET.get('warranty', '').strip()

        qs = ConsProductReg.objects.select_related('consumer_id', 'prid', 'prid__pcatid').all().order_by('-Reg_id')
        if pcatid:
            qs = qs.filter(prid__pcatid_id=pcatid)
        if status_val and status_val != 'All':
            qs = qs.filter(Isactive=status_val)
        if warranty_val == 'In Warranty':
            qs = qs.filter(warnt_enddate__gte=today)
        elif warranty_val == 'Expired':
            qs = qs.filter(warnt_enddate__lt=today)

        if export_csv:
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="appliance_warranty_report_{today}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Reg ID', 'Consumer Name', 'Consumer Mobile', 'Product Name', 'Category', 'Model', 'Serial No', 'Warranty Card', 'Invoice No', 'Invoice Date', 'Warranty End Date', 'Warranty Status', 'Active Status'])
            for a in qs:
                w_status = 'In Warranty' if a.warnt_enddate >= today else 'Expired'
                writer.writerow([a.Reg_id, f"{a.consumer_id.fname} {a.consumer_id.lname}", a.consumer_id.mob, a.prid.prname, a.prid.pcatid.category, a.prid.model, a.prod_no, a.warnt_cardno, a.Invoice_no, a.Invoice_date, a.warnt_enddate, w_status, a.Isactive])
            return response

        appliance_data = []
        in_warnt_count = 0
        for a in qs:
            is_valid = (a.warnt_enddate >= today)
            if is_valid:
                in_warnt_count += 1
            appliance_data.append({
                'app': a,
                'in_warranty': is_valid
            })

        return render(request, 'services/admin_reports.html', {
            'tab': tab,
            'appliance_data': appliance_data,
            'total_count': qs.count(),
            'in_warnt_count': in_warnt_count,
            'categories': categories,
            'selected_cat': pcatid,
            'selected_status': status_val,
            'selected_warranty': warranty_val,
            'today': today,
        })

    # 4. WORK ORDERS & REVENUE REPORT
    else:  # tab == 'work_orders'
        techid = request.GET.get('techid', '').strip()
        status_id = request.GET.get('w_stid', '').strip()
        loc_type = request.GET.get('loc_type', '').strip()
        from_date = request.GET.get('from_date', '').strip()
        to_date = request.GET.get('to_date', '').strip()

        qs = WorkOrder.objects.select_related('techid', 'w_stid', 'reg_id__consumer_id', 'reg_id__prid').all().order_by('-W_orderid')
        if techid:
            qs = qs.filter(techid_id=techid)
        if status_id:
            qs = qs.filter(w_stid_id=status_id)
        if loc_type:
            qs = qs.filter(loc_type=loc_type)
        if from_date:
            qs = qs.filter(cre_date__gte=from_date)
        if to_date:
            qs = qs.filter(cre_date__lte=to_date)

        if export_csv:
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="work_orders_report_{today}.csv"'
            writer = csv.writer(response)
            writer.writerow(['WO ID', 'Request No', 'Consumer', 'Appliance', 'Technician', 'Status', 'Location', 'Call Type', 'Jobsheet', 'Created Date', 'Closed Date', 'Invoice Amount'])
            for o in qs:
                tech_name = o.techid.tech_name if o.techid else 'Unassigned'
                writer.writerow([o.W_orderid, o.Serv_req_no, f"{o.reg_id.consumer_id.fname} {o.reg_id.consumer_id.lname}", o.reg_id.prid.prname, tech_name, o.w_stid.W_status, o.loc_type, o.calltype, o.jobsheet_type, o.cre_date, o.close_date or '', o.Inv_amt])
            return response

        total_revenue = sum(o.Inv_amt for o in qs.filter(w_stid__W_status='Completed'))
        completed_count = qs.filter(w_stid__W_status='Completed').count()
        pending_count = qs.filter(w_stid__W_status='Pending').count()

        return render(request, 'services/admin_reports.html', {
            'tab': 'work_orders',
            'report_data': qs,
            'total_count': qs.count(),
            'completed_count': completed_count,
            'pending_count': pending_count,
            'total_revenue': total_revenue,
            'technicians': technicians,
            'statuses': statuses,
            'selected_tech': techid,
            'selected_status': status_id,
            'selected_loc': loc_type,
            'from_date': from_date,
            'to_date': to_date,
            'today': today,
        })

# ==============================================================================
# TECHNICIAN MODULE VIEWS (APPLIANCE ACTIVATION, DIAGNOSTICS & BILLING)
# ==============================================================================

@tech_required
def tech_activate_products(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'Pending').strip()
    today = timezone.now().date()

    appliances = ConsProductReg.objects.select_related(
        'consumer_id', 'prid', 'prid__pcatid'
    ).all().order_by('-Reg_id')

    if status_filter and status_filter != 'All':
        appliances = appliances.filter(Isactive=status_filter)

    if q:
        appliances = appliances.filter(
            consumer_id__fname__icontains=q
        ) | appliances.filter(
            consumer_id__lname__icontains=q
        ) | appliances.filter(
            consumer_id__email__icontains=q
        ) | appliances.filter(
            prid__prname__icontains=q
        ) | appliances.filter(
            prid__model__icontains=q
        ) | appliances.filter(
            prod_no__icontains=q
        ) | appliances.filter(
            warnt_cardno__icontains=q
        ) | appliances.filter(
            Invoice_no__icontains=q
        )

    appliance_data = []
    for a in appliances:
        in_warranty = (a.warnt_enddate >= today)
        appliance_data.append({
            'app': a,
            'in_warranty': in_warranty
        })

    pending_count = ConsProductReg.objects.filter(Isactive='Pending').count()
    active_count = ConsProductReg.objects.filter(Isactive='Active').count()

    return render(request, 'services/tech_activate_products.html', {
        'appliance_data': appliance_data,
        'query': q,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'active_count': active_count,
        'today': today
    })


@tech_required
def tech_activate_product_toggle(request, reg_id):
    reg = get_object_or_404(ConsProductReg, Reg_id=reg_id)
    if request.method == 'POST':
        new_status = 'Active' if reg.Isactive != 'Active' else 'Pending'
        reg.Isactive = new_status
        reg.save()
        messages.success(request, f'Appliance "{reg.prid.prname}" (Serial: {reg.prod_no}) activation status updated to {new_status}.')
    return redirect('services:tech_activate_products')


@tech_required
def tech_work_order_detail(request, w_orderid):
    order = get_object_or_404(
        WorkOrder.objects.select_related('techid', 'w_stid', 'reg_id__consumer_id', 'reg_id__prid'),
        W_orderid=w_orderid
    )
    today = timezone.now().date()
    in_warranty = (order.cre_date <= order.reg_id.warnt_enddate) if (order.reg_id and order.reg_id.warnt_enddate) else False

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        if action == 'update_status':
            status_id = request.POST.get('status_id')
            jobsheet_type = request.POST.get('jobsheet_type', '').strip()
            prom_del_date = request.POST.get('prom_del_date', '').strip()
            remark = request.POST.get('remark', '').strip()

            if status_id:
                new_status = get_object_or_404(WorkStatus, Wo_stid=status_id)
                order.w_stid = new_status
            if jobsheet_type:
                order.jobsheet_type = jobsheet_type
            if prom_del_date:
                order.prom_del_date = prom_del_date

            order.save()

            note = remark if remark else f"Technician updated work order status to {order.w_stid.W_status}."
            ActivityDtls.objects.create(
                W_orderid=order,
                act_status=order.w_stid.W_status,
                Remark=note
            )
            messages.success(request, f'Work order #{order.W_orderid} status updated to {order.w_stid.W_status}.')
            return redirect('services:tech_work_order_detail', w_orderid=order.W_orderid)

        elif action == 'log_defect':
            defect_bytech = request.POST.get('defect_bytech', '').strip()
            defect_des = request.POST.get('defect_des', '').strip()
            condition = request.POST.get('Condition', 'Fair').strip()
            symptom = request.POST.get('Symptom', 'Faulty').strip()
            actual_rep = request.POST.get('Actual_rep', 'Repair').strip()
            faulty = request.POST.get('Faulty', 'Yes').strip()
            repaired = request.POST.get('Repaired', 'Yes').strip()
            msg = request.POST.get('Msg', '').strip()
            spareused = request.POST.get('Spareused', 'No').strip()
            status_val = request.POST.get('Status', 'Diagnosed').strip()

            if not defect_bytech or not defect_des:
                messages.error(request, 'Please provide defect name and diagnostic description.')
            else:
                DefectsSymptom.objects.create(
                    W_orderid=order,
                    defect_bytech=defect_bytech,
                    defect_des=defect_des,
                    Condition=condition,
                    Symptom=symptom,
                    Actual_rep=actual_rep,
                    Faulty=faulty,
                    Repaired=repaired,
                    Msg=msg,
                    Spareused=spareused,
                    Status=status_val
                )
                ActivityDtls.objects.create(
                    W_orderid=order,
                    act_status='In Progress',
                    Remark=f"Diagnostic defect logged: {defect_bytech} (Repaired: {repaired})."
                )
                messages.success(request, f'Diagnostic defect "{defect_bytech}" logged successfully.')
            return redirect('services:tech_work_order_detail', w_orderid=order.W_orderid)

        elif action == 'add_activity':
            act_status = request.POST.get('act_status', 'In Progress').strip()
            remark = request.POST.get('remark', '').strip()
            if not remark:
                messages.error(request, 'Activity remark cannot be blank.')
            else:
                ActivityDtls.objects.create(
                    W_orderid=order,
                    act_status=act_status,
                    Remark=remark
                )
                messages.success(request, 'Progress update added to activity history.')
            return redirect('services:tech_work_order_detail', w_orderid=order.W_orderid)

        elif action == 'add_spare_part':
            spare_id = request.POST.get('spare_id')
            qty_str = request.POST.get('qty', '1').strip()
            reason = request.POST.get('reason', 'Replacement').strip()
            position = request.POST.get('position', 'Internal').strip()
            section = request.POST.get('section', 'Main Unit').strip()
            defects = request.POST.get('defects', 'Faulty').strip()
            repair = request.POST.get('repair', 'Replaced').strip()

            try:
                qty_val = int(qty_str)
                if qty_val <= 0:
                    raise ValueError
            except ValueError:
                messages.error(request, 'Quantity must be a positive integer.')
                return redirect('services:tech_work_order_detail', w_orderid=order.W_orderid)

            with transaction.atomic():
                spare = get_object_or_404(SparePart, spareid=spare_id)
                if spare.qty < qty_val:
                    messages.error(request, f'Insufficient inventory for "{spare.partsname}". Available stock is {spare.qty}, but {qty_val} was requested.')
                else:
                    # Deduct from inventory
                    spare.qty -= qty_val
                    spare.save()

                    # Create ServicePart header & ServicePartDtls
                    serv_part = ServicePart.objects.create(
                        W_orderid=order,
                        Reason=reason,
                        Position=position,
                        Section=section,
                        Defects=defects,
                        Repair=repair
                    )
                    ServicePartDtls.objects.create(
                        servpartid=serv_part,
                        spareid=spare,
                        Qty=qty_val
                    )
                    ActivityDtls.objects.create(
                        W_orderid=order,
                        act_status='In Progress',
                        Remark=f"Spare part consumed: {spare.partsname} x{qty_val} (₹{spare.price:.2f}/ea). Stock remaining: {spare.qty}."
                    )
                    messages.success(request, f'Allocated {qty_val}x "{spare.partsname}" to this repair ticket. Current stock updated to {spare.qty}.')

            return redirect('services:tech_work_order_detail', w_orderid=order.W_orderid)

    activities = ActivityDtls.objects.filter(W_orderid=order).order_by('-Activityno')
    defects = DefectsSymptom.objects.filter(W_orderid=order).order_by('-defect_id')
    service_parts = ServicePart.objects.filter(W_orderid=order).prefetch_related('details__spareid')
    invoice = ServiceInvoice.objects.filter(W_orderid=order).first()
    statuses = WorkStatus.objects.all().order_by('Wo_stid')
    available_spares = SparePart.objects.select_related('prid').all().order_by('partsname')

    # Calculate current spare parts cost
    parts_total = sum(
        d.Qty * d.spareid.price
        for sp in service_parts
        for d in sp.details.all()
    )

    return render(request, 'services/tech_work_order_detail.html', {
        'order': order,
        'activities': activities,
        'defects': defects,
        'service_parts': service_parts,
        'invoice': invoice,
        'statuses': statuses,
        'available_spares': available_spares,
        'in_warranty': in_warranty,
        'parts_total': parts_total,
        'today': today,
    })


@tech_required
def tech_generate_invoice(request, w_orderid):
    order = get_object_or_404(
        WorkOrder.objects.select_related('reg_id', 'reg_id__prid', 'techid'),
        W_orderid=w_orderid
    )
    today = timezone.now().date()
    in_warranty = (order.cre_date <= order.reg_id.warnt_enddate) if (order.reg_id and order.reg_id.warnt_enddate) else False

    if request.method == 'POST':
        repaired_choice = request.POST.get('repaired', 'Yes').strip()  # 'Yes' or 'No'
        service_fee_str = request.POST.get('service_fee', '350.0').strip()
        try:
            service_fee = float(service_fee_str)
        except ValueError:
            service_fee = 350.0

        with transaction.atomic():
            # Calculate parts cost
            parts_dtls = ServicePartDtls.objects.filter(servpartid__W_orderid=order).select_related('spareid')
            parts_total = sum(d.Qty * d.spareid.price for d in parts_dtls)

            # Rule 1 (Under Warranty):
            # If under warranty, service & spare charges = 0.00.
            # If in-warranty product cannot be repaired, flag for Replacement.
            if in_warranty:
                amount = 0.0
                if repaired_choice == 'No':
                    order.jobsheet_type = 'Warranty Replacement'
                    completed_st, _ = WorkStatus.objects.get_or_create(W_status='Completed')
                    order.w_stid = completed_st
                    remark = "In-warranty appliance cannot be repaired. Ticket closed and escalated for Warranty Product Replacement."
                else:
                    completed_st, _ = WorkStatus.objects.get_or_create(W_status='Completed')
                    order.w_stid = completed_st
                    remark = "In-warranty repair completed at ₹0.00 warranty coverage."

            # Rule 2 (Out of Warranty & Irreparable):
            # If out of warranty AND marked Irreparable, service charge = 0.00.
            elif not in_warranty and repaired_choice == 'No':
                amount = 0.0
                irrep_st, _ = WorkStatus.objects.get_or_create(W_status='Irreparable')
                order.w_stid = irrep_st
                remark = "Out-of-warranty appliance is irreparable. Closed with ₹0.00 charge per company policy."

            # Rule 3 (Out of Warranty & Repaired):
            # If out of warranty AND Repaired, Invoice Amount =
            # Sum(Service_parts_dtls.Qty * Spare_parts.price) + Service Fee.
            else:
                amount = parts_total + service_fee
                completed_st, _ = WorkStatus.objects.get_or_create(W_status='Completed')
                order.w_stid = completed_st
                remark = f"Out-of-warranty repair completed. Parts: ₹{parts_total:.2f}, Service Fee: ₹{service_fee:.2f}. Total: ₹{amount:.2f}."

            # Save / update ServiceInvoice
            invoice, created = ServiceInvoice.objects.update_or_create(
                W_orderid=order,
                defaults={
                    'Inv_date': today,
                    'Amount': amount,
                }
            )

            # Update WorkOrder
            order.Inv_amt = amount
            order.close_date = today
            order.save()

            # Record ActivityDtls
            ActivityDtls.objects.create(
                W_orderid=order,
                act_status=order.w_stid.W_status,
                Remark=remark
            )

            messages.success(request, f'Invoice #{invoice.Invoice_id} generated for Work Order #{order.W_orderid} with Final Amount: ₹{amount:.2f}.')
            return redirect('services:tech_work_order_detail', w_orderid=order.W_orderid)

    # GET request - show invoice preview / confirmation
    parts_dtls = ServicePartDtls.objects.filter(servpartid__W_orderid=order).select_related('spareid')
    parts_total = sum(d.Qty * d.spareid.price for d in parts_dtls)
    latest_defect = DefectsSymptom.objects.filter(W_orderid=order).order_by('-defect_id').first()

    return render(request, 'services/tech_generate_invoice.html', {
        'order': order,
        'in_warranty': in_warranty,
        'parts_dtls': parts_dtls,
        'parts_total': parts_total,
        'latest_defect': latest_defect,
        'today': today
    })

# ==============================================================================
# CONSUMER MODULE VIEWS
# ==============================================================================

import random

@consumer_required
def consumer_register_product(request):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)
    products = Product.objects.select_related('pcatid').all().order_by('prname')
    today = timezone.now().date()

    if request.method == 'POST':
        prid = request.POST.get('prid', '').strip()
        prod_no = request.POST.get('prod_no', '').strip()
        warnt_cardno = request.POST.get('warnt_cardno', '').strip()
        Invoice_no = request.POST.get('Invoice_no', '').strip()
        Invoice_date = request.POST.get('Invoice_date', '').strip()
        warnt_enddate = request.POST.get('warnt_enddate', '').strip()

        if not (prid and prod_no and warnt_cardno and Invoice_no and Invoice_date and warnt_enddate):
            messages.error(request, 'Please complete all required fields.')
        elif ConsProductReg.objects.filter(prod_no=prod_no).exists():
            messages.error(request, f'An appliance with serial number "{prod_no}" is already registered.')
        else:
            product_obj = get_object_or_404(Product, prid=prid)
            ConsProductReg.objects.create(
                consumer_id=consumer,
                prid=product_obj,
                prod_no=int(prod_no),
                warnt_cardno=int(warnt_cardno),
                Invoice_no=int(Invoice_no),
                Invoice_date=Invoice_date,
                warnt_enddate=warnt_enddate,
                Isactive='Pending'
            )
            messages.success(request, f'Appliance "{product_obj.prname}" registered successfully! It is pending technician verification.')
            return redirect('services:consumer_register_product')

    user_appliances = ConsProductReg.objects.filter(consumer_id=consumer).select_related('prid', 'prid__pcatid').order_by('-Reg_id')
    annotated_apps = []
    for a in user_appliances:
        annotated_apps.append({
            'app': a,
            'in_warranty': (a.warnt_enddate >= today),
        })

    return render(request, 'services/consumer_register_product.html', {
        'products': products,
        'annotated_apps': annotated_apps,
        'today': today
    })


@consumer_required
def consumer_book_service(request):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)
    active_appliances = ConsProductReg.objects.filter(consumer_id=consumer, Isactive='Active').select_related('prid')

    if request.method == 'POST':
        reg_id = request.POST.get('reg_id', '').strip()
        loc_type = request.POST.get('loc_type', 'Home Service').strip()
        calltype = request.POST.get('calltype', 'Repair').strip()
        issue_des = request.POST.get('issue_des', '').strip()

        if not (reg_id and issue_des):
            messages.error(request, 'Please select a verified appliance and describe the fault.')
        else:
            selected_reg = get_object_or_404(ConsProductReg, Reg_id=reg_id, consumer_id=consumer)
            
            # Activation Gate Check
            if selected_reg.Isactive != 'Active':
                messages.error(request, 'This product is pending technician verification and cannot be booked for service yet.')
                return redirect('services:consumer_book_service')

            # Generate unique 6-digit Serv_req_no
            while True:
                req_no = random.randint(100000, 999999)
                if not WorkOrder.objects.filter(Serv_req_no=req_no).exists():
                    break

            pending_status, _ = WorkStatus.objects.get_or_create(W_status='Pending')

            with transaction.atomic():
                order = WorkOrder.objects.create(
                    Serv_req_no=req_no,
                    reg_id=selected_reg,
                    cons_pdtid=selected_reg.Reg_id,
                    prod_no=selected_reg.prod_no,
                    w_stid=pending_status,
                    loc_type=loc_type,
                    calltype=calltype,
                    jobsheet_type='Standard',
                    Inv_amt=0.0
                )

                ActivityDtls.objects.create(
                    W_orderid=order,
                    act_status='Pending',
                    Remark=f"Repair request booked by consumer. Issue: {issue_des}"
                )

            messages.success(request, f'Repair request raised successfully! Your Service Request No is #{req_no}.')
            return redirect('services:consumer_track_orders')

    return render(request, 'services/consumer_book_service.html', {
        'active_appliances': active_appliances
    })


@consumer_required
def consumer_track_orders(request):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)
    today = timezone.now().date()

    orders_qs = WorkOrder.objects.filter(
        reg_id__consumer_id=consumer
    ).select_related('techid', 'w_stid', 'reg_id__prid').order_by('-W_orderid')

    orders_data = []
    for o in orders_qs:
        orders_data.append({
            'order': o,
            'in_warranty': (o.cre_date <= o.reg_id.warnt_enddate),
        })

    return render(request, 'services/consumer_track_orders.html', {
        'orders_data': orders_data,
        'today': today
    })


@consumer_required
def consumer_track_order_detail(request, w_orderid):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)
    order = get_object_or_404(
        WorkOrder.objects.select_related('techid', 'w_stid', 'reg_id__prid', 'reg_id__consumer_id'),
        W_orderid=w_orderid,
        reg_id__consumer_id=consumer
    )
    activities = ActivityDtls.objects.filter(W_orderid=order).order_by('-Activityno')
    defects = DefectsSymptom.objects.filter(W_orderid=order)
    invoice = ServiceInvoice.objects.filter(W_orderid=order).first()
    in_warranty = (order.cre_date <= order.reg_id.warnt_enddate)

    return render(request, 'services/consumer_track_order_detail.html', {
        'order': order,
        'activities': activities,
        'defects': defects,
        'invoice': invoice,
        'in_warranty': in_warranty
    })


@consumer_required
def consumer_respond_estimate(request, w_orderid):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)
    order = get_object_or_404(WorkOrder, W_orderid=w_orderid, reg_id__consumer_id=consumer)

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()
        with transaction.atomic():
            if action == 'accept':
                assigned_status, _ = WorkStatus.objects.get_or_create(W_status='Assigned')
                order.w_stid = assigned_status
                order.save()
                ActivityDtls.objects.create(
                    W_orderid=order,
                    act_status='Assigned',
                    Remark=f"Repair estimate of ₹{order.Inv_amt:.2f} accepted by consumer. Ready for repair."
                )
                messages.success(request, f'Repair estimate of ₹{order.Inv_amt:.2f} accepted! Technician will commence repair.')
            elif action == 'cancel':
                cancelled_status, _ = WorkStatus.objects.get_or_create(W_status='Cancelled')
                order.w_stid = cancelled_status
                order.save()
                ActivityDtls.objects.create(
                    W_orderid=order,
                    act_status='Cancelled',
                    Remark=f"Repair estimate of ₹{order.Inv_amt:.2f} rejected by consumer. Work order cancelled."
                )
                messages.warning(request, f'Work order #{order.W_orderid} has been cancelled.')

    return redirect('services:consumer_track_order_detail', w_orderid=w_orderid)


@consumer_required
def consumer_history(request):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)

    completed_orders = WorkOrder.objects.filter(
        reg_id__consumer_id=consumer,
        w_stid__W_status__in=['Completed', 'Closed']
    ).select_related('techid', 'w_stid', 'reg_id__prid').prefetch_related('invoices').order_by('-close_date')

    return render(request, 'services/consumer_history.html', {
        'completed_orders': completed_orders
    })


@consumer_required
def consumer_complaints(request):
    email = request.session.get('username')
    consumer = get_object_or_404(ConsumerReg, email=email)
    user_appliances = ConsProductReg.objects.filter(consumer_id=consumer).select_related('prid')

    if request.method == 'POST':
        reg_id = request.POST.get('reg_id', '').strip()
        complaint_text = request.POST.get('complaint', '').strip()

        if not (reg_id and complaint_text):
            messages.error(request, 'Please select an appliance and provide your complaint description.')
        else:
            reg_obj = get_object_or_404(ConsProductReg, Reg_id=reg_id, consumer_id=consumer)
            Complaint.objects.create(
                Reg_id=reg_obj,
                Complaint=complaint_text,
                Status='Open'
            )
            messages.success(request, 'Complaint submitted successfully! Our service management team will review and respond.')
            return redirect('services:consumer_complaints')

    complaints_list = Complaint.objects.filter(
        Reg_id__consumer_id=consumer
    ).select_related('Reg_id__prid').order_by('-com_id')

    return render(request, 'services/consumer_complaints.html', {
        'complaints': complaints_list,
        'user_appliances': user_appliances
    })

