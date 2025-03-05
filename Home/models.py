from django.db import models
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from datetime import timedelta, datetime
from django.utils.timezone import make_aware


from django.urls import reverse
# Create your models here.

class CustomUser(AbstractUser):
    # Add any additional fields you need
    is_customer = models.BooleanField(default=False)
    is_service_provider = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False,blank=True,null=True)

    class Meta:
        unique_together = ('username', 'email')

CustomUser = get_user_model()

class Designation(models.Model):
    name = models.CharField(max_length=100, default="name")

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.service.name} - {self.name}"
    
class SubSubCategory(models.Model):
    service = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='subsubcategories')
    name = models.CharField(max_length=255)
    rate = models.PositiveIntegerField(null=True,blank=True)

    def __str__(self):
        return f"{self.name}"

class ServiceProvider(models.Model):
    user = models.OneToOneField(
        'CustomUser',
        on_delete=models.CASCADE,
        related_name='service_provider_profile'
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.CASCADE,
        null=True,
        related_name='service_providers'
    )
    name = models.CharField(max_length=100,blank=True,null=True)
    services_offered = models.ManyToManyField(SubCategory, related_name='service_providers')
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10, default='0000',null=True,blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} - {self.designation}"

class Customer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='customer_profile')
    fname = models.CharField(max_length=100)
    lname = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address =  models.CharField(max_length=100,blank=True,null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.user.username



class Appointment(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer')
    service_provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='appointments')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='appointments')
    subsubcategory = models.ForeignKey(SubSubCategory, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    date = models.DateField()
    time = models.TimeField()  
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Accepted', 'Accepted'),
            ('Declined', 'Declined'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled')
        ],
        default='Pending'
    )

    price = models.PositiveIntegerField(null=True, blank=True)
    extra_price = models.PositiveIntegerField(null=True, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('Payment Pending', 'Payment Pending'),
            ('Extra','Extra'),
            ('Paid', 'Paid')
        ],
        default='Payment Pending'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def get_invoice_url(self):
        return reverse('download_invoice', args=[self.id])

    def update_total_price(self):
        """Calculate and update the total price from additional items"""
        total_price = sum(item.total_price() for item in self.items.all())
        self.price = total_price
        self.save()

class AppointmentItem(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()

    def total_price(self):
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        """Override save method to update the appointment's total price"""
        super().save(*args, **kwargs)
        self.appointment.update_total_price()


    def __str__(self):
        return f"{self.customer.user.username} -> {self.service_provider.user.username} ({self.date} {self.time})"

    def is_available(self):
        """
        Checks if the service provider is available for the given appointment date and time.
        """
        overlapping_appointments = Appointment.objects.filter(
            service_provider=self.service_provider,
            date=self.date,
            time=self.time,
            status__in=['Pending', 'In Progress']
        ).exclude(pk=self.pk)
        return not overlapping_appointments.exists()

    @staticmethod
    def get_available_time_slots(service_provider, date):
        """
        Fetch available time slots for a specific service provider on a given date.
        Assumes time slots are hourly intervals between 9 AM and 10 PM.
        """
        start_time = datetime.strptime("09:00", "%H:%M").time()
        end_time = datetime.strptime("22:00", "%H:%M").time()

        # Collect all time slots for the day
        time_slots = []
        current_time = datetime.combine(date, start_time)

        while current_time.time() <= end_time:
            time_slots.append(current_time.time())
            current_time += timedelta(hours=1)

        # Exclude time slots with existing appointments
        existing_appointments = Appointment.objects.filter(
            service_provider=service_provider,
            date=date,
            status__in=['Pending', 'In Progress']
        ).values_list('time', flat=True)

        available_slots = [slot for slot in time_slots if slot not in existing_appointments]

        return available_slots


class FAQ(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='faqs')
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return f"FAQ for {self.service.name}: {self.question}"

class StarRating(models.Model):
    service_provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField()  # e.g., 1 to 5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.service_provider.name} by {self.user.username if self.user else 'Anonymous'}"

class BookingQuestion(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='booking_questions')
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name='questions', blank=True, null=True)
    question_text = models.TextField()
    is_required = models.BooleanField(default=True)
    has_options = models.BooleanField(default=False)  # Indicates if the question has predefined options

    def __str__(self):
        return f"Booking Question for {self.service.name}: {self.question_text}"


class QuestionOption(models.Model):
    question = models.ForeignKey(BookingQuestion, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)

    def __str__(self):
        return f"Option for '{self.question.question_text}': {self.option_text}"


class BookingAnswer(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(BookingQuestion, on_delete=models.CASCADE)
    answer = models.TextField()  # Stores the text or selected option

    def __str__(self):
        return f"Answer to {self.question.question_text} for appointment {self.appointment.id}"
