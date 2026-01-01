# library/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='home'), 
    path('about/', views.about, name='about'),
    path('profile/', views.profile, name='profile'),
    path('login/', views.MyLoginView.as_view(), name='login'),
    path('books', views.book_list, name='book_list'), 
    path('request/<int:book_id>/', views.request_loan, name='request_loan'), 
    path('books/genre/<str:genre>/',views.book_list_by_genre,name="book_by_genre"),
    path('books/<int:pk>/',views.detail_buku,name="detail_book"),
    path('books/<int:book_id>/review/', views.submit_review, name='submit_review'),
    path('books/search',views.search_books,name="search"),
    path('my-loans', views.my_loans, name='my_loans'), 
    path('loan/cancel/<int:loan_id>/', views.cancel_loan, name='cancel_loan'),
]