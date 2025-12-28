# library/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Book, Loan, Review
from django.core import serializers
from django.core.paginator import Paginator
from django.db.models import Q,Avg
from django.contrib import messages
 
def welcome(request):
    return render(request, 'pages/welcome.html')
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
    return render(request, 'pages/book_list.html', context)
def detail_buku(request, pk):
    # Mengambil objek Buku yang memiliki pk yang cocok.
    # Jika tidak ditemukan, otomatis menampilkan halaman 404 (Not Found).
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all().order_by('-created_at')
    context = {
        'book': book,
        'reviews': reviews
    }

    return render(request, 'pages/detail_book.html', context)

@login_required
def submit_review(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        # Validasi sederhana: Cek apakah user sudah pernah review buku ini
        existing_review = Review.objects.filter(book=book, user=request.user).exists()
        
        if existing_review:
            messages.error(request, "Anda sudah memberikan review untuk buku ini.")
        else:
            Review.objects.create(
                book=book,
                user=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Review berhasil dikirim!")
            
        return redirect('detail_book', pk=book.id)
    
    return redirect('detail_book', pk=book.id)


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
    
    books = Book.objects.filter(lookup).order_by('title').annotate(rating_rata2=Avg('reviews__rating'))
    
    sort_param = request.GET.get('sort')

    if sort_param == 'newest':
        books = books.order_by('-id') # Pastikan ada field created_at
    elif sort_param == 'rating':
        # Mengurutkan berdasarkan average_rating (asumsi field sudah ada di model)
        books = books.order_by('-rating_rata2')
    elif sort_param == 'title':
        books = books.order_by('title')
  
    paginator = Paginator(books, 3) 
    
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

        
        
    if book.stock > 0:
        # Buat entri peminjaman dengan status 'pending'
        Loan.objects.create(
            book=book,
            member=request.user,
            status='pending' 
        )
        messages.success(request,  'Peminjaman buku berhasil diajukan')
        return redirect('my_loans') 
    else:
        messages.error(request,  'Stok buku ini sedang kosong.')
    if existing_loan:
        messages.error(request, 'Anda sudah memiliki pengajuan peminjaman atau sedang meminjam buku ini.')
        
    return redirect('detail_book',pk=book_id)

@login_required
def my_loans(request):
    """Menampilkan daftar buku yang sedang dipinjam oleh user saat ini."""
    loans = Loan.objects.filter(member=request.user).order_by('-id')
    status_filter = request.GET.get('status')
    if status_filter:
        loans = loans.filter(status=status_filter)
    paginator = Paginator(loans, 8) 
    
    # 3. Ambil nomor halaman dari parameter GET URL (contoh: ?page=2)
    # Jika tidak ada parameter 'page', default ke halaman 1
    page_number = request.GET.get('page') or 1
    
    # 4. Dapatkan objek Page untuk halaman yang diminta
    loans = paginator.get_page(page_number)
    context = {'loans': loans}
    print(loans)
    return render(request, 'pages/my_loans.html', context)


# library/views.py

@login_required
def cancel_loan(request, loan_id):
    """Membatalkan pengajuan peminjaman oleh user."""
    # Pastikan peminjaman milik user yang login dan statusnya masih pending
    loan = get_object_or_404(Loan, pk=loan_id, member=request.user)

    if loan.status == 'pending':
        # Jika Anda ingin menghapus datanya sama sekali:
        loan.delete()
        
        # ATAU jika ingin statusnya berubah jadi 'cancelled' (lebih disarankan untuk history):
        # loan.status = 'cancelled'
        # loan.save()
        messages.success(request,"Pengajuan peminjaman berhasil dibatalkan")
        return redirect('my_loans')
    else:
        # Jika sudah disetujui (approved), user tidak boleh asal batal
        return render(request, 'library/error.html', {
            'message': 'Peminjaman yang sudah disetujui tidak dapat dibatalkan. Silakan hubungi admin.'
        })