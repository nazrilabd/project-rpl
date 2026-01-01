# library/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg
from datetime import date

# --- Model Genre ---
class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nama Genre")

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Kategori Genre"

    def __str__(self):
        return self.name

# --- Model Book ---
class Book(models.Model):
    # Field Baru: Cover Image
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True, verbose_name="Sampul Buku")
    
    genre = models.ManyToManyField(Genre, related_name='books', verbose_name="Genre") 
    title = models.CharField(max_length=200, verbose_name="Judul Buku")
    description = models.TextField(verbose_name="Deskripsi Buku")
    author = models.CharField(max_length=100, verbose_name="Penulis")
    isbn = models.CharField(default='_',max_length=13, verbose_name="ISBN")
    publication_year = models.IntegerField(verbose_name="Tahun Terbit")
    stock = models.IntegerField(default=0, verbose_name="Stok Tersedia")
    @property
    def average_rating(self):
        # Menghitung rata-rata rating dari model Review yang terhubung
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    @property
    def total_reviews(self):
        return self.reviews.count()
    
    class Meta:
        verbose_name = "Buku"
        verbose_name_plural = "Daftar Buku"

    def __str__(self):
        return self.title
    
# --- Model Review ---
class Review(models.Model):
    # Cukup gunakan angka 1-5
    RATING_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="Buku")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Pengguna")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5, verbose_name="Rating")
    comment = models.TextField(verbose_name="Isi Review")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Review")

    class Meta:
        verbose_name = "Review Buku"
        verbose_name_plural = "Daftar Review"
        # Mencegah satu user memberikan lebih dari satu review pada buku yang sama
        unique_together = ('book', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating}/5)"
# --- Model Loan ---
class Loan(models.Model):
    # Pilihan Status Peminjaman
    LOAN_STATUS = (
        ('pending', 'Menunggu Persetujuan'),
        ('approved', 'Disetujui / Sedang Dipinjam'),
        ('rejected', 'Ditolak'),
        ('returned', 'Sudah Dikembalikan'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Buku Dipinjam")
    member = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Anggota Peminjam")
    
    status = models.CharField(
        max_length=10,
        choices=LOAN_STATUS,
        default='pending',
        verbose_name="Status Peminjaman"
    )
  
    borrow_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Peminjaman")
    due_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Jatuh Tempo")
    return_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Pengembalian")
    is_paid = models.BooleanField(default=False, verbose_name="Denda Sudah Dibayar")
    fine_amount = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Jumlah Denda (Rp)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Peminjaman"
        verbose_name_plural = "Daftar Peminjaman"
        
    def __str__(self):
        return f"{self.member.username} ({self.status}) meminjam {self.book.title}"
    @staticmethod
    def can_user_borrow(user):
        """
        Mengecek apakah user boleh meminjam buku.
        Syarat: Tidak ada denda yang belum dibayar (is_paid=False)
        dan denda tersebut > 0.
        """
        # Cek denda dari buku yang sudah dikembalikan tapi belum dibayar
        unpaid_fines = Loan.objects.filter(
            member=user, 
            is_paid=False, 
            fine_amount__gt=0
        ).exists()
        
        # Cek juga apakah ada buku yang sedang dipinjam (approved) tapi sudah telat (due_date < today)
        overdue_books = Loan.objects.filter(
            member=user,
            status='approved',
            due_date__lt=date.today()
        ).exists()

        if unpaid_fines or overdue_books:
            return False
        return True
    def calculate_fine(self):
        # Rp 1.000 per hari
        FINE_PER_DAY = 1000  
        
        if self.status == 'returned' and self.return_date and self.due_date:
            if self.return_date > self.due_date:
                delay = (self.return_date - self.due_date).days
                fine = delay * FINE_PER_DAY
                return float(fine)
        return 0.00
    @property
    def current_fine(self):
        """Menghitung denda berjalan jika buku belum dikembalikan dan sudah lewat tempo."""
        FINE_PER_DAY = 1000
        
        # Jika sudah dikembalikan, gunakan denda yang sudah tercatat tetap
        if self.status == 'returned':
            return self.fine_amount
            
        # Jika belum dikembalikan (approved) dan sudah lewat jatuh tempo
        if self.status == 'approved' and self.due_date:
            today = date.today()
            if today > self.due_date:
                delay = (today - self.due_date).days
                return delay * FINE_PER_DAY
                
        return 0
    def save(self, *args, **kwargs):
        if self.status == 'returned' and not self.fine_amount and self.return_date:
            self.fine_amount = self.calculate_fine()
        super().save(*args, **kwargs)