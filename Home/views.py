from django.shortcuts import render,get_object_or_404, render,redirect
import calendar
import json
from datetime import datetime, timedelta
from .models import *
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login as auth_login
from django.contrib import messages
from .forms import *
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count,Sum
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
#CUSTOMER AUTH
def index(request):
    services = Service.objects.all()
    return render(request,'index2.html',{"services":services})

def sub(request,service_id):
    service = get_object_or_404(Service, id=service_id)
    subcategories = service.subcategories.all()
    return render(request, 'page2.html', {'service': service, 'subcategories': subcategories})


def customer_signup(request):
    if request.method == 'POST':
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('customer_login') # Redirect to customer dashboard
    else:
        form = CustomerSignUpForm()
    return render(request, 'register.html', {'form': form})



def customer_login(request):
    if request.method == 'POST':
        form = CustomerLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # Authenticate against the CustomUser model
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Check if the user is a customer
                if hasattr(user, 'is_customer') and user.is_customer:
                    auth_login(request, user)
                    return redirect('index')  # Redirect to customer dashboard
                else:
                    # Handle non-customer login attempts
                    return render(request, 'login.html', {
                        'form': form,
                        'error_message': 'This account does not have customer access.'
                    })
            else:
                # Handle invalid login
                return render(request, 'login.html', {
                    'form': form,
                    'error_message': 'Invalid credentials'
                })
    else:
        form = CustomerLoginForm()
    return render(request, 'login.html', {'form': form})



#SELLER AUTH
def service_provider_signup(request):
    if request.method == 'POST':
        form = ServiceProviderSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # This will handle creating both CustomUser and Seller
            auth_login(request, user)
            return redirect('service_provider_login') # Redirect to seller login
    else:
        form = ServiceProviderSignUpForm()
    return render(request, 'seller_register.html', {'form': form})

def service_provider_login(request):
    if request.method == 'POST':
        form = ServiceProviderLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None and user.is_service_provider and user.is_approved:
                auth_login(request, user)
                return redirect('sp_dashboard')  # Redirect to seller dashboard
            else:
                # Handle invalid login for sellers
                return render(request, 'seller_login.html', {'form': form, 'error_message': 'Invalid credentials or Wait for admin approvals'})
    else:
        form = ServiceProviderLoginForm()
    return render(request, 'seller_login.html', {'form': form})


def logout_view(request):
    # Use the built-in logout function to log the user out
    logout(request)
    return redirect('index') 


# Display details of the subcategory with a book now button
def subcategory_detail(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    return render(request, 'subcategory_detail.html', {'subcategory': subcategory})

from django.core.mail import send_mail
from django.conf import settings


@login_required
def book_now(request, pk):
    subcategory = get_object_or_404(SubCategory, pk=pk)
    subsubcategories = SubSubCategory.objects.filter(service=subcategory)
    booking_questions = BookingQuestion.objects.filter(subcategory=subcategory)

    now = datetime.now()
    today = now.date()

    def generate_time_slots(selected_date):
        """Generate available hourly time slots based on the selected date."""
        time_slots = []
        start_time = datetime.strptime("09:00", "%H:%M")  # Default start time
        end_time = datetime.strptime("22:00", "%H:%M")    # Default end time

        if selected_date == today:  # If today's date is selected
            current_time = now + timedelta(hours=1)
            start_time = current_time.replace(minute=0, second=0, microsecond=0)
            if start_time.time() > end_time.time():
                return time_slots  # No slots available for today

        while start_time.time() <= end_time.time():
            time_slots.append(start_time.strftime('%H:%M'))
            start_time += timedelta(hours=1)

        return time_slots

    def render_with_error(error_message):
        """Render the form with an error message."""
        time_slots = generate_time_slots(today)
        return render(request, 'book_now.html', {
            'subcategory': subcategory,
            'subsubcategories': subsubcategories,
            'booking_questions': booking_questions,
            'time_slots': time_slots,
            'today': today,
            'error': error_message,
        })

    if request.method == "POST":
        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')
        print(f"Received date: {selected_date}, time: {selected_time}")

        selected_subsubcategory_id = request.POST.get('subsubcategory')

        try:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return render_with_error('Invalid date format.')

        time_slots = generate_time_slots(selected_date)

        # Validate form inputs
        if not selected_date or not selected_time or not selected_subsubcategory_id:
            return render_with_error('All fields, including Sub-Subcategory, are required.')
        if len(selected_time) == 2:  # Only hour is provided
            selected_time += ":00"

        try:
            selected_datetime = datetime.strptime(
                selected_date.strftime('%Y-%m-%d') + f" {selected_time}", '%Y-%m-%d %H:%M'
            )
        except ValueError:
            return render_with_error('Invalid date or time format.')

        if selected_datetime < now + timedelta(hours=1):
            return render_with_error('The selected time slot must be at least 1 hour from now.')

        try:
            selected_subsubcategory = SubSubCategory.objects.get(pk=selected_subsubcategory_id)
        except SubSubCategory.DoesNotExist:
            return render_with_error('Invalid Sub-Subcategory selected.')

        customer = request.user.customer_profile
        customer_pincode = customer.pincode
        service_providers = ServiceProvider.objects.filter(
            pincode=customer_pincode,
            services_offered=subcategory,
        )

        if not service_providers.exists():
            return render_with_error(f'No service providers available in your area (Pincode: {customer_pincode}).')

        # Check service provider availability
        service_provider = service_providers.first()  # You can adjust the selection logic here
        if not is_service_provider_available(service_provider):
            return render_with_error(f"The selected service provider is not available at this time.")
        
        def send_appointment_email(appointment):
            subject = "Appointment Confirmation"
            customer_message = (
                f"Dear {appointment.customer.fname},\n\n"
                f"Your appointment for {appointment.subsubcategory.name} has been confirmed.\n"
                f"Date: {appointment.date}\n"
                f"Time: {appointment.time}\n"
                f"Service Provider: {appointment.service_provider.name}\n\n"
                f"Phone: {appointment.service_provider.phone}\n\n"
                "Thank you for choosing our service!"
            )

            provider_message = (
                f"Dear {appointment.service_provider.name},\n\n"
                f"You have a new appointment.\n"
                f"Customer: {appointment.customer.fname}\n"
                f"Service: {appointment.subsubcategory.name}\n"
                f"Date: {appointment.date}\n"
                f"Time: {appointment.time}\n\n"
                f"Address: {appointment.customer.address}\n\n"
                f"Phone: {appointment.customer.phone}\n\n"
                "Please be prepared for the service."
            )

            send_mail(
                subject,
                customer_message,
                settings.DEFAULT_FROM_EMAIL,
                [appointment.customer.user.email],
                fail_silently=False,
            )

            send_mail(
                subject,
                provider_message,
                settings.DEFAULT_FROM_EMAIL,
                [appointment.service_provider.user.email],
                fail_silently=False,
            )


        # Create the appointment if everything is valid
        appointment = Appointment.objects.create(
            customer=customer,
            service_provider=service_provider,
            subcategory=subcategory,
            subsubcategory=selected_subsubcategory,
            date=selected_date,
            price=selected_subsubcategory.rate,
            time=selected_time
        )

        save_booking_answers(request, booking_questions, appointment)
        send_appointment_email(appointment)

        return redirect('appointment_success', pk=appointment.id)

    time_slots = generate_time_slots(today)

    return render(request, 'book_now.html', {
        'subcategory': subcategory,
        'subsubcategories': subsubcategories,
        'booking_questions': booking_questions,
        'time_slots': time_slots,
        'today': today,
    })



@csrf_exempt
def add_appointment_item(request):
    if request.method == "POST":
        data = json.loads(request.body)
        appointment_id = data.get("appointment_id")
        item_name = data.get("item_name")
        quantity = int(data.get("quantity"))
        unit_price = int(data.get("unit_price"))

        try:
            appointment = Appointment.objects.get(id=appointment_id)
            AppointmentItem.objects.create(
                appointment=appointment,
                item_name=item_name,
                quantity=quantity,
                unit_price=unit_price
            )
            return JsonResponse({"success": True})
        except Appointment.DoesNotExist:
            return JsonResponse({"success": False, "error": "Appointment not found"})

    return JsonResponse({"success": False, "error": "Invalid request"})





def render_with_error(request, subcategory, booking_questions, time_slots, today, error_message):
    """Utility function to render the booking page with an error."""
    return render(request, 'book_now.html', {
        'subcategory': subcategory,
        'booking_questions': booking_questions,
        'time_slots': time_slots,
        'today': today,
        'error': error_message
    })


def is_service_provider_available(provider):
    """
    Checks if a service provider has any 'Pending' or 'In Progress' appointments.
    """
    overlapping_appointments = Appointment.objects.filter(
        service_provider=provider,
        status__in=["Pending", "In Progress"]
    )
    return not overlapping_appointments.exists()


def save_booking_answers(request, booking_questions, appointment):
    """
    Saves booking answers for a given appointment.
    """
    for question in booking_questions:
        answer_text = request.POST.get(f"question_{question.id}")
        if answer_text:
            BookingAnswer.objects.create(
                appointment=appointment,
                question=question,
                answer=answer_text
            )


@login_required
def get_time_slots(request):
    if request.method == "GET":
        selected_date = request.GET.get("date")
        if not selected_date:
            return JsonResponse({"error": "Date not provided"}, status=400)

        try:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid date format"}, status=400)

        now = datetime.now()
        today = now.date()
        current_time = now + timedelta(hours=1)

        time_slots = []
        if selected_date == today:
            if current_time.time() <= datetime.strptime("22:00", "%H:%M").time():
                while current_time.time() <= datetime.strptime("22:00", "%H:%M").time():
                    time_slots.append(current_time.strftime('%H'))
                    current_time += timedelta(hours=1)
        else:
            start_time = datetime.strptime("09:00", "%H:%M")
            while start_time.time() <= datetime.strptime("22:00", "%H:%M").time():
                time_slots.append(start_time.strftime('%H'))
                start_time += timedelta(hours=1)

        return JsonResponse({"time_slots": time_slots})
    return JsonResponse({"error": "Invalid request"}, status=400)



# Success page for the appointment
def appointment_success(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    return render(request, 'appointment_success.html', {'appointment': appointment})



from django.db.models.functions import TruncMonth
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import Appointment


import logging

logger = logging.getLogger(__name__)

@login_required
def service_provider_dashboard(request):
    if not request.user.is_service_provider:
        return render(request, '403.html')

    service_provider = request.user.service_provider_profile
    all_bookings = Appointment.objects.filter(service_provider=service_provider)

    # Calculate total earnings
    completed_appointments = all_bookings.filter(status='Completed')
    total_earnings = sum(
        appointment.price for appointment in completed_appointments if appointment.subsubcategory and appointment.subsubcategory.rate
    )

    # Calculate monthly booking counts
    monthly_bookings = (
        all_bookings.annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    months = [entry['month'].strftime('%B %Y') for entry in monthly_bookings]
    booking_counts = [entry['count'] for entry in monthly_bookings]

    # Calculate monthly earnings
    monthly_earnings = (
        all_bookings.filter(status='Completed')
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total_earnings=Sum('price'))
        .order_by('month')
    )
    months_earnings = [entry['month'].strftime('%B %Y') for entry in monthly_earnings]
    earnings = [entry['total_earnings'] for entry in monthly_earnings]

    # Handle status update
    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        appointment = get_object_or_404(Appointment, id=appointment_id, service_provider=service_provider)
        new_status = request.POST.get("status")
        if new_status in dict(Appointment.status.field.choices):
            appointment.status = new_status
            if new_status == 'Completed':
                appointment.completed_at = timezone.now()
            appointment.save()

    # Fetch notifications for new appointments
    new_appointments = all_bookings.filter(status='Pending').order_by('-date')
    notifications = [f"New appointment booked by {appointment.customer.user.username} on {appointment.date} at {appointment.time}" for appointment in new_appointments]

    all_services = SubCategory.objects.all()

    # Context data
    context = {
        'provider': service_provider,
        'total_bookings': all_bookings.count(),
        'current_works': all_bookings.filter(status__in=['Pending']),
        'going_works': all_bookings.filter(status__in=['In Progress']),
        'completed_bookings': completed_appointments,
        'total_earnings': total_earnings,
        'months': months,
        'booking_counts': booking_counts,
        'months_earnings': months_earnings,
        'earnings': earnings,
        'notifications': notifications,
        'all_services': all_services,
    }
    return render(request, 'sp_dashboard.html', context)


#customer dashboard
@login_required
def edit_customer_profile(request):
    customer = request.user.customer_profile
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = CustomerProfileForm(instance=customer)
    return render(request, 'c_profile.html', {'form': form})



from django.db.models import Prefetch
from django.shortcuts import render
from .models import Appointment, StarRating

def customer_bookings(request):
    # Get the logged-in user's customer instance
    customer = request.user.customer_profile  # Assumes a OneToOne relationship between User and Customer
    
    # Fetch appointments related to the logged-in customer
    appointments = Appointment.objects.filter(customer=customer).order_by('-date', '-time').prefetch_related(
        Prefetch(
            "service_provider__ratings",
            queryset=StarRating.objects.filter(user=request.user),
            to_attr="user_ratings"
        )
    )

    # Attach the latest rating given by the user to each appointment
    for appointment in appointments:
        appointment.latest_rating = (
            appointment.service_provider.user_ratings[0].rating 
            if appointment.service_provider.user_ratings else None
        )

    context = {
        'appointments': appointments
    }
    return render(request, 'c_bookings.html', context)



from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('index')  # Redirect to the home page
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})



# View to update customer pincode
@login_required
def update_pincode(request):
    if request.method == "POST":
        pincode = request.POST.get("pincode")
        if pincode and request.user.is_authenticated:
            customer = request.user.customer_profile
            customer.pincode = pincode
            customer.save()
            return JsonResponse({"success": True, "message": "Pincode updated successfully."})
        return JsonResponse({"success": False, "message": "Invalid pincode or user not authenticated."})
    return JsonResponse({"success": False, "message": "Invalid request method."})



@login_required
def edit_address(request):
    customer = request.user.customer_profile
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = AddressForm(instance=customer)
    return render(request, 'myaddress.html', {'form': form})

from django.shortcuts import redirect
from django.db.models.functions import ExtractMonth


@login_required
def update_services_offered(request):
    if request.method == 'POST':
        services_ids = request.POST.getlist('services')
        service_provider = request.user.service_provider_profile
        service_provider.services_offered.set(services_ids)
        service_provider.save()
        return redirect('sp_dashboard')
    return redirect('sp_dashboard')


  # Adjust based on your model name

def add_extra_pay(request, work_id):
    work = get_object_or_404(Appointment, id=work_id)

    if request.method == "POST":
        extra_pay = request.POST.get("extra_pay")
        work.extra_price = int(extra_pay)  # Update the price with the extra_pay
        work.payment_status = 'Extra'  
        work.save()
        return redirect("sp_dashboard")  # Redirect to the pending works page

    return render(request, "add_extra_pay.html", {"work": work})

def pay_now_extra(request, work_id):
    appointment = get_object_or_404(Appointment, id=work_id)
    
    # Update the price in the appointment table
    appointment.price += appointment.extra_price  # Assuming 'extra_pay' is a field
    appointment.payment_status = 'Paid'
    appointment.status = 'Completed'
    appointment.save()
    

    messages.success(request, "Payment successful! Price updated.")
    return redirect("customer_bookings")  # Redirect to the pending works page


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from .models import Appointment

def accept_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user.service_provider_profile != appointment.service_provider:
        messages.error(request, "You are not authorized to accept this appointment.")
        return redirect("sp_dashboard")

    appointment.status = "In Progress"
    appointment.save()
    messages.success(request, "Appointment accepted successfully!")
    
    return redirect("sp_dashboard")  # Adjust the redirection as needed


from django.contrib.auth import get_user_model

def decline_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.user.service_provider_profile != appointment.service_provider:
        messages.error(request, "You are not authorized to decline this appointment.")
        return redirect("service_provider_dashboard")

    # Find the next available service provider
    customer_pincode = appointment.customer.pincode
    next_provider = ServiceProvider.objects.filter(
        pincode=customer_pincode,
        services_offered=appointment.subcategory,
    ).exclude(id=appointment.service_provider.id).first()

    if next_provider:
        appointment.service_provider = next_provider
        messages.success(request, f"Appointment reassigned to {next_provider.user.username}.")
    else:
        appointment.status = "Pending"
        appointment.service_provider = None
        messages.warning(request, "No available service providers. Appointment set to pending.")

    appointment.save()
    return redirect("sp_dashboard")


from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.shortcuts import get_object_or_404
from .models import Appointment

def download_invoice(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{appointment.id}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, f"Invoice for Booking ID: {appointment.id}")
    p.drawString(100, 730, f"Customer: {appointment.customer}")
    p.drawString(100, 710, f"Service Provider: {appointment.service_provider}")
    p.drawString(100, 690, f"Date: {appointment.date}")
    p.drawString(100, 670, f"Time: {appointment.time}")
    p.drawString(100, 650, f"Status: {appointment.status}")
    p.drawString(100, 630, f"Amount: ₹{appointment.price}")
    

    p.showPage()
    p.save()
    
    return response


def admin_h(request):
    recent_bookings = Appointment.objects.all().order_by('-created_at')[:5]
    #get total number of bookings and revenue per month
    bookings = Appointment.objects.annotate(month=ExtractMonth("date")).values("month").annotate(count=Count("id"), revenue=Sum("price")).values("month", "count", "revenue")
    month = []
    total_bookings = []
    total_revenue = []
    for booking in bookings:
        month.append(calendar.month_name[booking["month"]])
        total_bookings.append(booking["count"])
        total_revenue.append(booking["revenue"])

    # Convert total_revenue to integers
    total_revenue = [int(revenue) for revenue in total_revenue]
    # Total number of appointments
    total_appointments = Appointment.objects.count()

    # Get top selling products
    top_subcategories = (
    SubCategory.objects
    .annotate(appointment_count=Count('appointments'))
    .order_by('-appointment_count')[:5]
)
    for subcategory in top_subcategories:
        subcategory.percentage = (subcategory.appointment_count / total_appointments * 100) if total_appointments > 0 else 0

    if request.method == 'POST':
        form = SubCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a project list view
            return redirect('admin_h')
        
    if request.method == 'POST':
        form2 = ServiceForm(request.POST)
        if form2.is_valid():
            form2.save()
            # Redirect to a project list view
            return redirect('admin_h')
    
    if request.method == 'POST':
        form3 = SubSubCategoryForm(request.POST)
        if form3.is_valid():
            form3.save()
            # Redirect to a project list view
            return redirect('admin_h')
    
    form = SubCategoryForm()
    form2 = ServiceForm()
    form3 = SubSubCategoryForm()
    customers = Customer.objects.count()
    service_providers = ServiceProvider.objects.count()
    services_count = Service.objects.count()
    context = {
        'bookings': bookings,
        'month': month,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'recent_bookings' : recent_bookings,
        'top_subcategories':top_subcategories,
        'form': form,
        'form2': form2,
        'form3': form3,
        'customers':customers,
        'service_providers':service_providers,
        'services_count':services_count
    }

    return render(request, 'adminUI/adminHome.html',context)

def service_providers(request):
    service_providers = ServiceProvider.objects.all()
    return render(request,"adminUI/users.html",{"service_providers":service_providers})

def customers(request):
    customers = Customer.objects.all()
    return render(request,"adminUI/customer.html",{"customers":customers})


def admin1_approvals(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = CustomUser.objects.get(id=user_id)
        user.is_approved = True
        user.save()
        messages.success(request, f"{user.username} has been approved successfully!")
        return redirect("admin_approvals")  # Redirect back after approval

    need_approvals = CustomUser.objects.filter(is_service_provider=True, is_approved=False)
    return render(request, "adminUI/approvals.html", {"need_approvals": need_approvals})



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StarRating, ServiceProvider
import json

@csrf_exempt  # Temporarily disable CSRF for simplicity (use a token for production)
def submit_rating(request):
    if request.method == "POST":
        data = json.loads(request.body)
        service_provider_id = data.get("service_provider_id")
        rating = data.get("rating")
        
        if not service_provider_id or not rating:
            return JsonResponse({"error": "Invalid data"}, status=400)
        
        service_provider = ServiceProvider.objects.get(id=service_provider_id)
        
        # Update or create the rating
        star_rating, created = StarRating.objects.update_or_create(
            user=request.user, 
            service_provider=service_provider,
            defaults={"rating": rating}
        )

        return JsonResponse({"message": "Rating submitted successfully", "rating": rating})
    
    return JsonResponse({"error": "Invalid request"}, status=400)


def all_services(request):
    services = Service.objects.all()
    return render(request,"all_services.html",{"services":services})

@login_required
def edit_service_provider_profile(request):
    service_provider = request.user.service_provider_profile
    if request.method == 'POST':
        form = ServiceProviderProfileForm(request.POST, instance=service_provider)
        if form.is_valid():
            form.save()
            return redirect('sp_dashboard')
    else:
        form = ServiceProviderProfileForm(instance=service_provider)
    return render(request, 'sp_profile.html', {'form': form})