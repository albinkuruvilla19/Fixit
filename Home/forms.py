from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *

class CustomerSignUpForm(UserCreationForm):
    fname = forms.CharField(max_length=100)
    lname = forms.CharField(max_length=100)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'fname', 'lname', 'email', 'phone', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_customer = True  # Assuming you have an is_customer field in your CustomUser model
        user.is_approved = True
        if commit:
            user.save()
            customer = Customer.objects.create(
                user=user,
                fname=self.cleaned_data['fname'],
                lname=self.cleaned_data['lname'],
                email=self.cleaned_data['email'],
                phone=self.cleaned_data['phone']
            )
        return user


from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, ServiceProvider

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, ServiceProvider, Designation

class ServiceProviderSignUpForm(UserCreationForm):
    # Fields for ServiceProvider model
    designation = forms.ModelChoiceField(
        queryset=Designation.objects.all(),  # Fetch all available designations
        empty_label="Select a designation"
    )
    city = forms.CharField(max_length=100)
    pincode = forms.CharField(max_length=10)
    phone = forms.CharField(max_length=20)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_service_provider = True  # Assuming you have an is_service_provider field in your CustomUser model
        if commit:
            user.save()
            # Create the ServiceProvider instance
            ServiceProvider.objects.create(
                user=user,
                designation=self.cleaned_data['designation'],  # This will be a Designation instance
                city=self.cleaned_data['city'],
                pincode=self.cleaned_data['pincode'],
                email=user.email,  # Assuming the email comes from the user model
                phone=self.cleaned_data['phone']
            )
        return user

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')


    

class CustomerLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class ServiceProviderLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


from django import forms
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['date', 'time']


from django import forms
from .models import Appointment
from django.utils.timezone import now

class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status']

    def save(self, commit=True):
        appointment = super().save(commit=False)
        if appointment.status == 'Completed' and not appointment.completed_at:
            appointment.completed_at = now()
        if commit:
            appointment.save()
        return appointment


class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['fname', 'lname', 'email', 'phone']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Enter a valid 10-digit phone number.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Customer.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email already in use.")
        return email

class AddressForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['address', 'pincode']

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if not pincode.isdigit() or len(pincode) != 6:
            raise forms.ValidationError("Enter a valid 6-digit pincode.")
        return pincode
    



class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = "__all__"

class SubSubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubSubCategory
        fields = "__all__"

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = "__all__"


class ServiceProviderProfileForm(forms.ModelForm):
    class Meta:
        model = ServiceProvider
        fields = ['name', 'designation','services_offered', 'city','pincode', 'phone', 'email']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            raise forms.ValidationError("Enter a valid 10-digit phone number.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Customer.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email already in use.")
        return email