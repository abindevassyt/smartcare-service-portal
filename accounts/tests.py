from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from accounts.models import AuthUser, State, District, ConsumerReg


class Stage4AuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.state = State.objects.create(state='Kerala')
        self.dist = District.objects.create(District='Ernakulam', statid=self.state)
        self.admin_user = AuthUser.objects.create(
            username='admin',
            password=make_password('admin123'),
            role='Admin'
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SmartCare Service Portal')
        self.assertContains(response, 'Username or Email')

    def test_admin_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'admin123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session.get('role'), 'Admin')
        self.assertEqual(self.client.session.get('username'), 'admin')
        self.assertContains(response, 'Administrator Command Center')

    def test_invalid_login_failure(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client.session.get('role'))
        self.assertContains(response, 'Invalid password')

    def test_protected_dashboard_redirects_unauthenticated(self):
        response = self.client.get(reverse('accounts:admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_districts_api(self):
        response = self.client.get(reverse('accounts:districts_api', args=[self.state.statid]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('districts', data)
        self.assertEqual(len(data['districts']), 1)
        self.assertEqual(data['districts'][0]['name'], 'Ernakulam')

    def test_consumer_registration(self):
        reg_data = {
            'fname': 'John',
            'lname': 'Doe',
            'dob': '1995-05-15',
            'address': 'MG Road, Kochi',
            'statid': str(self.state.statid),
            'Distid': str(self.dist.Distid),
            'mob': '9847012345',
            'pin': '682016',
            'email': 'john.doe@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'consumertype': 'Regular'
        }
        response = self.client.post(reverse('accounts:register'), reg_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify ConsumerReg created
        consumer = ConsumerReg.objects.filter(email='john.doe@example.com').first()
        self.assertIsNotNone(consumer)
        self.assertEqual(consumer.status, 'Pending')
        
        # Verify AuthUser created
        auth_user = AuthUser.objects.filter(username='john.doe@example.com').first()
        self.assertIsNotNone(auth_user)
        self.assertEqual(auth_user.role, 'Consumer')

        # Test login with newly created consumer
        login_res = self.client.post(reverse('accounts:login'), {
            'username': 'john.doe@example.com',
            'password': 'password123'
        }, follow=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertEqual(self.client.session.get('role'), 'Consumer')
        self.assertContains(login_res, 'Consumer Dashboard')

