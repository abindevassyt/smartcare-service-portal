from django.db import models
from accounts.models import ConsumerReg, Technician
from products.models import Product, SparePart


class ConsProductReg(models.Model):
    Reg_id = models.AutoField(primary_key=True)
    consumer_id = models.ForeignKey(
        ConsumerReg,
        on_delete=models.CASCADE,
        db_column='consumer_id',
        related_name='registered_products'
    )
    prid = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        db_column='prid',
        related_name='registered_instances'
    )
    prod_no = models.IntegerField()
    warnt_cardno = models.IntegerField()
    Invoice_no = models.IntegerField()
    Invoice_date = models.DateField()
    warnt_enddate = models.DateField()
    Isactive = models.CharField(max_length=10, default='Pending')
    clm_before = models.DateField(null=True, blank=True)
    Reg_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'cons_product_reg'
        verbose_name = 'Consumer Product Registration'
        verbose_name_plural = 'Consumer Product Registrations'
        ordering = ['-Reg_date']

    def __str__(self):
        return f"Reg #{self.Reg_id} - {self.prid.prname} (S/N: {self.prod_no})"


class WorkStatus(models.Model):
    Wo_stid = models.AutoField(primary_key=True)
    W_status = models.CharField(max_length=20)

    class Meta:
        db_table = 'work_status'
        verbose_name = 'Work Status'
        verbose_name_plural = 'Work Statuses'
        ordering = ['Wo_stid']

    def __str__(self):
        return self.W_status


class WorkOrder(models.Model):
    W_orderid = models.AutoField(primary_key=True)
    Siebel_no = models.IntegerField(null=True, blank=True)
    techid = models.ForeignKey(
        Technician,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='techid',
        related_name='work_orders'
    )
    Serv_req_no = models.IntegerField()
    reg_id = models.ForeignKey(
        ConsProductReg,
        on_delete=models.CASCADE,
        db_column='reg_id',
        related_name='work_orders'
    )
    cons_pdtid = models.IntegerField()
    prod_no = models.IntegerField()
    prom_del_date = models.DateField(null=True, blank=True)
    w_stid = models.ForeignKey(
        WorkStatus,
        on_delete=models.PROTECT,
        db_column='w_stid',
        related_name='work_orders'
    )
    Inv_amt = models.FloatField(default=0.0)
    refnd_amt = models.FloatField(default=0.0)
    cre_date = models.DateField(auto_now_add=True)
    modi_date = models.DateField(auto_now=True)
    close_date = models.DateField(null=True, blank=True)
    jobsheet_type = models.CharField(max_length=20, default='Standard')
    calltype = models.CharField(max_length=20, default='Repair')
    loc_type = models.CharField(max_length=20, default='Home Service')

    class Meta:
        db_table = 'Work_order'
        verbose_name = 'Work Order'
        verbose_name_plural = 'Work Orders'
        ordering = ['-W_orderid']

    def __str__(self):
        return f"WO #{self.W_orderid} (Req: {self.Serv_req_no}) - {self.w_stid.W_status}"


class ActivityDtls(models.Model):
    Activityno = models.AutoField(primary_key=True)
    W_orderid = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        db_column='W_orderid',
        related_name='activities'
    )
    act_status = models.CharField(max_length=15)
    Remark = models.CharField(max_length=100)
    cre_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'Activity_dtls'
        verbose_name = 'Activity Detail'
        verbose_name_plural = 'Activity Details'
        ordering = ['-Activityno']

    def __str__(self):
        return f"Activity #{self.Activityno} (WO #{self.W_orderid_id}): {self.act_status}"


class DefectsSymptom(models.Model):
    defect_id = models.AutoField(primary_key=True)
    W_orderid = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        db_column='W_orderid',
        related_name='defects'
    )
    defect_bytech = models.CharField(max_length=100)
    defect_des = models.CharField(max_length=100)
    Condition = models.CharField(max_length=20)
    Symptom = models.CharField(max_length=20)
    Actual_rep = models.CharField(max_length=20)
    Faulty = models.CharField(max_length=20)
    Repaired = models.CharField(max_length=20)
    Msg = models.CharField(max_length=100)
    Spareused = models.CharField(max_length=20)
    Status = models.CharField(max_length=20)

    class Meta:
        db_table = 'Defects_symptom'
        verbose_name = 'Defects & Symptom'
        verbose_name_plural = 'Defects & Symptoms'

    def __str__(self):
        return f"Defect #{self.defect_id} (WO #{self.W_orderid_id}) - {self.Symptom}"


class ServicePart(models.Model):
    servpartid = models.AutoField(primary_key=True)
    W_orderid = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        db_column='W_orderid',
        related_name='service_parts'
    )
    Reason = models.CharField(max_length=20)
    Position = models.CharField(max_length=20)
    Section = models.CharField(max_length=20)
    Defects = models.CharField(max_length=20)
    Repair = models.CharField(max_length=20)

    class Meta:
        db_table = 'service_parts'
        verbose_name = 'Service Part'
        verbose_name_plural = 'Service Parts'

    def __str__(self):
        return f"ServicePart #{self.servpartid} (WO #{self.W_orderid_id})"


class ServicePartDtls(models.Model):
    ser_p_dtid = models.AutoField(primary_key=True)
    servpartid = models.ForeignKey(
        ServicePart,
        on_delete=models.CASCADE,
        db_column='servpartid',
        related_name='details'
    )
    spareid = models.ForeignKey(
        SparePart,
        on_delete=models.PROTECT,
        db_column='spareid',
        related_name='service_part_details'
    )
    Qty = models.IntegerField(default=1)

    class Meta:
        db_table = 'Service_parts_dtls'
        verbose_name = 'Service Part Detail'
        verbose_name_plural = 'Service Part Details'

    def __str__(self):
        return f"{self.spareid.partsname} x {self.Qty} for ServicePart #{self.servpartid_id}"


class ServiceInvoice(models.Model):
    Invoice_id = models.AutoField(primary_key=True)
    W_orderid = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        db_column='W_orderid',
        related_name='invoices'
    )
    Inv_date = models.DateField(auto_now_add=True)
    Amount = models.FloatField(default=0.0)

    class Meta:
        db_table = 'Service_Invoice'
        verbose_name = 'Service Invoice'
        verbose_name_plural = 'Service Invoices'
        ordering = ['-Invoice_id']

    def __str__(self):
        return f"Invoice #{self.Invoice_id} (WO #{self.W_orderid_id}) - ₹{self.Amount:.2f}"


class Complaint(models.Model):
    com_id = models.AutoField(primary_key=True)
    com_date = models.DateField(auto_now_add=True)
    Reg_id = models.ForeignKey(
        ConsProductReg,
        on_delete=models.CASCADE,
        db_column='Reg_id',
        related_name='complaints'
    )
    Complaint = models.CharField(max_length=100)
    Reply = models.CharField(max_length=100, blank=True, default='')
    Status = models.CharField(max_length=20, default='Open')

    class Meta:
        db_table = 'Complaints'
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'
        ordering = ['-com_id']

    def __str__(self):
        return f"Complaint #{self.com_id} ({self.Status})"

