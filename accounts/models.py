from django.db import models


class State(models.Model):
    statid = models.AutoField(primary_key=True)
    state = models.CharField(max_length=20)

    class Meta:
        db_table = 'state'
        verbose_name = 'State'
        verbose_name_plural = 'States'
        ordering = ['state']

    def __str__(self):
        return self.state


class District(models.Model):
    Distid = models.AutoField(primary_key=True)
    District = models.CharField(max_length=20)
    statid = models.ForeignKey(
        State,
        on_delete=models.CASCADE,
        db_column='statid',
        related_name='districts'
    )

    class Meta:
        db_table = 'District'
        verbose_name = 'District'
        verbose_name_plural = 'Districts'
        ordering = ['District']

    def __str__(self):
        return f"{self.District} ({self.statid.state})"


class ServCenter(models.Model):
    serv_centid = models.AutoField(primary_key=True)
    serv_cent = models.CharField(max_length=20)
    statid = models.ForeignKey(State, on_delete=models.PROTECT, db_column='statid')
    Distid = models.ForeignKey(District, on_delete=models.PROTECT, db_column='Distid')
    place = models.CharField(max_length=20)
    pin = models.CharField(max_length=10)
    landmark = models.CharField(max_length=20)
    Contact_per = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    mob = models.CharField(max_length=20)
    email = models.EmailField(max_length=30)
    username = models.CharField(max_length=20, unique=True)
    pwd = models.CharField(max_length=128)
    status = models.CharField(max_length=20, default='Active')

    class Meta:
        db_table = 'serv_center'
        verbose_name = 'Service Center'
        verbose_name_plural = 'Service Centers'

    def __str__(self):
        return f"{self.serv_cent} - {self.place}"


class ConsumerReg(models.Model):
    consumer_id = models.AutoField(primary_key=True)
    fname = models.CharField(max_length=20)
    lname = models.CharField(max_length=20)
    dob = models.DateField()
    address = models.CharField(max_length=30)
    statid = models.ForeignKey(State, on_delete=models.PROTECT, db_column='statid')
    Distid = models.ForeignKey(District, on_delete=models.PROTECT, db_column='Distid')
    regmode = models.CharField(max_length=20, default='Online')
    phone = models.CharField(max_length=20)
    mob = models.CharField(max_length=20)
    pin = models.CharField(max_length=8)
    email = models.EmailField(max_length=30, unique=True)
    password = models.CharField(max_length=128)
    remarks = models.CharField(max_length=30, blank=True, null=True)
    status = models.CharField(max_length=20, default='Pending')
    regdate = models.DateField(auto_now_add=True)
    consumertype = models.CharField(max_length=20, default='Regular')

    class Meta:
        db_table = 'Consumer_reg'
        verbose_name = 'Consumer Registration'
        verbose_name_plural = 'Consumer Registrations'

    def __str__(self):
        return f"{self.fname} {self.lname} ({self.email})"


class Technician(models.Model):
    techid = models.AutoField(primary_key=True)
    tech_name = models.CharField(max_length=30)
    Address = models.CharField(max_length=100)
    statid = models.ForeignKey(State, on_delete=models.PROTECT, db_column='statid')
    Distid = models.ForeignKey(District, on_delete=models.PROTECT, db_column='Distid')
    Gender = models.CharField(max_length=6)
    Quali = models.CharField(max_length=20)
    Exp = models.CharField(max_length=10)
    Mob = models.CharField(max_length=20)
    Email = models.EmailField(max_length=30, unique=True)
    Status = models.CharField(max_length=20, default='Active')

    class Meta:
        db_table = 'Technicians'
        verbose_name = 'Technician'
        verbose_name_plural = 'Technicians'

    def __str__(self):
        return f"{self.tech_name} ({self.Mob})"


class AuthUser(models.Model):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Technician', 'Technician'),
        ('Consumer', 'Consumer'),
    ]

    username = models.CharField(max_length=30, primary_key=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        db_table = 'accounts_authuser'
        verbose_name = 'Auth User'
        verbose_name_plural = 'Auth Users'

    def __str__(self):
        return f"{self.username} [{self.role}]"

