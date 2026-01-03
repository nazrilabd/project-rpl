# library/views.py

from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.dispatch import receiver
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum, Q, Avg, Value
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator

from .models import Book, Loan, Review, Location, Author, Genre

# --- AUTHENTICATION VIEWS ---

class MyPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'registration/change_password.html'
    success_url = reverse_lazy('profile')
    success_message = "Password Anda berhasil diperbarui!"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Menjaga agar session tetap aktif setelah ganti password
        update_session_auth_hash(self.request, form.user)
        return response

@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    messages.success(request, f"Selamat datang kembali, {user.username}!")

@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    messages.success(request, "Anda telah berhasil keluar. Sampai jumpa lagi!")

# --- GENERAL PAGES ---

def welcome(request):
    return render(request, 'pages/welcome.html')

def about(request):
    return render(request, 'pages/about.html')

# --- BOOK COLLECTION ---

def book_list(request):
    # 1. Ambil data dasar dengan anotasi rating
    books = Book.objects.all().annotate(
        rating_rata2=Coalesce(Avg('reviews__rating'), Value(0.0))
    )
    
    # 2. Tangkap parameter filter
    query = request.GET.get('q')
    genre_id = request.GET.get('genre')
    author_id = request.GET.get('author')
    location_id = request.GET.get('location')
    sort = request.GET.get('sort')

    # 3. Logika Pencarian & Filter
    if query:
        books = books.filter(Q(title__icontains=query) | Q(isbn__icontains=query))
    if genre_id:
        books = books.filter(genre__id=genre_id)
    if author_id:
        books = books.filter(authors__id=author_id)
    if location_id:
        books = books.filter(location__id=location_id)

    # 4. Logika Sorting
    if sort == 'rating':
        books = books.order_by('-rating_rata2', 'title')
    elif sort == 'newest':
        books = books.order_by('-id')
    else:
        books = books.order_by('title')

    # 5. Pagination
    paginator = Paginator(books, 12)
    page_number = request.GET.get('page') or 1
    books_page = paginator.get_page(page_number)

    context = {
        'books': books_page,
        'books_count': books.count(),
        'genres': Genre.objects.all(),
        'authors': Author.objects.all(),
        'locations': Location.objects.all(),
        'title': "Daftar Koleksi"
    }
    return render(request, 'pages/book_list.html', context)

def detail_buku(request, pk):
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all().order_by('-created_at')
    return render(request, 'pages/detail_book.html', {
        'book': book, 
        'reviews': reviews
    })

# --- USER PROFILE & LOANS ---

@login_required
def profile(request):
    current_loans = Loan.objects.filter(member=request.user, status='approved').order_by('due_date')
    
    # Perhitungan denda
    fixed_fine = Loan.objects.filter(
        member=request.user, is_paid=False
    ).aggregate(Sum('fine_amount'))['fine_amount__sum'] or 0
    
    running_fine = sum(loan.current_fine for loan in current_loans)
    total_fine = fixed_fine + running_fine
    
    context = {
        'current_loans': current_loans,
        'current_loans_count': current_loans.count(),
        'loan_limit': 5,
        'total_fine': total_fine,
        'has_fine': not Loan.can_user_borrow(request.user),
        'today': date.today(),
    }
    return render(request, 'pages/profile.html', context)

@login_required
def request_loan(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    active_loans = Loan.objects.filter(member=request.user, status__in=['pending', 'approved'])
    
    # Validasi
    if not Loan.can_user_borrow(request.user):
        messages.error(request, 'Anda memiliki denda yang belum dibayar.')
    elif active_loans.count() >= 5:
        messages.error(request, "Batas maksimal peminjaman adalah 5 buku.")
    elif active_loans.filter(book=book).exists():
        messages.error(request, 'Anda sudah mengajukan atau sedang meminjam buku ini.')
    elif book.stock <= 0:
        messages.error(request, 'Stok buku sedang kosong.')
    else:
        Loan.objects.create(book=book, member=request.user, status='pending')
        messages.success(request, 'Peminjaman berhasil diajukan!')
        return redirect('my_loans')

    return redirect('detail_book', pk=book_id)

@login_required
def my_loans(request):
    loans_list = Loan.objects.filter(member=request.user).order_by('-id')
    
    status_filter = request.GET.get('status')
    if status_filter:
        loans_list = loans_list.filter(status=status_filter)
        
    paginator = Paginator(loans_list, 8)
    page_number = request.GET.get('page') or 1
    loans = paginator.get_page(page_number)
    
    active_count = Loan.objects.filter(member=request.user, status__in=['pending', 'approved']).count()
    
    return render(request, 'pages/my_loans.html', {
        'loans': loans, 
        'active_loans_count': active_count
    })

@login_required
def cancel_loan(request, loan_id):
    loan = get_object_or_404(Loan, pk=loan_id, member=request.user)
    if loan.status == 'pending':
        loan.delete()
        messages.success(request, "Pengajuan berhasil dibatalkan.")
    else:
        messages.error(request, "Hanya pengajuan pending yang dapat dibatalkan.")
    return redirect('my_loans')

@login_required
def submit_review(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        if Review.objects.filter(book=book, user=request.user).exists():
            messages.error(request, "Anda sudah memberikan review untuk buku ini.")
        else:
            Review.objects.create(
                book=book, user=request.user,
                rating=request.POST.get('rating'),
                comment=request.POST.get('comment')
            )
            messages.success(request, "Review berhasil dikirim!")
    return redirect('detail_book', pk=book_id)