# library/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Book, Loan
from django.core import serializers
from django.core.paginator import Paginator
from django.db.models import Q
 
def book_list(request):
    """Menampilkan daftar semua buku yang tersedia."""
    books = Book.objects.order_by('title') 
    paginator = Paginator(books, 12) 
    
    # 3. Ambil nomor halaman dari parameter GET URL (contoh: ?page=2)
    # Jika tidak ada parameter 'page', default ke halaman 1
    page_number = request.GET.get('page') or 1
    
    # 4. Dapatkan objek Page untuk halaman yang diminta
    halaman_buku = paginator.get_page(page_number)
    context = {'books': halaman_buku}
    print(books)
    return render(request, 'pages/homepage.html', context)
def detail_buku(request, pk):
    # Mengambil objek Buku yang memiliki pk yang cocok.
    # Jika tidak ditemukan, otomatis menampilkan halaman 404 (Not Found).
    books = get_object_or_404(Book, pk=pk)
    
    context = {
        'book': books
    }
    print(context)
    
    return render(request, 'pages/detail_book.html', context)
def book_list_by_genre(request,genre):
    books = Book.objects.filter(genre__name=genre).order_by('title')
    paginator = Paginator(books, 12) 
    
    # 3. Ambil nomor halaman dari parameter GET URL (contoh: ?page=2)
    # Jika tidak ada parameter 'page', default ke halaman 1
    page_number = request.GET.get('page') or 1
    
    # 4. Dapatkan objek Page untuk halaman yang diminta
    halaman_buku = paginator.get_page(page_number)
    context ={
        "genre":genre,
        "books":halaman_buku,
        "title_heading":f"Daftar Buku Dengan Genre  {genre}"
    }
    return render(request,'pages/book_by_genre.html',context)
def search_books(request):
    query = request.GET.get("query")
    lookup = Q(title__icontains=query) | Q(author__icontains=query)

    books = Book.objects.filter(lookup).order_by('title')
  
    paginator = Paginator(books, 12) 
    
    # 3. Ambil nomor halaman dari parameter GET URL (contoh: ?page=2)
    # Jika tidak ada parameter 'page', default ke halaman 1
    page_number = request.GET.get('page') or 1
    
    # 4. Dapatkan objek Page untuk halaman yang diminta
    halaman_buku = paginator.get_page(page_number)
    context ={
        "query":query,
        "books":halaman_buku,
        "title_heading":f"Hasil Pencarian {query} "
    }
    return render(request,'library/search.html',context)
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
    paginator = Paginator(loans, 8) 
    
    # 3. Ambil nomor halaman dari parameter GET URL (contoh: ?page=2)
    # Jika tidak ada parameter 'page', default ke halaman 1
    page_number = request.GET.get('page') or 1
    
    # 4. Dapatkan objek Page untuk halaman yang diminta
    loans = paginator.get_page(page_number)
    context = {'loans': loans}
    return render(request, 'pages/my_loans.html', context)