from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from accounts.models import State, District, ServCenter, AuthUser, Technician, ConsumerReg
from products.models import ProductCat, Product, SparePart
from services.models import WorkStatus, ConsProductReg, WorkOrder, ActivityDtls


class Command(BaseCommand):
    help = 'Seeds initial WorkStatus values, Admin user, and baseline master data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting initial data seeding for SmartCare Service Portal...'))

        # 1. Seed Work Statuses
        statuses = [
            'Pending',
            'Estimate Sent',
            'Assigned',
            'Spare Parts Pending',
            'Completed',
            'Irreparable',
            'Cancelled',
        ]
        for st in statuses:
            obj, created = WorkStatus.objects.get_or_create(W_status=st)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created WorkStatus: {st}'))

        # 2. Seed Admin in AuthUser
        admin_user, created = AuthUser.objects.get_or_create(
            username='admin',
            defaults={
                'password': make_password('admin123'),
                'role': 'Admin',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created default AuthUser: admin / admin123 (Role: Admin)'))
        else:
            admin_user.password = make_password('admin123')
            admin_user.role = 'Admin'
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Updated default AuthUser: admin / admin123'))

        # 3. Create Django superuser for /admin/ access if needed
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@smartcare.local', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created Django superuser: admin / admin123'))

        # 4. Seed baseline States & Districts
        geo_data = {
            'Kerala': ['Ernakulam', 'Thiruvananthapuram', 'Thrissur', 'Kozhikode', 'Kottayam', 'Palakkad', 'Kollam', 'Alappuzha'],
            'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Salem'],
            'Karnataka': ['Bengaluru', 'Mysuru', 'Mangaluru', 'Hubballi'],
        }

        for st_name, dist_list in geo_data.items():
            state_obj, _ = State.objects.get_or_create(state=st_name)
            for dist_name in dist_list:
                District.objects.get_or_create(District=dist_name, statid=state_obj)
        self.stdout.write(self.style.SUCCESS('Seeded baseline States and Districts'))

        # 5. Seed a primary Service Center
        kl_state = State.objects.filter(state='Kerala').first()
        ekm_dist = District.objects.filter(District='Ernakulam').first()
        if kl_state and ekm_dist:
            ServCenter.objects.get_or_create(
                username='sc_central',
                defaults={
                    'serv_cent': 'SmartCare Central Hub',
                    'statid': kl_state,
                    'Distid': ekm_dist,
                    'place': 'Kochi',
                    'pin': '682001',
                    'landmark': 'MG Road',
                    'Contact_per': 'Operations Manager',
                    'phone': '0484-2345678',
                    'mob': '9876543210',
                    'email': 'central@smartcare.com',
                    'pwd': make_password('center123'),
                    'status': 'Active'
                }
            )
            self.stdout.write(self.style.SUCCESS('Seeded central Service Center'))

        # 6. Seed Product Categories, Products, and Spare Parts
        cat_tv, _ = ProductCat.objects.get_or_create(category='Television')
        cat_ref, _ = ProductCat.objects.get_or_create(category='Refrigerator')
        cat_wm, _ = ProductCat.objects.get_or_create(category='Washing Machine')

        tv_prod, _ = Product.objects.get_or_create(
            srno='SN-TV-001',
            defaults={
                'pcatid': cat_tv,
                'prname': 'Smart LED TV 43"',
                'model': 'STV-43X',
                'price': 28500.0,
                'des': '4K Ultra HD Smart LED Display with HDR'
            }
        )

        ref_prod, _ = Product.objects.get_or_create(
            srno='SN-RF-002',
            defaults={
                'pcatid': cat_ref,
                'prname': 'Double Door Fridge',
                'model': 'RF-260D',
                'price': 31000.0,
                'des': 'Frost Free 260 Litres 3-Star Inverter Refrigerator'
            }
        )

        wm_prod, _ = Product.objects.get_or_create(
            srno='SN-WM-003',
            defaults={
                'pcatid': cat_wm,
                'prname': 'Front Load Washer',
                'model': 'WM-70FL',
                'price': 29500.0,
                'des': '7 kg Fully Automatic Front Load Washing Machine'
            }
        )

        # Spares for TV
        SparePart.objects.get_or_create(partsname='Power Supply Board', prid=tv_prod, defaults={'price': 1800.0, 'qty': 20})
        SparePart.objects.get_or_create(partsname='Main Motherboard', prid=tv_prod, defaults={'price': 3400.0, 'qty': 15})
        SparePart.objects.get_or_create(partsname='LED Backlight Strip', prid=tv_prod, defaults={'price': 750.0, 'qty': 30})

        # Spares for Fridge
        SparePart.objects.get_or_create(partsname='Compressor Relay', prid=ref_prod, defaults={'price': 650.0, 'qty': 25})
        SparePart.objects.get_or_create(partsname='Defrost Thermostat', prid=ref_prod, defaults={'price': 480.0, 'qty': 35})
        SparePart.objects.get_or_create(partsname='Thermostat Sensor', prid=ref_prod, defaults={'price': 350.0, 'qty': 40})

        # Spares for Washer
        SparePart.objects.get_or_create(partsname='Drain Pump Motor', prid=wm_prod, defaults={'price': 1250.0, 'qty': 18})
        SparePart.objects.get_or_create(partsname='Inlet Solenoid Valve', prid=wm_prod, defaults={'price': 600.0, 'qty': 25})
        SparePart.objects.get_or_create(partsname='Drive Belt', prid=wm_prod, defaults={'price': 420.0, 'qty': 40})

        # 7. Seed Default Technician (Rahul Kumar)
        tech_obj, _ = Technician.objects.get_or_create(
            Email='rahul.tech@smartcare.com',
            defaults={
                'tech_name': 'Rahul Kumar',
                'Address': 'Flat 4B, Smart Enclave, MG Road',
                'statid': kl_state,
                'Distid': ekm_dist,
                'Gender': 'Male',
                'Quali': 'Diploma in Electronics',
                'Exp': '5 Years',
                'Mob': '9876501234',
                'Status': 'Active'
            }
        )
        for u_name in ['rahul.tech', 'rahul.tech@smartcare.com']:
            u, _ = AuthUser.objects.get_or_create(username=u_name, defaults={'role': 'Technician', 'password': make_password('password123')})
            u.role = 'Technician'
            u.password = make_password('password123')
            u.save()
        self.stdout.write(self.style.SUCCESS('Seeded default Technician: rahul.tech / password123 (Rahul Kumar)'))

        # 8. Seed Default Consumer (Anjali Nair)
        consumer_obj, _ = ConsumerReg.objects.get_or_create(
            email='consumer@smartcare.com',
            defaults={
                'fname': 'Anjali',
                'lname': 'Nair',
                'dob': '1995-05-15',
                'address': 'Nair Villa, Panampilly Nagar',
                'statid': kl_state,
                'Distid': ekm_dist,
                'regmode': 'Online',
                'phone': '0484-2345678',
                'mob': '9876543211',
                'pin': '682036',
                'password': make_password('password123'),
                'remarks': 'Registered online',
                'status': 'Active',
                'consumertype': 'Regular'
            }
        )
        for u_name in ['consumer', 'consumer@smartcare.com']:
            u, _ = AuthUser.objects.get_or_create(username=u_name, defaults={'role': 'Consumer', 'password': make_password('password123')})
            u.role = 'Consumer'
            u.password = make_password('password123')
            u.save()
        self.stdout.write(self.style.SUCCESS('Seeded default Consumer: consumer / password123 (Anjali Nair)'))

        # 9. Seed Sample Registered Appliance & Work Order
        today = timezone.now().date()
        app_obj, _ = ConsProductReg.objects.get_or_create(
            prod_no=700101,
            defaults={
                'consumer_id': consumer_obj,
                'prid': ref_prod,
                'warnt_cardno': 500101,
                'Invoice_no': 900101,
                'Invoice_date': today - timedelta(days=60),
                'warnt_enddate': today + timedelta(days=305),
                'Isactive': 'Active'
            }
        )

        st_assigned = WorkStatus.objects.filter(W_status='Assigned').first()
        if app_obj and st_assigned and tech_obj:
            wo_obj, wo_created = WorkOrder.objects.get_or_create(
                Serv_req_no=10001,
                defaults={
                    'techid': tech_obj,
                    'reg_id': app_obj,
                    'cons_pdtid': app_obj.Reg_id,
                    'prod_no': app_obj.prod_no,
                    'w_stid': st_assigned,
                    'loc_type': 'Home Service',
                    'calltype': 'Repair',
                    'jobsheet_type': 'Standard',
                    'Inv_amt': 0.0,
                    'prom_del_date': today + timedelta(days=2)
                }
            )
            if wo_created:
                ActivityDtls.objects.get_or_create(
                    W_orderid=wo_obj,
                    act_status='Assigned',
                    Remark='Initial complaint registered: Cooling issue reported. Technician Rahul Kumar assigned for diagnostic visit.'
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded all initial data!'))

