# library/models.py

from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

# --- 1. Master Data Models ---

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nama Genre")

    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Kategori Genre"

    def __str__(self):
        return self.name


class Location(models.Model):
    shelf_name = models.CharField(max_length=50, unique=True, verbose_name="Nama Rak/Lokasi")
    description = models.TextField(blank=True, verbose_name="Keterangan Tambahan")

    class Meta:
        verbose_name = "Lokasi"
        verbose_name_plural = "Daftar Lokasi/Rak"

    def __str__(self):
        return self.shelf_name


class Author(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nama Penulis")

    class Meta:
        verbose_name = "Penulis"
        verbose_name_plural = "Daftar Penulis"

    def __str__(self):
        return self.name


# --- 2. Core Book Model ---

class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="Judul Buku")
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True, verbose_name="Sampul Buku")
    genre = models.ManyToManyField(Genre, related_name='books', verbose_name="Genre") 
    authors = models.ManyToManyField(Author, related_name='books', verbose_name="Penulis")
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='books', verbose_name="Lokasi Rak"
    )
    description = models.TextField(verbose_name="Deskripsi Buku")
    isbn = models.CharField(max_length=13, default='-', verbose_name="ISBN")
    publication_year = models.IntegerField(verbose_name="Tahun Terbit")
    stock = models.IntegerField(default=0, verbose_name="Stok Tersedia")

    class Meta:
        verbose_name = "Buku"
        verbose_name_plural = "Daftar Buku"

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    @property
    def total_reviews(self):
        return self.reviews.count()


# --- 3. Interaction Models ---

class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name="Buku")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Pengguna")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5, verbose_name="Rating")
    comment = models.TextField(verbose_name="Isi Review")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Review")

    class Meta:
        verbose_name = "Review Buku"
        verbose_name_plural = "Daftar Review"
        unique_together = ('book', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} ({self.rating}/5)"


class Loan(models.Model):
    LOAN_STATUS = (
        ('pending', 'Menunggu Persetujuan'),
        ('approved', 'Disetujui / Sedang Dipinjam'),
        ('rejected', 'Ditolak'),
        ('returned', 'Sudah Dikembalikan'),
    )

    FINE_PER_DAY = 1000  # Konstanta tarif denda

    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="Buku Dipinjam")
    member = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Anggota Peminjam")
    status = models.CharField(max_length=10, choices=LOAN_STATUS, default='pending', verbose_name="Status Peminjaman")
    
    borrow_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Peminjaman")
    due_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Jatuh Tempo")
    return_date = models.DateField(null=True, blank=True, verbose_name="Tanggal Pengembalian")
    
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Jumlah Denda (Rp)")
    is_paid = models.BooleanField(default=False, verbose_name="Denda Sudah Dibayar")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Peminjaman"
        verbose_name_plural = "Daftar Peminjaman"

    def __str__(self):
        return f"{self.member.username} - {self.book.title} ({self.get_status_display()})"

    @property
    def current_fine(self):
        """Menghitung denda berjalan (real-time) jika terlambat."""
        if self.status == 'returned':
            return float(self.fine_amount)
            
        if self.status == 'approved' and self.due_date:
            today = date.today()
            if today > self.due_date:
                delay = (today - self.due_date).days
                return delay * self.FINE_PER_DAY
        return 0

    def calculate_final_fine(self):
        """Menghitung denda tetap saat buku dikembalikan."""
        if self.return_date and self.due_date and self.return_date > self.due_date:
            delay = (self.return_date - self.due_date).days
            return delay * self.FINE_PER_DAY
        return 0

    def save(self, *args, **kwargs):
        # Otomatis hitung denda jika status berubah jadi returned
        if self.status == 'returned' and self.return_date:
            self.fine_amount = self.calculate_final_fine()
        super().save(*args, **kwargs)

    @staticmethod
    def can_user_borrow(user):
        """Cek kelayakan user: tidak ada denda unpaid dan tidak ada buku overdue."""
        has_unpaid = Loan.objects.filter(member=user, is_paid=False, fine_amount__gt=0).exists()
        has_overdue = Loan.objects.filter(member=user, status='approved', due_date__lt=date.today()).exists()
        return not (has_unpaid or has_overdue)