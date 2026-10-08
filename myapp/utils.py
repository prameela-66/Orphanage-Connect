import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from num2words import num2words
from django.core.files.base import ContentFile
from .models import Donation
def generate_donation_receipt(donation, logo_path='static/images/logo.png'):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 40
    right = width - 40
    top = height - 40

    # --- Logo & Header ---
    try:
        logo = ImageReader(logo_path)
        pdf.drawImage(logo, left + 10, top - 80, width=100, height=60, preserveAspectRatio=True)
    except:
        pass

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(left + 130, top - 40, donation.need.orphanage.name_of_orphanage.upper())

    pdf.setFont("Helvetica", 11)
    pdf.drawString(left + 130, top - 60, "DONATION RECEIPT")

    pdf.line(left, top - 85, right, top - 85)

    # --- Receipt Info ---
    y = top - 110
    pdf.setFont("Helvetica", 10)
    pdf.drawString(left, y, f"Receipt No : {donation.transaction_id}")
    pdf.drawString(right - 200, y, f"Date : {donation.date.strftime('%d/%m/%Y')}")

    y -= 20
    # Safely handle donor name (DonorProfile → User)
    donor_name = ""
    if hasattr(donation.donor, "user"):
        donor_user = donation.donor.user
        donor_name = donor_user.get_full_name() or donor_user.username
    else:
        donor_name = str(donation.donor)

    pdf.drawString(left, y, f"Name : {donor_name}")
    pdf.drawString(right - 200, y, f"Orphanage : {donation.need.orphanage.name_of_orphanage}")


    # --- Table Header ---
    y -= 40
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left + 5, y, "Sl.No")
    pdf.drawString(left + 60, y, "Particulars")
    pdf.drawRightString(right - 60, y, "Amount (₹)")
    pdf.line(left, y - 5, right, y - 5)

    # --- Table Content ---
    pdf.setFont("Helvetica", 10)
    y -= 25
    pdf.drawString(left + 5, y, "1")
    pdf.drawString(left + 60, y, "Donation Amount")
    pdf.drawRightString(right - 60, y, f"{donation.amount:.2f}")

    # --- Total ---
    y -= 30
    pdf.line(left, y, right, y)
    y -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left + 60, y, "Total")
    pdf.drawRightString(right - 60, y, f"{donation.amount:.2f}")

    # --- Amount in Words ---
    y -= 40
    pdf.setFont("Helvetica", 9)
    amount_words = num2words(donation.amount, lang='en').title()
    pdf.drawString(left, y, f"Rupees in words : {amount_words} Only")

    # --- Reference ---
    y -= 30
    pdf.setFont("Helvetica", 9)
    pdf.drawString(left, y, f"Payment Reference No : {donation.transaction_id}")

    # --- Footer ---
    y -= 60
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.setFillColor(colors.grey)
    pdf.drawString(left, y, "This is a system auto-generated receipt. No signature required.")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return ContentFile(buffer.getvalue(), f"receipt_{donation.transaction_id}.pdf")


# # ---------------- Email Notifications ----------------
# import logging
# from django.core.mail import EmailMessage
# from django.conf import settings

# logger = logging.getLogger(__name__)

# def send_donation_confirmation_email(donation):
#     """
#     Sends a confirmation email to the donor after a successful donation.
#     Attaches the generated PDF receipt if available.
#     """
#     try:
#         donor_email = donation.donor.user.email if hasattr(donation.donor, 'user') else None
#         if not donor_email:
#             logger.warning(f"No registered email found for donor {donation.donor}")
#             return False

#         donor_name = donation.donor.full_name or (donation.donor.user.username if hasattr(donation.donor, 'user') else "Valued Donor")
#         orphanage_name = donation.need.orphanage.name_of_orphanage
#         need_title = donation.need.title
#         amount = donation.amount
#         transaction_id = donation.transaction_id
#         donation_date = donation.date.strftime('%B %d, %Y at %I:%M %p')

#         subject = f"Donation Successful - Receipt #{transaction_id}"
#         body = (
#             f"Dear {donor_name},\n\n"
#             f"Thank you for your generous donation to {orphanage_name}!\n\n"
#             f"Here are your donation details:\n"
#             f"--------------------------------------------------\n"
#             f"Donor Name     : {donor_name}\n"
#             f"Orphanage Name : {orphanage_name}\n"
#             f"Need Title     : {need_title}\n"
#             f"Amount Donated : ₹{amount}\n"
#             f"Transaction ID : {transaction_id}\n"
#             f"Donation Date  : {donation_date}\n"
#             f"Status         : Successful\n"
#             f"--------------------------------------------------\n\n"
#             f"Your support brings hope and makes a real difference in the lives of children.\n"
#             f"Please find your official donation receipt attached to this email.\n\n"
#             f"Warm regards,\n"
#             f"The OrphaNet Team"
#         )

#         email = EmailMessage(
#             subject=subject,
#             body=body,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             to=[donor_email],
#         )

#         # Attach PDF receipt if available
#         if donation.receipt and hasattr(donation.receipt, 'path'):
#             try:
#                 email.attach_file(donation.receipt.path)
#             except Exception as attach_err:
#                 logger.warning(f"Could not attach file path directly, reading content: {attach_err}")
#                 if hasattr(donation.receipt, 'read'):
#                     email.attach(f"receipt_{transaction_id}.pdf", donation.receipt.read(), 'application/pdf')

#         email.send(fail_silently=False)
#         logger.info(f"Donation confirmation email sent successfully to {donor_email}")
#         return True
#     except Exception as e:
#         logger.error(f"Failed to send donation confirmation email for donation {donation.id}: {e}")
#         return False


# def send_proof_uploaded_email(proof, request=None):
#     """
#     Sends an email notification to all donors who donated to the specific Need
#     when an orphanage uploads a proof/bill.
#     """
#     try:
#         from .models import Donation
#         need = proof.need
#         orphanage_name = need.orphanage.name_of_orphanage
#         need_title = need.title
#         description = proof.description or "No description provided."
#         upload_date = proof.date_uploaded.strftime('%B %d, %Y')

#         # Find all distinct donors who donated to this specific Need
#         donations = Donation.objects.filter(need=need).select_related('donor__user').distinct()
        
#         if request:
#             proof_link = request.build_absolute_uri('/donor/dashboard/')
#         else:
#             proof_link = "http://localhost:8000/donor/dashboard/"

#         sent_count = 0
#         seen_emails = set()

#         for donation in donations:
#             donor_user = getattr(donation.donor, 'user', None)
#             donor_email = donor_user.email if donor_user else None

#             if not donor_email or donor_email in seen_emails:
#                 continue

#             seen_emails.add(donor_email)
#             donor_name = donation.donor.full_name or (donor_user.username if donor_user else "Valued Donor")

#             subject = f"Proof of Utilization Uploaded: {need_title}"
#             body = (
#                 f"Dear {donor_name},\n\n"
#                 f"We are pleased to inform you that {orphanage_name} has uploaded proof of utilization for the cause you supported:\n\n"
#                 f"--------------------------------------------------\n"
#                 f"Need Title    : {need_title}\n"
#                 f"Orphanage     : {orphanage_name}\n"
#                 f"Date Uploaded : {upload_date}\n"
#                 f"Description   : {description}\n"
#                 f"--------------------------------------------------\n\n"
#                 f"You can view the proof and updates directly on your Donor Dashboard:\n"
#                 f"{proof_link}\n\n"
#                 f"Thank you once again for your contribution!\n\n"
#                 f"Warm regards,\n"
#                 f"The OrphaNet Team"
#             )

#             email = EmailMessage(
#                 subject=subject,
#                 body=body,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 to=[donor_email],
#             )
#             email.send(fail_silently=False)
#             sent_count += 1

#         logger.info(f"Proof upload email sent to {sent_count} donor(s) for need '{need_title}'")
#         return sent_count
#     except Exception as e:
#         logger.error(f"Failed to send proof upload email for proof {proof.id}: {e}")
#         return 0

import logging
from django.core.mail import EmailMessage
from django.conf import settings

logger = logging.getLogger(__name__)


def send_donation_confirmation_email(donation):
    """Send donation confirmation email with PDF receipt."""

    donor_email = donation.donor.user.email

    if not donor_email:
        print("ERROR: Donor has no email address.")
        return False

    donor_name = donation.donor.full_name or "Valued Donor"
    orphanage_name = donation.need.orphanage.name_of_orphanage
    need_title = donation.need.title
    amount = donation.amount
    transaction_id = donation.transaction_id
    donation_date = donation.date.strftime("%B %d, %Y at %I:%M %p")

    subject = f"Donation Successful - Receipt #{transaction_id}"

    body = f"""
Dear {donor_name},

Thank you for your generous donation to {orphanage_name}.

Donation Details
------------------------------------------
Donor Name     : {donor_name}
Orphanage Name : {orphanage_name}
Need Title     : {need_title}
Amount Donated : ₹{amount}
Transaction ID : {transaction_id}
Donation Date  : {donation_date}
Status         : Successful
------------------------------------------

Your support makes a real difference.

Your donation receipt is attached to this email.

Warm regards,
The OrphaNet Team
"""

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[donor_email],
        )

        # Attach PDF receipt
        if donation.receipt:
            try:
                email.attach_file(donation.receipt.path)
            except Exception as e:
                print("PDF attachment error:", e)

        result = email.send(fail_silently=False)

        print(f"Donation email sent to {donor_email}")
        print(f"Email result: {result}")

        return True

    except Exception as e:
        print("DONATION EMAIL ERROR:", repr(e))
        logger.exception("Donation email failed")

        # During debugging, re-raise the error
        raise


def send_proof_uploaded_email(proof, request=None):
    """Send proof-upload notification to donors who donated to this Need."""

    need = proof.need

    orphanage_name = need.orphanage.name_of_orphanage
    need_title = need.title
    description = proof.description or "No description provided."
    upload_date = proof.date_uploaded.strftime("%B %d, %Y")

    # Find donors who donated to THIS need
    donations = (
        Donation.objects
        .filter(need=need)
        .select_related("donor__user")
    )

    if request:
        proof_link = request.build_absolute_uri("/donor/dashboard/")
    else:
        proof_link = "http://127.0.0.1:8000/donor/dashboard/"

    sent_count = 0
    seen_emails = set()

    for donation in donations:

        donor = donation.donor
        donor_user = donor.user

        donor_email = donor_user.email

        if not donor_email:
            continue

        if donor_email in seen_emails:
            continue

        seen_emails.add(donor_email)

        donor_name = donor.full_name or "Valued Donor"

        subject = f"Proof Uploaded - {need_title}"

        body = f"""
Dear {donor_name},

{orphanage_name} has uploaded proof of utilization
for the donation need you supported.

Proof Details
------------------------------------------
Need Title    : {need_title}
Orphanage     : {orphanage_name}
Date Uploaded : {upload_date}
Description   : {description}
------------------------------------------

You can view your donor dashboard here:

{proof_link}

Thank you for your contribution.

Warm regards,
The OrphaNet Team
"""

        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[donor_email],
            )

            # Send proof PDF/bill as attachment
            if proof.receipt:
                try:
                    email.attach_file(proof.receipt.path)
                except Exception as e:
                    print("Proof attachment error:", e)

            result = email.send(fail_silently=False)

            print(f"Proof email sent to {donor_email}")
            print(f"Email result: {result}")

            sent_count += 1

        except Exception as e:
            print(
                f"PROOF EMAIL ERROR for {donor_email}:",
                repr(e)
            )
            logger.exception("Proof email failed")

    print(f"Total proof emails sent: {sent_count}")

    return sent_count