from django.contrib import admin
from .models import State, District, ServCenter, ConsumerReg, Technician, AuthUser


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('statid', 'state')
    search_fields = ('state',)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('Distid', 'District', 'statid')
    list_filter = ('statid',)
    search_fields = ('District',)


@admin.register(ServCenter)
class ServCenterAdmin(admin.ModelAdmin):
    list_display = ('serv_centid', 'serv_cent', 'place', 'phone', 'mob', 'email', 'status')
    list_filter = ('status', 'statid', 'Distid')
    search_fields = ('serv_cent', 'place', 'email', 'Contact_per')


@admin.register(ConsumerReg)
class ConsumerRegAdmin(admin.ModelAdmin):
    list_display = ('consumer_id', 'fname', 'lname', 'mob', 'email', 'status', 'consumertype', 'regdate')
    list_filter = ('status', 'consumertype', 'statid')
    search_fields = ('fname', 'lname', 'email', 'mob', 'phone')


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('techid', 'tech_name', 'Mob', 'Email', 'Quali', 'Exp', 'Status')
    list_filter = ('Status', 'Gender', 'statid')
    search_fields = ('tech_name', 'Email', 'Mob')


@admin.register(AuthUser)
class AuthUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role')
    list_filter = ('role',)
    search_fields = ('username',)

