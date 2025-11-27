# library/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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
    author = models.CharField(max_length=100, verbose_name="Penulis")
    isbn = models.CharField(max_length=13, unique=True, verbose_name="ISBN")
    publication_year = models.IntegerField(verbose_name="Tahun Terbit")
    stock = models.IntegerField(default=1, verbose_name="Stok Tersedia")

    class Meta:
        verbose_name = "Buku"
        verbose_name_plural = "Daftar Buku"

    def __str__(self):
        return self.title

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
    
    fine_amount = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0.00, 
        verbose_name="Jumlah Denda (Rp)"
    )

    class Meta:
        verbose_name = "Peminjaman"
        verbose_name_plural = "Daftar Peminjaman"
        
    def __str__(self):
        return f"{self.member.username} ({self.status}) meminjam {self.book.title}"

    def calculate_fine(self):
        # Rp 1.000 per hari
        FINE_PER_DAY = 1000  
        
        if self.status == 'returned' and self.return_date and self.due_date:
            if self.return_date > self.due_date:
                delay = (self.return_date - self.due_date).days
                fine = delay * FINE_PER_DAY
                return float(fine)
        return 0.00
            
    def save(self, *args, **kwargs):
        if self.status == 'returned' and not self.fine_amount and self.return_date:
            self.fine_amount = self.calculate_fine()
        super().save(*args, **kwargs)