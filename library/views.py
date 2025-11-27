# library/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Book, Loan

 
def book_list(request):
    """Menampilkan daftar semua buku yang tersedia."""
    books = Book.objects.filter(stock__gt=0).order_by('title') 
    context = {'books': books}
    return render(request, 'library/book_list.html', context)

@login_required
def request_loan(request, book_id):
    """Proses pengajuan peminjaman buku."""
    book = get_object_or_404(Book, pk=book_id)
    
    # Cek apakah user sudah memiliki pengajuan yang pending atau sedang dipinjam
    existing_loan = Loan.objects.filter(
        book=book, 
        member=request.user, 
        status__in=['pending', 'approved'] 
    ).exists()

    if existing_loan:
        return render(request, 'library/error.html', {'message': 'Anda sudah memiliki pengajuan peminjaman atau sedang meminjam buku ini.'})
        
    if book.stock > 0:
        # Buat entri peminjaman dengan status 'pending'
        Loan.objects.create(
            book=book,
            member=request.user,
            status='pending' 
        )
        return redirect('my_loans') 
    else:
        return render(request, 'library/error.html', {'message': 'Stok buku ini sedang kosong.'})

@login_required
def my_loans(request):
    """Menampilkan daftar buku yang sedang dipinjam oleh user saat ini."""
    loans = Loan.objects.filter(member=request.user).order_by('-id')
    context = {'loans': loans}
    return render(request, 'library/my_loans.html', context)