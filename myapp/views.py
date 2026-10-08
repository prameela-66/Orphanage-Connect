from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, DonorProfile, OrphanageProfile, Need, Donation, Proof
from .forms import DonorRegisterForm, OrphanageRegisterForm
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, get_object_or_404
from .models import Need, Proof

from .forms import EmailLoginForm

from .forms import DonationForm
from .forms import DonorUserForm, DonorProfileForm, OrphanageProfileForm
from django.db.models import Sum, Avg, Prefetch, Q
from django.shortcuts import render

@login_required
def view_proofs(request):
    if request.user.user_type != 'Donor':
        messages.error(request, "Only donors can view proofs.")
        return redirect('home')

    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    donations = donor_profile.donation_set.select_related('need__orphanage')
    proofs = Proof.objects.filter(need__in=[don.need for don in donations])

    context = {'proofs': proofs}
    return render(request, 'view_proofs.html', context)
def donor_statistics(request):
    # Example: get total donors and total donations
    total_donors = Donation.objects.values('donor').distinct().count()
    total_donations = Donation.objects.aggregate(total=Sum('amount'))['total']

    
    context = {
        'total_donors': total_donors,
        'total_donations': total_donations,
    }
    return render(request, 'donor_statistics.html', context)
from .utils import generate_donation_receipt, send_donation_confirmation_email, send_proof_uploaded_email
import uuid

@login_required
def donate(request, need_id):
    if request.user.user_type != 'Donor':
        return redirect('home')

    need = get_object_or_404(Need, id=need_id)
    donor_profile = get_object_or_404(DonorProfile, user=request.user)

    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = donor_profile
            donation.need = need
            donation.orphanage = need.orphanage
            donation.transaction_id = str(uuid.uuid4())[:8]
            donation.save()

            # Update amount received
            need.amount_received += donation.amount
            need.save()

            # ✅ Generate PDF receipt
            pdf_file = generate_donation_receipt(donation)
            donation.receipt.save(f"receipt_{donation.transaction_id}.pdf", pdf_file)
            donation.save()

            # 📧 Send donation confirmation email (with PDF receipt attachment)
            send_donation_confirmation_email(donation)

            messages.success(request, f"You have donated ₹{donation.amount} to {need.orphanage.name_of_orphanage}!")

            # Redirect to success page (so donor can download receipt)
            return render(request, 'donation_success.html', {'donation': donation})
    else:
        form = DonationForm()

    return render(request, 'donate.html', {'form': form, 'need': need})

# ---------- Home ----------
def home(request):
    return render(request, 'home.html')


# ---------- Donor Registration ----------
def donor_register(request):
    if request.method == 'POST':
        form = DonorRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'Donor'
            user.set_password(form.cleaned_data['password1'])  # <-- hash password
            user.save()
            DonorProfile.objects.create(
                user=user,
                full_name=form.cleaned_data['full_name']
            )
            messages.success(request, 'Donor registration successful! Please log in.')
            return redirect('login')
    else:
        form = DonorRegisterForm()
    return render(request, 'donor_register.html', {'form': form})


# ---------- Orphanage Registration ----------
def orphanage_register(request):
    if request.method == 'POST':
        form = OrphanageRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 'Orphanage'
            user.set_password(form.cleaned_data['password1'])  # <-- hash password
            user.save()
            OrphanageProfile.objects.create(
                user=user,
                name_of_orphanage=form.cleaned_data['name_of_orphanage'],
                location=form.cleaned_data['location'],
                email=form.cleaned_data['email'],
                phone_number=form.cleaned_data['phone_number'],
                registration_certificate=form.cleaned_data['registration_certificate'],
                government_id_proof=form.cleaned_data['government_id_proof'],
                trust_deed=form.cleaned_data.get('trust_deed'),
                address_proof=form.cleaned_data.get('address_proof'),
                orphanage_photo=form.cleaned_data.get('orphanage_photo')
            )
            messages.success(request, 'Orphanage registration successful! Please log in.')
            return redirect('login')
    else:
        form = OrphanageRegisterForm()
    return render(request, 'orphanage_register.html', {'form': form})



# ---------- Login ----------
def user_login(request):
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # actually email
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if user.user_type == 'Donor':
                    return redirect('donor_dashboard')
                elif user.user_type == 'Orphanage':
                    return redirect('orphanage_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Invalid email or password.')
    else:
        form = EmailLoginForm()
    return render(request, 'login.html', {'form': form})



# ---------- Logout ----------
def user_logout(request):
    logout(request)
    return redirect('home')


# ---------- Donor Dashboard ----------
@login_required
def donor_dashboard(request):
    donor = request.user.donorprofile

    # Extract filter GET parameters
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category', '').strip()

    # Base QuerySet
    needs = (
        Need.objects
        .select_related('orphanage')
        .prefetch_related('proof_set')
        .all()
    )

    # Search across need title, description, orphanage name, and location
    if search_query:
        needs = needs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(orphanage__name_of_orphanage__icontains=search_query) |
            Q(orphanage__location__icontains=search_query)
        )

    # Filter by Category
    if category_filter and category_filter != 'All':
        needs = needs.filter(category=category_filter)

    needs = needs.order_by('-date_posted')

    donated_need_ids = list(donor.donation_set.values_list('need_id', flat=True))

    categories = [choice[0] for choice in Need.CATEGORY_CHOICES]

    context = {
        'needs': needs,
        'donated_need_ids': donated_need_ids,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_filter,
    }
    return render(request, 'donor_dashboard.html', context)
# ---------- Orphanage Dashboard ----------
@login_required
def orphanage_dashboard(request):
    if request.user.user_type != 'Orphanage':
        return redirect('home')
    orphanage = OrphanageProfile.objects.get(user=request.user)
    needs = Need.objects.filter(orphanage=orphanage)
    return render(request, 'orphanage_dashboard.html', {'needs': needs, 'orphanage': orphanage})


# ---------- Post Need ----------
@login_required
def post_need(request):
    if request.user.user_type != 'Orphanage':
        return redirect('home')

    orphanage = OrphanageProfile.objects.get(user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category', 'Food')
        amount_required = request.POST.get('amount_required')

        Need.objects.create(
            orphanage=orphanage,
            title=title,
            description=description,
            category=category,
            amount_required=amount_required
        )
        messages.success(request, 'Need posted successfully!')
        return redirect('orphanage_dashboard')

    return render(request, 'post_need.html')


# ---------- Upload Proof ----------
@login_required
def upload_proof(request, need_id):
    if request.user.user_type != 'Orphanage':
        return redirect('home')

    need = Need.objects.get(id=need_id)

    if request.method == 'POST':
        receipt = request.FILES.get('receipt')
        description = request.POST.get('description')
        proof = Proof.objects.create(need=need, receipt=receipt, description=description)
        
        # 📧 Send proof upload notification email to contributing donors
        send_proof_uploaded_email(proof, request=request)

        messages.success(request, 'Proof uploaded successfully!')
        return redirect('orphanage_dashboard')

    return render(request, 'upload_proof.html', {'need': need})

# views.py
@login_required
def donor_profile(request):
    if request.user.user_type != 'Donor':
        return redirect('home')

    donor_profile = DonorProfile.objects.get(user=request.user)

    # Prefetch proofs for each need
    donations = Donation.objects.filter(donor=donor_profile)\
        .select_related('orphanage', 'need')\
        .prefetch_related(Prefetch('need__proof_set'))\
        .order_by('-date')

    total_donations = donations.aggregate(total=Sum('amount'))['total'] or 0
    donated_needs = Need.objects.filter(donation__donor=donor_profile).distinct().prefetch_related('proof_set')
    if request.method == 'POST':
        user_form = DonorUserForm(request.POST, instance=request.user)
        profile_form = DonorProfileForm(request.POST, request.FILES, instance=donor_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('donor_profile')
    else:
        user_form = DonorUserForm(instance=request.user)
        profile_form = DonorProfileForm(instance=donor_profile)

    return render(request, 'donor_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': donor_profile,
        'donations': donations,
        'total_donations': total_donations,
         'donated_needs': donated_needs, 
    })

@login_required
def orphanage_profile(request):
    if request.user.user_type != 'Orphanage':
        return redirect('home')

    orphanage_profile = OrphanageProfile.objects.get(user=request.user)

    if request.method == 'POST':
        form = OrphanageProfileForm(request.POST, request.FILES, instance=orphanage_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('orphanage_profile')
    else:
        form = OrphanageProfileForm(instance=orphanage_profile)

    return render(request, 'orphanage_profile.html', {'form': form})
def need_details(request, need_id):
    need = Need.objects.get(id=need_id)
    return render(request, 'need_details.html', {'need': need})
@property
def progress_percentage(self):
    if self.amount_required == 0:
        return 0
    return float(self.amount_received / self.amount_required * 100)

@property
def donors_count(self):
    return self.donation_set.count()




# views.py
from django.shortcuts import render, redirect
from .models import DonorProfile
from .forms import DonorProfileForm

@login_required
def edit_profile(request):
    profile, created = DonorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = DonorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('donor_profile')  # redirect to your profile page
    else:
        form = DonorProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})






