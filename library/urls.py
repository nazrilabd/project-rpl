# library/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='home'), 
    path('request/<int:book_id>/', views.request_loan, name='request_loan'), 
    path('books/genre/<str:genre>/',views.book_list_by_genre,name="book_by_genre"),
    path('books/<int:pk>/',views.detail_buku,name="detail_book"),
    path('books/search',views.search_books,name="search"),
    path('my-loans/', views.my_loans, name='my_loans'), 
]