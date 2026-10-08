from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

from decimal import Decimal
# ---------------- Custom User ----------------
class User(AbstractUser):
    USER_TYPES = (
        ('Donor', 'Donor'),
        ('Orphanage', 'Orphanage'),
    )
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    USERNAME_FIELD = 'email'  # login using email
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.username} ({self.user_type})"


# ---------------- Donor Profile ----------------
class DonorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, blank=True, null=True)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    total_donations = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    address = models.TextField(blank=True, null=True)
    def __str__(self):
        return self.full_name


# ---------------- Orphanage Profile ----------------
class OrphanageProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name_of_orphanage = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    registration_certificate = models.FileField(upload_to='documents/')
    government_id_proof = models.FileField(upload_to='documents/')
    trust_deed = models.FileField(upload_to='documents/', blank=True, null=True)
    address_proof = models.FileField(upload_to='documents/', blank=True, null=True)
    orphanage_photo = models.ImageField(upload_to='images/', blank=True, null=True)

    def __str__(self):
        return self.name_of_orphanage


CATEGORY_CHOICES = (
    ('Food', 'Food'),
    ('Education', 'Education'),
    ('Medicine', 'Medicine'),
    ('Clothing', 'Clothing'),
)

# ---------------- Needs posted by orphanage ----------------
class Need(models.Model):
    CATEGORY_CHOICES = CATEGORY_CHOICES
    orphanage = models.ForeignKey(OrphanageProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Food')
    amount_required = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_posted = models.DateTimeField(default=timezone.now)
    is_fulfilled = models.BooleanField(default=False)  # keep this as a database field

    def __str__(self):
        return f"{self.title} - {self.orphanage.name_of_orphanage}"

    @property
    def progress_percentage(self):
        """Return donation progress as a percentage."""
        if self.amount_required > 0:
            return float((self.amount_received / self.amount_required) * 100)
        return 0

    @property
    def donors_count(self):
        """Return number of donors for this need."""
        return self.donation_set.count()

    def save(self, *args, **kwargs):

        try:
            required = Decimal(self.amount_required)
            received = Decimal(self.amount_received)
            self.is_fulfilled = received >= required
        except (TypeError, ValueError, InvalidOperation):
            self.is_fulfilled = False
        super().save(*args, **kwargs)



# ---------------- Donation ----------------
class Donation(models.Model):
    donor = models.ForeignKey(DonorProfile, on_delete=models.CASCADE)
    need = models.ForeignKey('myapp.Need', on_delete=models.CASCADE)  # use actual app name
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)

    orphanage = models.ForeignKey(OrphanageProfile, on_delete=models.CASCADE, related_name='donations', default=1)
    def __str__(self):
        return f"{self.donor.full_name} → {self.need.title}"


# ---------------- Proofs of purchase or receipts ----------------
class Proof(models.Model):
    need = models.ForeignKey('myapp.Need', on_delete=models.CASCADE)  # use actual app name
    receipt = models.FileField(upload_to='proofs/')
    description = models.TextField(blank=True, null=True)
    date_uploaded = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Proof for {self.need.title}"
