# library/admin.py

from django.contrib import admin
from .models import Book, Loan, Genre, Location, Author
from django.utils import timezone
from datetime import timedelta 
from django.db.models import F
from django.template.defaultfilters import truncatechars
class BookInlineAuthors(admin.TabularInline):
    model = Book.authors.through # Untuk ManyToMany
    extra = 1 # Menampilkan 3 baris kosong sekaligus
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
# --- Register Location ---
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('shelf_name', 'description')
    search_fields = ('shelf_name',)
# --- Register Book ---
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    inlines = [BookInlineAuthors]
    list_display = ('name', )
    search_fields = ('name',)
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    save_as=True
    # Tambahkan 'location' ke dalam list_display
    list_display = ('title', 'short_description', 'location', 'stock','display_authors','publication_year') 
    
    # Tambahkan 'location' ke filter agar admin bisa memfilter buku berdasarkan Rak
    list_filter = ('publication_year', 'genre', 'location','authors')
    
    search_fields = ('title', 'description', 'authors', 'isbn')
    filter_horizontal = ('genre','authors') 
    # Fungsi untuk menampilkan daftar penulis di tabel admin (dipisahkan koma)
    def display_authors(self, obj):
        return ", ".join([a.name for a in obj.authors.all()])
    display_authors.short_description = 'Penulis'
    def get_genres(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])
    get_genres.short_description = 'Genre'

    def short_description(self, obj):
        return truncatechars(obj.description, 50)
    short_description.short_description = "Deskripsi"
    
    # Memberikan nama kolom di header tabel admin
    short_description.short_description = "Deskripsi"
from django.contrib import admin
from .models import Genre, Book, Loan, Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('book__title', 'user__username', 'comment')

# --- Register Loan ---
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'status', 'borrow_date', 'due_date', 'fine_amount','is_paid') 
    list_filter = ('status', 'due_date', 'borrow_date','is_paid') 
    raw_id_fields = ('book', 'member')
    actions = ['approve_loan', 'mark_as_returned', 'reject_loan','mark_fine_as_paid']
    # readonly_fields = ('fine_amount',) 
    
    fields = (
        ('book', 'member'), 
        ('status', 'borrow_date', 'due_date'),
        'return_date', 
        'fine_amount',
        'is_paid'
    )
    
    # Action Kustom: Menyetujui Peminjaman
    def approve_loan(self, request, queryset):
        loans_to_approve = queryset.filter(status='pending')
        
        for loan in loans_to_approve:
            if loan.book.stock > 0:
                loan.borrow_date = timezone.now().date()
                loan.due_date = loan.borrow_date + timedelta(days=7)
                loan.status = 'approved'
                loan.save()
                
                loan.book.stock =F('stock') - 1
                loan.book.save()
            else:
                self.message_user(request, f"Buku '{loan.book.title}' kehabisan stok. Peminjaman ini dilewati.", level='warning')

        self.message_user(request, f"Total {loans_to_approve.count()} peminjaman berhasil disetujui.")
    approve_loan.short_description = "Setujui Peminjaman (Kurangi Stok)"
    
    # Action Kustom: Menolak Peminjaman
    def reject_loan(self, request, queryset):
        loans_to_reject = queryset.filter(status='pending')
        loans_to_reject.update(status='rejected')
        self.message_user(request, f"Total {loans_to_reject.count()} pengajuan berhasil ditolak.")
    reject_loan.short_description = "Tolak Pengajuan"

    # Action Kustom: Pengembalian
    def mark_as_returned(self, request, queryset):
        loans_to_return = queryset.filter(status__in=['approved'])
        
        for loan in loans_to_return:
            if not loan.return_date:
                loan.return_date = timezone.now().date()
            
            loan.status = 'returned'
            loan.save() 
            
            loan.book.stock =F('stock') + 1
            loan.book.save()
            
        self.message_user(request, f"Total {loans_to_return.count()} peminjaman berhasil dikembalikan. Denda telah dihitung.")
    
    mark_as_returned.short_description = "Tandai sebagai Dikembalikan"

    def mark_fine_as_paid(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(request, f"{updated} peminjaman telah ditandai lunas.")
    mark_fine_as_paid.short_description = "Tandai denda sudah lunas"