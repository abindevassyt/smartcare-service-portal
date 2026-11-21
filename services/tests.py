from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password

from accounts.models import AuthUser, State, District, ConsumerReg, Technician, ServCenter
from products.models import ProductCat, Product, SparePart
from services.models import (
    WorkStatus, ConsProductReg, WorkOrder, ActivityDtls, Complaint,
    DefectsSymptom, ServicePart, ServicePartDtls, ServiceInvoice
)


class Stage5AdminModuleTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Admin Auth User
        self.admin_user = AuthUser.objects.create(
            username='admin',
            password=make_password('admin123'),
            role='Admin'
        )

        # Baseline geo data
        self.state = State.objects.create(state='Kerala')
        self.dist = District.objects.create(District='Ernakulam', statid=self.state)

        # Baseline consumer
        self.consumer = ConsumerReg.objects.create(
            fname='Abin',
            lname='Devassy',
            dob='1998-08-10',
            address='Aluva, Kochi',
            statid=self.state,
            Distid=self.dist,
            phone='0484223344',
            mob='9895012345',
            pin='683101',
            email='abin@example.com',
            password=make_password('pass123'),
            status='Active'
        )

        # Baseline product & spare
        self.cat = ProductCat.objects.create(category='Television')
        self.product = Product.objects.create(
            pcatid=self.cat,
            prname='Smart LED TV 43',
            model='STV-43X',
            price=28000.0,
            srno='SN-TV-101',
            des='Full HD Smart TV'
        )
        self.spare = SparePart.objects.create(
            prid=self.product,
            partsname='Power Supply',
            price=1500.0,
            qty=10
        )

        # Baseline work statuses
        self.st_pending = WorkStatus.objects.create(W_status='Pending')
        self.st_assigned = WorkStatus.objects.create(W_status='Assigned')
        self.st_completed = WorkStatus.objects.create(W_status='Completed')

        # Baseline Technician
        self.tech = Technician.objects.create(
            tech_name='Rahul Ramesh',
            Address='Palarivattom, Kochi',
            statid=self.state,
            Distid=self.dist,
            Gender='Male',
            Quali='Diploma Electronics',
            Exp='3 Years',
            Mob='9847112233',
            Email='rahul.tech@smartcare.com',
            Status='Active'
        )
        AuthUser.objects.create(
            username=self.tech.Email,
            password=make_password('tech123'),
            role='Technician'
        )

        # Session login as Admin
        session = self.client.session
        session['username'] = 'admin'
        session['role'] = 'Admin'
        session.save()

    def test_admin_work_orders_view(self):
        # Register appliance with active warranty
        today = timezone.now().date()
        reg_warranty = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=1001,
            warnt_cardno=5001,
            Invoice_no=9001,
            Invoice_date=today - timedelta(days=60),
            warnt_enddate=today + timedelta(days=300),
            Isactive='Active'
        )

        # Create Work Order
        order = WorkOrder.objects.create(
            Serv_req_no=10001,
            reg_id=reg_warranty,
            cons_pdtid=reg_warranty.Reg_id,
            prod_no=1001,
            w_stid=self.st_pending,
            loc_type='Home Service',
            calltype='Repair',
            jobsheet_type='Standard'
        )

        response = self.client.get(reverse('services:admin_work_orders'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'In Warranty')
        self.assertContains(response, '10001')

    def test_admin_assign_work_order(self):
        today = timezone.now().date()
        reg_expired = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=1002,
            warnt_cardno=5002,
            Invoice_no=9002,
            Invoice_date=today - timedelta(days=700),
            warnt_enddate=today - timedelta(days=50),
            Isactive='Active'
        )
        order = WorkOrder.objects.create(
            Serv_req_no=10002,
            reg_id=reg_expired,
            cons_pdtid=reg_expired.Reg_id,
            prod_no=1002,
            w_stid=self.st_pending,
            loc_type='Home Service',
            calltype='Repair',
            jobsheet_type='Standard'
        )

        # Admin assigns technician and sets repair estimate
        assign_data = {
            'techid': str(self.tech.techid),
            'w_stid': str(self.st_assigned.Wo_stid),
            'Inv_amt': '850.00',
            'prom_del_date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
            'loc_type': 'Home Service',
            'calltype': 'Repair',
            'jobsheet_type': 'Standard',
            'remark': 'Technician assigned for on-site inspection.'
        }
        res = self.client.post(reverse('services:admin_assign_work_order', args=[order.W_orderid]), assign_data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify WorkOrder was updated
        order.refresh_from_db()
        self.assertEqual(order.techid, self.tech)
        self.assertEqual(order.w_stid, self.st_assigned)
        self.assertEqual(order.Inv_amt, 850.00)

        # Verify Activity Log was recorded
        act = ActivityDtls.objects.filter(W_orderid=order).first()
        self.assertIsNotNone(act)
        self.assertEqual(act.act_status, 'Assigned')
        self.assertIn('Technician assigned', act.Remark)

    def test_admin_complaints_reply(self):
        reg = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=1003,
            warnt_cardno=5003,
            Invoice_no=9003,
            Invoice_date=timezone.now().date(),
            warnt_enddate=timezone.now().date() + timedelta(days=365),
            Isactive='Active'
        )
        complaint = Complaint.objects.create(
            Reg_id=reg,
            Complaint='Screen flicker after 20 minutes of usage',
            Status='Open'
        )

        reply_data = {
            'Reply': 'We have dispatched technician Rahul to inspect your panel tomorrow.',
            'Status': 'Resolved'
        }
        res = self.client.post(reverse('services:admin_reply_complaint', args=[complaint.com_id]), reply_data, follow=True)
        self.assertEqual(res.status_code, 200)

        complaint.refresh_from_db()
        self.assertEqual(complaint.Status, 'Resolved')
        self.assertIn('dispatched technician Rahul', complaint.Reply)


class Stage6ConsumerModuleTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.state = State.objects.create(state='Kerala')
        self.dist = District.objects.create(District='Ernakulam', statid=self.state)

        self.consumer = ConsumerReg.objects.create(
            fname='Abin',
            lname='Devassy',
            dob='1998-08-10',
            address='Aluva, Kochi',
            statid=self.state,
            Distid=self.dist,
            phone='0484223344',
            mob='9895012345',
            pin='683101',
            email='abin.consumer@smartcare.com',
            password=make_password('pass123'),
            status='Active'
        )
        self.auth_user = AuthUser.objects.create(
            username=self.consumer.email,
            password=make_password('pass123'),
            role='Consumer'
        )

        self.cat = ProductCat.objects.create(category='Washing Machine')
        self.product = Product.objects.create(
            pcatid=self.cat,
            prname='Front Load 8kg',
            model='WM-FL800',
            price=32000.0,
            srno='WM-SN-8800',
            des='Fully Automatic Washing Machine'
        )

        self.st_pending = WorkStatus.objects.create(W_status='Pending')
        self.st_completed = WorkStatus.objects.create(W_status='Completed')
        self.st_cancelled = WorkStatus.objects.create(W_status='Cancelled')

        # Log in as consumer
        session = self.client.session
        session['username'] = self.consumer.email
        session['role'] = 'Consumer'
        session['user_id'] = self.consumer.consumer_id
        session['name'] = f"{self.consumer.fname} {self.consumer.lname}"
        session.save()

    def test_consumer_register_product_and_activation_gate(self):
        today = timezone.now().date()
        reg_data = {
            'prid': str(self.product.prid),
            'prod_no': '90881',
            'warnt_cardno': '77665',
            'Invoice_no': '4411',
            'Invoice_date': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
            'warnt_enddate': (today + timedelta(days=335)).strftime('%Y-%m-%d'),
        }
        res = self.client.post(reverse('services:consumer_register_product'), reg_data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Verify product is registered with status 'Pending' (Activation Gate)
        reg = ConsProductReg.objects.filter(consumer_id=self.consumer, prod_no=90881).first()
        self.assertIsNotNone(reg)
        self.assertEqual(reg.Isactive, 'Pending')

        # Attempt to book service on Pending appliance -> Activation Gate must reject
        book_data = {
            'reg_id': str(reg.Reg_id),
            'loc_type': 'Home Service',
            'calltype': 'Repair',
            'issue_des': 'Drain pump not working properly',
        }
        res_book = self.client.post(reverse('services:consumer_book_service'), book_data, follow=True)
        self.assertEqual(res_book.status_code, 200)
        self.assertContains(res_book, 'pending technician verification')
        # Ensure no work order created
        self.assertEqual(WorkOrder.objects.filter(reg_id=reg).count(), 0)

        # Simulate activation by technician / admin
        reg.Isactive = 'Active'
        reg.save()

        # Re-attempt booking service on Active appliance -> Must succeed
        res_book2 = self.client.post(reverse('services:consumer_book_service'), book_data, follow=True)
        self.assertEqual(res_book2.status_code, 200)
        self.assertContains(res_book2, 'Repair request raised successfully')

        # Check work order creation
        order = WorkOrder.objects.filter(reg_id=reg).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.w_stid, self.st_pending)
        self.assertEqual(order.loc_type, 'Home Service')

    def test_consumer_track_orders_and_estimate_response(self):
        today = timezone.now().date()
        reg = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=90882,
            warnt_cardno=77666,
            Invoice_no=9901,
            Invoice_date=today - timedelta(days=500),
            warnt_enddate=today - timedelta(days=100),
            Isactive='Active'
        )
        order = WorkOrder.objects.create(
            Serv_req_no=20001,
            reg_id=reg,
            cons_pdtid=reg.Reg_id,
            prod_no=90882,
            w_stid=self.st_pending,
            loc_type='Home Service',
            calltype='Repair',
            Inv_amt=1250.00
        )

        # Track orders list
        res_list = self.client.get(reverse('services:consumer_track_orders'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, '20001')

        # Track order detail
        res_detail = self.client.get(reverse('services:consumer_track_order_detail', args=[order.W_orderid]))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, '20001')
        self.assertContains(res_detail, 'Accept Estimate')

        # Consumer approves estimate
        res_approve = self.client.post(reverse('services:consumer_respond_estimate', args=[order.W_orderid]), {'action': 'accept'}, follow=True)
        self.assertEqual(res_approve.status_code, 200)

        # Verify activity log
        log = ActivityDtls.objects.filter(W_orderid=order, act_status='Assigned').first()
        self.assertIsNotNone(log)
        self.assertIn('accepted', log.Remark.lower())


class Stage7TechnicianModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        self.state = State.objects.create(state='Kerala')
        self.dist = District.objects.create(District='Ernakulam', statid=self.state)

        # Baseline Technician & AuthUser
        self.tech = Technician.objects.create(
            tech_name='Manoj Kumar',
            Address='Kaloor, Kochi',
            statid=self.state,
            Distid=self.dist,
            Gender='Male',
            Quali='B.Tech Electronics',
            Exp='5 Years',
            Mob='9847998877',
            Email='manoj.tech@smartcare.com',
            Status='Active'
        )
        self.tech_user = AuthUser.objects.create(
            username=self.tech.Email,
            password=make_password('tech123'),
            role='Technician'
        )

        # Consumer
        self.consumer = ConsumerReg.objects.create(
            fname='Kiran',
            lname='Babu',
            dob='1995-04-12',
            address='Edappally, Kochi',
            statid=self.state,
            Distid=self.dist,
            phone='0484556677',
            mob='9846112233',
            pin='682024',
            email='kiran.babu@example.com',
            password=make_password('kiran123'),
            status='Pending'
        )

        # Product & Spares
        self.cat = ProductCat.objects.create(category='Refrigerator')
        self.product = Product.objects.create(
            pcatid=self.cat,
            prname='Double Door 340L',
            model='RF-DD340',
            price=38000.0,
            srno='RF-SN-9901',
            des='Inverter Frost-Free Refrigerator'
        )
        self.spare_relay = SparePart.objects.create(
            prid=self.product,
            partsname='Starter Relay',
            price=450.0,
            qty=5
        )
        self.spare_thermostat = SparePart.objects.create(
            prid=self.product,
            partsname='Thermostat Unit',
            price=850.0,
            qty=3
        )

        # Work Statuses
        self.st_pending = WorkStatus.objects.create(W_status='Pending')
        self.st_assigned = WorkStatus.objects.create(W_status='Assigned')
        self.st_inprogress = WorkStatus.objects.create(W_status='In Progress')
        self.st_completed = WorkStatus.objects.create(W_status='Completed')
        self.st_irrep = WorkStatus.objects.create(W_status='Irreparable')

        # Log in as Technician
        session = self.client.session
        session['username'] = self.tech.Email
        session['role'] = 'Technician'
        session['name'] = self.tech.tech_name
        session.save()

    def test_tech_activation_queues(self):
        # 1. Activate Consumer
        self.assertEqual(self.consumer.status, 'Pending')
        res_c = self.client.post(
            reverse('accounts:tech_activate_consumer_toggle', args=[self.consumer.consumer_id]),
            follow=True
        )
        self.assertEqual(res_c.status_code, 200)
        self.consumer.refresh_from_db()
        self.assertEqual(self.consumer.status, 'Active')

        # 2. Activate Consumer Product
        prod_reg = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=88201,
            warnt_cardno=11223,
            Invoice_no=5544,
            Invoice_date=self.today - timedelta(days=90),
            warnt_enddate=self.today + timedelta(days=275),
            Isactive='Pending'
        )
        self.assertEqual(prod_reg.Isactive, 'Pending')
        res_p = self.client.post(
            reverse('services:tech_activate_product_toggle', args=[prod_reg.Reg_id]),
            follow=True
        )
        self.assertEqual(res_p.status_code, 200)
        prod_reg.refresh_from_db()
        self.assertEqual(prod_reg.Isactive, 'Active')

    def test_tech_diagnostics_and_spare_stock_deduction(self):
        reg = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=88202,
            warnt_cardno=11224,
            Invoice_no=5545,
            Invoice_date=self.today - timedelta(days=600),
            warnt_enddate=self.today - timedelta(days=100),
            Isactive='Active'
        )
        order = WorkOrder.objects.create(
            Serv_req_no=30001,
            techid=self.tech,
            reg_id=reg,
            cons_pdtid=reg.Reg_id,
            prod_no=88202,
            w_stid=self.st_assigned,
            loc_type='Home Service',
            calltype='Repair',
            jobsheet_type='Standard'
        )

        # 1. Update status to In Progress
        res_st = self.client.post(
            reverse('services:tech_work_order_detail', args=[order.W_orderid]),
            {
                'action': 'update_status',
                'status_id': str(self.st_inprogress.Wo_stid),
                'jobsheet_type': 'Standard',
                'prom_del_date': (self.today + timedelta(days=2)).strftime('%Y-%m-%d'),
                'remark': 'Technician arrived on-site and began diagnosis.'
            },
            follow=True
        )
        self.assertEqual(res_st.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.w_stid, self.st_inprogress)

        # 2. Log Defect Diagnostics
        defect_data = {
            'action': 'log_defect',
            'defect_bytech': 'Faulty Starter Relay',
            'defect_des': 'Compressor fails to start, clicking sound from relay.',
            'Condition': 'Fair',
            'Symptom': 'Clicking Sound / No Cooling',
            'Actual_rep': 'Relay Replacement',
            'Faulty': 'Yes',
            'Repaired': 'Yes',
            'Msg': 'Advised clean airflow around compressor coils.',
            'Spareused': 'Yes',
            'Status': 'Diagnosed'
        }
        res_def = self.client.post(
            reverse('services:tech_work_order_detail', args=[order.W_orderid]),
            defect_data,
            follow=True
        )
        self.assertEqual(res_def.status_code, 200)
        defect = DefectsSymptom.objects.filter(W_orderid=order).first()
        self.assertIsNotNone(defect)
        self.assertEqual(defect.defect_bytech, 'Faulty Starter Relay')

        # 3. Test Insufficient Stock rejection
        res_fail_spare = self.client.post(
            reverse('services:tech_work_order_detail', args=[order.W_orderid]),
            {
                'action': 'add_spare_part',
                'spare_id': str(self.spare_relay.spareid),
                'qty': '99',
                'reason': 'Replacement',
                'position': 'Internal',
                'section': 'Compressor',
                'defects': 'Burnt',
                'repair': 'Replaced'
            },
            follow=True
        )
        self.assertContains(res_fail_spare, 'Insufficient inventory')
        self.spare_relay.refresh_from_db()
        self.assertEqual(self.spare_relay.qty, 5)  # Stock untouched

        # 4. Successful stock deduction
        res_ok_spare = self.client.post(
            reverse('services:tech_work_order_detail', args=[order.W_orderid]),
            {
                'action': 'add_spare_part',
                'spare_id': str(self.spare_relay.spareid),
                'qty': '2',
                'reason': 'Replacement',
                'position': 'Internal',
                'section': 'Compressor',
                'defects': 'Burnt',
                'repair': 'Replaced'
            },
            follow=True
        )
        self.assertEqual(res_ok_spare.status_code, 200)
        self.spare_relay.refresh_from_db()
        self.assertEqual(self.spare_relay.qty, 3)  # Deducted 5 - 2 = 3

        part_dtls = ServicePartDtls.objects.filter(spareid=self.spare_relay).first()
        self.assertIsNotNone(part_dtls)
        self.assertEqual(part_dtls.Qty, 2)

    def test_automated_billing_engine_rules(self):
        # Case A: Rule 1 - In-Warranty Repaired -> Amount = 0.00
        reg_in_warnt = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=88203,
            warnt_cardno=11225,
            Invoice_no=5546,
            Invoice_date=self.today - timedelta(days=30),
            warnt_enddate=self.today + timedelta(days=335),
            Isactive='Active'
        )
        order_in = WorkOrder.objects.create(
            Serv_req_no=30002,
            techid=self.tech,
            reg_id=reg_in_warnt,
            cons_pdtid=reg_in_warnt.Reg_id,
            prod_no=88203,
            w_stid=self.st_inprogress,
            loc_type='Home Service',
            calltype='Repair'
        )
        # Allocate part under warranty
        sp = ServicePart.objects.create(W_orderid=order_in, Reason='Warranty', Position='Internal', Section='Main', Defects='Wear', Repair='Replaced')
        ServicePartDtls.objects.create(servpartid=sp, spareid=self.spare_relay, Qty=1)

        res_inv1 = self.client.post(
            reverse('services:tech_generate_invoice', args=[order_in.W_orderid]),
            {'repaired': 'Yes', 'service_fee': '350.0'},
            follow=True
        )
        self.assertEqual(res_inv1.status_code, 200)
        inv1 = ServiceInvoice.objects.get(W_orderid=order_in)
        self.assertEqual(inv1.Amount, 0.0)
        order_in.refresh_from_db()
        self.assertEqual(order_in.Inv_amt, 0.0)
        self.assertEqual(order_in.w_stid, self.st_completed)

        # Case B: Rule 2 - Out-of-Warranty & Irreparable -> Amount = 0.00, Status = Irreparable
        reg_out_warnt = ConsProductReg.objects.create(
            consumer_id=self.consumer,
            prid=self.product,
            prod_no=88204,
            warnt_cardno=11226,
            Invoice_no=5547,
            Invoice_date=self.today - timedelta(days=600),
            warnt_enddate=self.today - timedelta(days=100),
            Isactive='Active'
        )
        order_irrep = WorkOrder.objects.create(
            Serv_req_no=30003,
            techid=self.tech,
            reg_id=reg_out_warnt,
            cons_pdtid=reg_out_warnt.Reg_id,
            prod_no=88204,
            w_stid=self.st_inprogress,
            loc_type='Home Service',
            calltype='Repair'
        )
        res_inv2 = self.client.post(
            reverse('services:tech_generate_invoice', args=[order_irrep.W_orderid]),
            {'repaired': 'No', 'service_fee': '350.0'},
            follow=True
        )
        self.assertEqual(res_inv2.status_code, 200)
        inv2 = ServiceInvoice.objects.get(W_orderid=order_irrep)
        self.assertEqual(inv2.Amount, 0.0)
        order_irrep.refresh_from_db()
        self.assertEqual(order_irrep.w_stid, self.st_irrep)

        # Case C: Rule 3 - Out-of-Warranty & Repaired -> Amount = Parts (450*2 = 900) + ServiceFee (350) = 1250.00
        order_out_rep = WorkOrder.objects.create(
            Serv_req_no=30004,
            techid=self.tech,
            reg_id=reg_out_warnt,
            cons_pdtid=reg_out_warnt.Reg_id,
            prod_no=88204,
            w_stid=self.st_inprogress,
            loc_type='Home Service',
            calltype='Repair'
        )
        sp_out = ServicePart.objects.create(W_orderid=order_out_rep, Reason='Chargeable', Position='Internal', Section='Main', Defects='Burnt', Repair='Replaced')
        ServicePartDtls.objects.create(servpartid=sp_out, spareid=self.spare_relay, Qty=2) # 2 * 450 = 900.0

        res_inv3 = self.client.post(
            reverse('services:tech_generate_invoice', args=[order_out_rep.W_orderid]),
            {'repaired': 'Yes', 'service_fee': '350.0'},
            follow=True
        )
        self.assertEqual(res_inv3.status_code, 200)
        inv3 = ServiceInvoice.objects.get(W_orderid=order_out_rep)
        self.assertEqual(inv3.Amount, 1250.0)  # 900 + 350
        order_out_rep.refresh_from_db()
        self.assertEqual(order_out_rep.Inv_amt, 1250.0)
        self.assertEqual(order_out_rep.w_stid, self.st_completed)


class Stage8ReportsAndInvoicingTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        self.state = State.objects.create(state='Kerala')
        self.dist = District.objects.create(District='Ernakulam', statid=self.state)

        # Admin
        self.admin = AuthUser.objects.create(
            username='admin_reports',
            password=make_password('admin123'),
            role='Admin'
        )

        # Technician
        self.tech = Technician.objects.create(
            tech_name='Vipin Varghese',
            Address='Palarivattom, Kochi',
            statid=self.state,
            Distid=self.dist,
            Gender='Male',
            Quali='Diploma Electronics',
            Exp='4 Years',
            Mob='9847123999',
            Email='vipin.tech@smartcare.com',
            Status='Active'
        )
        self.tech_user = AuthUser.objects.create(
            username=self.tech.Email,
            password=make_password('tech123'),
            role='Technician'
        )

        # Consumer 1 (Owner)
        self.consumer1 = ConsumerReg.objects.create(
            fname='Thomas',
            lname='Mathew',
            dob='1992-06-15',
            address='Kakkanad, Kochi',
            statid=self.state,
            Distid=self.dist,
            phone='0484334455',
            mob='9846001122',
            pin='682030',
            email='thomas.m@example.com',
            password=make_password('pass123'),
            status='Active'
        )
        AuthUser.objects.create(
            username=self.consumer1.email,
            password=make_password('pass123'),
            role='Consumer'
        )

        # Consumer 2 (Other Consumer)
        self.consumer2 = ConsumerReg.objects.create(
            fname='Sneha',
            lname='Paul',
            dob='1994-09-20',
            address='Aluva, Kochi',
            statid=self.state,
            Distid=self.dist,
            phone='0484998877',
            mob='9846334455',
            pin='683101',
            email='sneha.p@example.com',
            password=make_password('pass123'),
            status='Active'
        )
        AuthUser.objects.create(
            username=self.consumer2.email,
            password=make_password('pass123'),
            role='Consumer'
        )

        # Product & Spares
        self.cat = ProductCat.objects.create(category='Microwave Oven')
        self.product = Product.objects.create(
            pcatid=self.cat,
            prname='Convection 28L',
            model='MW-CV28',
            price=16000.0,
            srno='MW-SN-1100',
            des='Convection Microwave Oven'
        )
        self.spare = SparePart.objects.create(
            prid=self.product,
            partsname='Magnetron Tube',
            price=1800.0,
            qty=4
        )

        self.st_completed = WorkStatus.objects.create(W_status='Completed')

        # Appliance & Work Order
        self.reg = ConsProductReg.objects.create(
            consumer_id=self.consumer1,
            prid=self.product,
            prod_no=77201,
            warnt_cardno=33445,
            Invoice_no=6655,
            Invoice_date=self.today - timedelta(days=600),
            warnt_enddate=self.today - timedelta(days=235),
            Isactive='Active'
        )
        self.order = WorkOrder.objects.create(
            Serv_req_no=40001,
            techid=self.tech,
            reg_id=self.reg,
            cons_pdtid=self.reg.Reg_id,
            prod_no=77201,
            w_stid=self.st_completed,
            loc_type='Home Service',
            calltype='Repair',
            jobsheet_type='Standard',
            Inv_amt=2150.0,
            close_date=self.today
        )

        # Spare part used
        sp = ServicePart.objects.create(W_orderid=self.order, Reason='Burnt', Position='Internal', Section='High Voltage', Defects='No Heat', Repair='Replaced')
        ServicePartDtls.objects.create(servpartid=sp, spareid=self.spare, Qty=1)

        # Invoice
        self.invoice = ServiceInvoice.objects.create(
            W_orderid=self.order,
            Inv_date=self.today,
            Amount=2150.0
        )

    def test_printable_service_invoice_access_and_render(self):
        # 1. Accessible by Admin
        session = self.client.session
        session['username'] = self.admin.username
        session['role'] = 'Admin'
        session.save()

        res_admin = self.client.get(reverse('services:print_service_invoice', args=[self.invoice.Invoice_id]))
        self.assertEqual(res_admin.status_code, 200)
        self.assertContains(res_admin, 'Tax Invoice & Service Receipt')
        self.assertContains(res_admin, 'Magnetron Tube')
        self.assertContains(res_admin, '2150.00')

        # 2. Accessible by Owning Consumer
        session['username'] = self.consumer1.email
        session['role'] = 'Consumer'
        session.save()

        res_owner = self.client.get(reverse('services:print_service_invoice', args=[self.invoice.Invoice_id]))
        self.assertEqual(res_owner.status_code, 200)
        self.assertContains(res_owner, 'Thomas Mathew')

        # 3. Forbidden (403) for Non-Owning Consumer
        session['username'] = self.consumer2.email
        session['role'] = 'Consumer'
        session.save()

        res_other = self.client.get(reverse('services:print_service_invoice', args=[self.invoice.Invoice_id]))
        self.assertEqual(res_other.status_code, 403)

    def test_admin_reports_tabs_and_csv_export(self):
        # Log in as Admin
        session = self.client.session
        session['username'] = self.admin.username
        session['role'] = 'Admin'
        session.save()

        # Tab 1: Service Centers HTML and CSV
        res_sc = self.client.get(reverse('services:admin_reports'), {'tab': 'service_centers'})
        self.assertEqual(res_sc.status_code, 200)
        self.assertContains(res_sc, 'Service Center Network Report')

        res_sc_csv = self.client.get(reverse('services:admin_reports'), {'tab': 'service_centers', 'export': 'csv'})
        self.assertEqual(res_sc_csv.status_code, 200)
        self.assertIn('text/csv', res_sc_csv['Content-Type'])
        self.assertIn('Center ID,Center Name', res_sc_csv.content.decode('utf-8'))

        # Tab 2: Consumers HTML and CSV
        res_cons = self.client.get(reverse('services:admin_reports'), {'tab': 'consumers'})
        self.assertEqual(res_cons.status_code, 200)
        self.assertContains(res_cons, 'Consumer Registrations Registry')

        res_cons_csv = self.client.get(reverse('services:admin_reports'), {'tab': 'consumers', 'export': 'csv'})
        self.assertEqual(res_cons_csv.status_code, 200)
        self.assertIn('text/csv', res_cons_csv['Content-Type'])
        self.assertIn('Consumer ID,First Name', res_cons_csv.content.decode('utf-8'))

        # Tab 3: Products / Appliances HTML and CSV
        res_prod = self.client.get(reverse('services:admin_reports'), {'tab': 'products'})
        self.assertEqual(res_prod.status_code, 200)
        self.assertContains(res_prod, 'Consumer Product Registrations')

        res_prod_csv = self.client.get(reverse('services:admin_reports'), {'tab': 'products', 'export': 'csv'})
        self.assertEqual(res_prod_csv.status_code, 200)
        self.assertIn('text/csv', res_prod_csv['Content-Type'])
        self.assertIn('Reg ID,Consumer Name', res_prod_csv.content.decode('utf-8'))

        # Tab 4: Work Orders HTML and CSV
        res_wo = self.client.get(reverse('services:admin_reports'), {'tab': 'work_orders'})
        self.assertEqual(res_wo.status_code, 200)
        self.assertContains(res_wo, 'Work Order Lifecycle & Invoiced Revenue')

        res_wo_csv = self.client.get(reverse('services:admin_reports'), {'tab': 'work_orders', 'export': 'csv'})
        self.assertEqual(res_wo_csv.status_code, 200)
        self.assertIn('text/csv', res_wo_csv['Content-Type'])
        self.assertIn('WO ID,Request No', res_wo_csv.content.decode('utf-8'))

    def test_admin_reports_role_security(self):
        # Unauthenticated blocked from /admin/reports/
        res_unauth = self.client.get(reverse('services:admin_reports'))
        self.assertRedirects(res_unauth, reverse('accounts:login'), fetch_redirect_response=False)

        # Non-admin (Consumer) blocked from /admin/reports/
        session = self.client.session
        session['username'] = self.consumer1.email
        session['role'] = 'Consumer'
        session.save()

        res = self.client.get(reverse('services:admin_reports'))
        self.assertRedirects(res, reverse('accounts:login'), fetch_redirect_response=False)





