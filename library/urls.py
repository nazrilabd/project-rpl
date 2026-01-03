# library/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import MyPasswordChangeView

urlpatterns = [
    path('', views.welcome, name='home'), 
    path('about/', views.about, name='about'),
    path('user/profile/', views.profile, name='profile'),
    path('books', views.book_list, name='book_list'), 
    path('request/<int:book_id>/', views.request_loan, name='request_loan'), 
   
    path('books/<int:pk>/',views.detail_buku,name="detail_book"),
    path('books/<int:book_id>/review/', views.submit_review, name='submit_review'),

    path('my-loans', views.my_loans, name='my_loans'), 
    path('loan/cancel/<int:loan_id>/', views.cancel_loan, name='cancel_loan'),
    path('user/change-password/',MyPasswordChangeView.as_view(), name='change_password'),
]