from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.index,name="index"),
    path('customer/signup/', views.customer_signup, name='customer_signup'),
    path('customer/login/', views.customer_login, name='customer_login'),
    path('sp/signup/', views.service_provider_signup, name='seller_signup'),
    path('sp/login/', views.service_provider_login, name='service_provider_login'),
    path('logout/', views.logout_view, name='logout'),
    path('service/<int:service_id>/', views.sub, name='service_detail'),
    path('subcategory/<int:pk>/', views.subcategory_detail, name='subcategory_detail'),
    path('subcategory/<int:pk>/book-now/', views.book_now, name='book_now'),
    path('appointment/success/<int:pk>/', views.appointment_success, name='appointment_success'),
    path('subcategory/<int:pk>/detail/', views.subcategory_detail, name='subcategory_detail'),
     path('dashboard/', views.service_provider_dashboard, name='sp_dashboard'),
     path("get-time-slots/", views.get_time_slots, name="get_time_slots"),

     path('profile/edit/', views.edit_customer_profile, name='edit_profile'),
     path('c_bookings/', views.customer_bookings, name='customer_bookings'),
     path('password/change/', views.change_password, name='change_password'),
     path('update-pincode/', views.update_pincode, name='update_pincode'),
     path('edit-address/', views.edit_address, name='edit_address'),
     path('update-services-offered/', views.update_services_offered, name='update_services_offered'),

     path("add-extra-pay/<int:work_id>/", views.add_extra_pay, name="add_extra_pay"),
     path("pay-now/<int:work_id>/", views.pay_now_extra, name="pay_now"),

    path("appointment/<int:appointment_id>/accept/", views.accept_appointment, name="accept_appointment"),
    path("appointment/<int:appointment_id>/decline/", views.decline_appointment, name="decline_appointment"),

    path('invoice/<int:appointment_id>/', views.download_invoice, name='download_invoice'),
    path('admin1/',views.admin_h,name='admin_h'),
    path('service_providers/',views.service_providers,name="service_providers"),
    path('customers/',views.customers,name="customers"),

    path("admin1/approvals/", views.admin1_approvals, name="admin_approvals"),
    path('submit_rating/', views.submit_rating, name='submit_rating'),

    path('all_services/', views.all_services, name='all_services'),

    path('sp/profile/edit/', views.edit_service_provider_profile, name='sp_edit_profile'),
]

