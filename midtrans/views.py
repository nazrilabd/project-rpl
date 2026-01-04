import json
import midtransclient
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from library.models import Loan
from datetime import datetime

# Konfigurasi Midtrans
snap = midtransclient.Snap(
    is_production=settings.IS_PRODUCTION,
    server_key=settings.MIDTRANS_SERVER_KEY,
    client_key=settings.MIDTRANS_CLIENT_KEY
)

@login_required
def create_payment(request, loan_id):
    loan = get_object_or_404(Loan, pk=loan_id, member=request.user)
    
    if loan.status != 'returned':
        return JsonResponse({'error': 'Buku harus dikembalikan terlebih dahulu.'}, status=400)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    amount = int(loan.fine_amount)
    order_id = f"FINE-{loan.id}-{timestamp}"
    print(order_id)
    param = {
        "transaction_details": {"order_id": order_id, "gross_amount": amount},
        "item_details": [{"id": str(loan.id), "price": amount, "quantity": 1, "name": f"Denda: {loan.book.title[:20]}"}],
        "customer_details": {"first_name": loan.member.username, "email": loan.member.email}
    }

    try:
        transaction = snap.create_transaction(param)
        return JsonResponse({'token': transaction['token']})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def midtrans_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        order_id_raw = data.get('order_id')
        status = data.get('transaction_status')
        
        try:
            loan_id = order_id_raw.split('-')[1]
            loan = Loan.objects.get(id=loan_id)
            if status in ['settlement', 'capture']:
                loan.is_paid = True
                loan.save()
            return HttpResponse(status=200)
        except:
            return HttpResponse(status=404)
    return HttpResponse(status=405)

# Handler untuk memicu Django Messages
def payment_callback(request):
    status = request.GET.get('status')
    if status == 'success':
        messages.success(request, "Terima kasih! Pembayaran denda Anda telah kami terima.")
    else:
        messages.error(request, "Pembayaran dibatalkan atau terjadi kesalahan.")
    return redirect('loan_history')