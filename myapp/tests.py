from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from myapp.models import User, DonorProfile, OrphanageProfile, Need, Donation, Proof
from decimal import Decimal
import io
from django.core.files.uploadedfile import SimpleUploadedFile

class DonorDashboardFilterTest(TestCase):
    def setUp(self):
        # Create Donor user & profile
        self.donor_user = User.objects.create_user(
            username='donor@example.com',
            email='donor@example.com',
            password='password123',
            user_type='Donor'
        )
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user,
            full_name='John Donor'
        )

        # Create Orphanage 1 user & profile
        self.orp1_user = User.objects.create_user(
            username='orp1@example.com',
            email='orp1@example.com',
            password='password123',
            user_type='Orphanage'
        )
        self.orp1 = OrphanageProfile.objects.create(
            user=self.orp1_user,
            name_of_orphanage='Little Angels Orphanage',
            location='Bhimavaram',
            email='orp1@example.com',
            phone_number='9876543210'
        )

        # Create Orphanage 2 user & profile
        self.orp2_user = User.objects.create_user(
            username='orp2@example.com',
            email='orp2@example.com',
            password='password123',
            user_type='Orphanage'
        )
        self.orp2 = OrphanageProfile.objects.create(
            user=self.orp2_user,
            name_of_orphanage='Hope Foundation',
            location='Vijayawada',
            email='orp2@example.com',
            phone_number='9876543211'
        )

        # Create Needs
        self.need1 = Need.objects.create(
            orphanage=self.orp1,
            title='Need medicines for 30 children',
            description='Urgent requirement for seasonal viral medicines.',
            category='Medicine',
            amount_required=Decimal('5000.00'),
            amount_received=Decimal('0.00'),
            is_fulfilled=False
        )

        self.need2 = Need.objects.create(
            orphanage=self.orp1,
            title='School books and stationery',
            description='Textbooks and notebooks for primary school students.',
            category='Education',
            amount_required=Decimal('10000.00'),
            amount_received=Decimal('10000.00'),
            is_fulfilled=True
        )

        self.need3 = Need.objects.create(
            orphanage=self.orp2,
            title='Winter clothing drive',
            description='Warm sweaters and blankets for orphans.',
            category='Clothing',
            amount_required=Decimal('8000.00'),
            amount_received=Decimal('2000.00'),
            is_fulfilled=False
        )

        self.client = Client()
        self.client.force_login(self.donor_user)

    def test_search_across_title_description_orphanage_location(self):
        # 1. Search title "medicine"
        response = self.client.get(reverse('donor_dashboard'), {'search': 'medicine'})
        needs = list(response.context['needs'])
        self.assertEqual(len(needs), 1)
        self.assertEqual(needs[0].id, self.need1.id)

        # 2. Search description "notebooks"
        response = self.client.get(reverse('donor_dashboard'), {'search': 'notebooks'})
        needs = list(response.context['needs'])
        self.assertEqual(len(needs), 1)
        self.assertEqual(needs[0].id, self.need2.id)

        # 3. Search location "Bhimavaram"
        response = self.client.get(reverse('donor_dashboard'), {'search': 'Bhimavaram'})
        needs = list(response.context['needs'])
        self.assertEqual(len(needs), 2)

        # 4. Search orphanage name "Hope"
        response = self.client.get(reverse('donor_dashboard'), {'search': 'Hope'})
        needs = list(response.context['needs'])
        self.assertEqual(len(needs), 1)
        self.assertEqual(needs[0].id, self.need3.id)

    def test_filter_by_category(self):
        response = self.client.get(reverse('donor_dashboard'), {'category': 'Medicine'})
        needs = list(response.context['needs'])
        self.assertEqual(len(needs), 1)
        self.assertEqual(needs[0].category, 'Medicine')

    def test_combined_search_and_category(self):
        params = {
            'search': 'Little Angels',
            'category': 'Medicine'
        }
        response = self.client.get(reverse('donor_dashboard'), params)
        needs = list(response.context['needs'])
        self.assertEqual(len(needs), 1)
        self.assertEqual(needs[0].id, self.need1.id)


class EmailNotificationTest(TestCase):
    def setUp(self):
        # Create Donor
        self.donor_user = User.objects.create_user(
            username='donor@example.com',
            email='donor@example.com',
            password='password123',
            user_type='Donor'
        )
        self.donor_profile = DonorProfile.objects.create(
            user=self.donor_user,
            full_name='Jane Donor'
        )

        # Create Orphanage
        self.orp_user = User.objects.create_user(
            username='orp@example.com',
            email='orp@example.com',
            password='password123',
            user_type='Orphanage'
        )
        self.orphanage = OrphanageProfile.objects.create(
            user=self.orp_user,
            name_of_orphanage='Hope Haven',
            location='Hyderabad',
            email='orp@example.com',
            phone_number='9123456780'
        )

        # Create Need
        self.need = Need.objects.create(
            orphanage=self.orphanage,
            title='Food Kits for 50 Kids',
            description='Monthly grocery supplies.',
            category='Food',
            amount_required=Decimal('15000.00'),
            amount_received=Decimal('0.00'),
            is_fulfilled=False
        )

        self.client = Client()

    def test_donation_success_email_triggered(self):
        self.client.force_login(self.donor_user)

        # Make donation POST request
        response = self.client.post(reverse('donate', kwargs={'need_id': self.need.id}), {'amount': 2500})
        self.assertEqual(response.status_code, 200)

        # Check outbox email
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertIn('donor@example.com', sent_mail.to)
        self.assertIn('Donation Successful', sent_mail.subject)
        self.assertIn('Food Kits for 50 Kids', sent_mail.body)
        self.assertIn('Hope Haven', sent_mail.body)
        self.assertEqual(len(sent_mail.attachments), 1)

    def test_proof_upload_email_triggered(self):
        # First, donor donates
        self.client.force_login(self.donor_user)
        self.client.post(reverse('donate', kwargs={'need_id': self.need.id}), {'amount': 5000})

        # Clear outbox from donation email
        mail.outbox.clear()

        # Orphanage logs in and uploads proof
        self.client.force_login(self.orp_user)
        sample_file = SimpleUploadedFile("bill.jpg", b"file_content", content_type="image/jpeg")

        response = self.client.post(
            reverse('upload_proof', kwargs={'need_id': self.need.id}),
            {'description': 'Receipt for grocery items purchased', 'receipt': sample_file}
        )
        self.assertEqual(response.status_code, 302)

        # Verify email sent to contributing donor
        self.assertEqual(len(mail.outbox), 1)
        proof_mail = mail.outbox[0]
        self.assertIn('donor@example.com', proof_mail.to)
        self.assertIn('Proof of Utilization Uploaded', proof_mail.subject)
        self.assertIn('Food Kits for 50 Kids', proof_mail.body)
        self.assertIn('Receipt for grocery items purchased', proof_mail.body)
