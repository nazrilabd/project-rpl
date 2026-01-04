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
        try:
            data = json.loads(request.body)
            order_id_raw = data.get('order_id')
            status = data.get('transaction_status')
            
            print(f"Webhook Received: {order_id_raw} - Status: {status}") # DEBUG

            # Pecah ID
            parts = order_id_raw.split('-')
            if len(parts) < 2:
                return HttpResponse(status=400) # Bad Request jika format salah
                
            loan_id = parts[1]
            loan = Loan.objects.filter(id=loan_id).first() # Gunakan filter agar tidak crash
            
            if loan:
                if status in ['settlement', 'capture']:
                    loan.is_paid = True
                    loan.save()
                    print(f"Loan {loan_id} marked as PAID")
                return HttpResponse(status=200)
            else:
                print(f"Loan ID {loan_id} not found in database!")
                return HttpResponse(status=404) # Ini yang bikin 404 jika ID ga ada
        except Exception as e:
            print(f"Webhook Error: {str(e)}")
            return HttpResponse(status=500)
            
    return HttpResponse(status=405)
# Handler untuk memicu Django Messages
def payment_callback(request):
    status = request.GET.get('status')
    mess = request.GET.get('message')
    if status == 'success':
        messages.success(request, mess)
    else:
        messages.error(request, mess)
    return redirect('my_loans')