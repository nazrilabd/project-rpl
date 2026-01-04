from django.urls import path
from . import views

urlpatterns = [
 path('checkout/<int:loan_id>/', views.create_payment, name='checkout_midtrans'),
path('payment-callback/', views.payment_callback, name='payment_callback'),
path('webhook/midtrans/', views.midtrans_webhook, name='midtrans_webhook'),
]