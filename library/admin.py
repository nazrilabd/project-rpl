# library/admin.py

from django.contrib import admin
from .models import Book, Loan, Genre
from django.utils import timezone
from datetime import timedelta 

# --- Register Genre ---
@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# --- Register Book ---
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'get_genres', 'isbn', 'stock') 
    search_fields = ('title', 'author', 'isbn')
    list_filter = ('author', 'publication_year', 'genre')
    
    def get_genres(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])
    get_genres.short_description = 'Genre'

# --- Register Loan ---
@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'member', 'status', 'borrow_date', 'due_date', 'fine_amount') 
    list_filter = ('status', 'due_date', 'borrow_date') 
    raw_id_fields = ('book', 'member')
    actions = ['approve_loan', 'mark_as_returned', 'reject_loan']
    readonly_fields = ('fine_amount',) 
    
    fields = (
        ('book', 'member'), 
        ('status', 'borrow_date', 'due_date'),
        'return_date', 
        'fine_amount'
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
                
                loan.book.stock -= 1
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
            
            loan.book.stock += 1
            loan.book.save()
            
        self.message_user(request, f"Total {loans_to_return.count()} peminjaman berhasil dikembalikan. Denda telah dihitung.")
    
    mark_as_returned.short_description = "Tandai sebagai Dikembalikan"