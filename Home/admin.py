from django.contrib import admin
from .models import *


admin.site.register(CustomUser)
admin.site.register(Service)
admin.site.register(SubCategory)
admin.site.register(ServiceProvider)
admin.site.register(Customer)
admin.site.register(Appointment)
admin.site.register(FAQ)
admin.site.register(StarRating)
admin.site.register(BookingQuestion)
admin.site.register(BookingAnswer)
admin.site.register(QuestionOption)
admin.site.register(Designation)
admin.site.register(SubSubCategory)
admin.site.register(AppointmentItem)