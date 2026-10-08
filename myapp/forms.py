from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, DonorProfile, OrphanageProfile, Need, Proof
from django.contrib.auth.forms import AuthenticationForm

class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')

class DonorRegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=15)
    dob = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    location = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    captcha = forms.CharField(help_text="Type 'HUMAN' to verify")

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone_number', 'dob', 'location', 'state', 'captcha', 'password1', 'password2']

    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        if captcha.lower() != 'human':
            raise forms.ValidationError('Captcha incorrect. Please type HUMAN.')
        return captcha

from django import forms
from .models import Donation

class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount'}),
        }
class OrphanageRegisterForm(UserCreationForm):
    name_of_orphanage = forms.CharField(max_length=150)
    location = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone_number = forms.CharField(max_length=15)
    registration_certificate = forms.FileField()
    government_id_proof = forms.FileField()
    trust_deed = forms.FileField(required=False)
    address_proof = forms.FileField(required=False)
    orphanage_photo = forms.FileField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'Orphanage'
        if commit:
            user.save()
        return user
    
# forms.py
from django import forms
from .models import DonorProfile, OrphanageProfile, User

class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = ['full_name','phone', 'photo','address']

class DonorUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'phone_number', 'location', 'state', 'dob']

class OrphanageProfileForm(forms.ModelForm):
    class Meta:
        model = OrphanageProfile
        fields = [
            'name_of_orphanage', 'location', 'email', 'phone_number',
            'registration_certificate', 'government_id_proof',
            'trust_deed', 'address_proof', 'orphanage_photo'
        ]
