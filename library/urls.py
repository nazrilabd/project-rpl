# library/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'), 
    path('request/<int:book_id>/', views.request_loan, name='request_loan'), 
    path('my-loans/', views.my_loans, name='my_loans'), 
]