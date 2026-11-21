from django.contrib import admin
from .models import (
    ConsProductReg,
    WorkStatus,
    WorkOrder,
    ActivityDtls,
    DefectsSymptom,
    ServicePart,
    ServicePartDtls,
    ServiceInvoice,
    Complaint,
)


@admin.register(ConsProductReg)
class ConsProductRegAdmin(admin.ModelAdmin):
    list_display = ('Reg_id', 'consumer_id', 'prid', 'prod_no', 'warnt_cardno', 'Invoice_no', 'Invoice_date', 'warnt_enddate', 'Isactive')
    list_filter = ('Isactive', 'Invoice_date', 'warnt_enddate')
    search_fields = ('prod_no', 'warnt_cardno', 'Invoice_no', 'consumer_id__fname', 'consumer_id__email')


@admin.register(WorkStatus)
class WorkStatusAdmin(admin.ModelAdmin):
    list_display = ('Wo_stid', 'W_status')
    search_fields = ('W_status',)


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('W_orderid', 'Serv_req_no', 'reg_id', 'techid', 'w_stid', 'Inv_amt', 'cre_date', 'loc_type')
    list_filter = ('w_stid', 'loc_type', 'calltype', 'cre_date')
    search_fields = ('Serv_req_no', 'Siebel_no', 'techid__tech_name', 'reg_id__consumer_id__fname')


@admin.register(ActivityDtls)
class ActivityDtlsAdmin(admin.ModelAdmin):
    list_display = ('Activityno', 'W_orderid', 'act_status', 'Remark', 'cre_date')
    list_filter = ('act_status', 'cre_date')
    search_fields = ('Remark', 'W_orderid__W_orderid')


@admin.register(DefectsSymptom)
class DefectsSymptomAdmin(admin.ModelAdmin):
    list_display = ('defect_id', 'W_orderid', 'Symptom', 'Repaired', 'Status')
    list_filter = ('Status', 'Repaired', 'Condition')
    search_fields = ('defect_des', 'defect_bytech', 'Msg')


@admin.register(ServicePart)
class ServicePartAdmin(admin.ModelAdmin):
    list_display = ('servpartid', 'W_orderid', 'Reason', 'Position', 'Section', 'Repair')
    search_fields = ('Reason', 'Position', 'Section')


@admin.register(ServicePartDtls)
class ServicePartDtlsAdmin(admin.ModelAdmin):
    list_display = ('ser_p_dtid', 'servpartid', 'spareid', 'Qty')
    list_filter = ('spareid',)


@admin.register(ServiceInvoice)
class ServiceInvoiceAdmin(admin.ModelAdmin):
    list_display = ('Invoice_id', 'W_orderid', 'Inv_date', 'Amount')
    list_filter = ('Inv_date',)
    search_fields = ('W_orderid__W_orderid',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('com_id', 'Reg_id', 'Complaint', 'Status', 'com_date')
    list_filter = ('Status', 'com_date')
    search_fields = ('Complaint', 'Reply')

