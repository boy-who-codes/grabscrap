from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.conf import settings
from .models import Wallet, WalletTransaction
from .tasks import process_wallet_recharge
import razorpay
import json
import hmac
import hashlib


# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(
    getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_key'),
    getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_secret')
))


@login_required
def wallet_detail(request):
    """Wallet detail view - only for customers"""
    # Redirect vendors to their dashboard
    if hasattr(request.user, 'vendor_profile'):
        messages.info(request, "Wallet is not available for vendors.")
        return redirect('vendors:dashboard')
    
    # Check if this is a recharge request with parameters
    amount = request.GET.get('amount')
    payment_method = request.GET.get('payment_method')
    
    if amount and payment_method:
        # Redirect to recharge with the amount pre-filled
        return redirect(f'/wallet/recharge/?amount={amount}&payment_method={payment_method}')
    
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'transactions': page_obj,
    }
    return render(request, 'wallet/detail.html', context)


@login_required
def recharge_wallet(request):
    """Wallet recharge with Razorpay integration"""
    # Redirect vendors
    if hasattr(request.user, 'vendor_profile'):
        messages.error(request, "Wallet recharge is not available for vendors.")
        return redirect('vendors:dashboard')
    
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Handle GET parameters for direct recharge
    if request.method == 'GET':
        amount = request.GET.get('amount')
        payment_method = request.GET.get('payment_method')
        
        if amount and payment_method:
            # Just redirect to recharge page with amount pre-filled
            return redirect(f'/wallet/recharge/?prefill_amount={amount}')
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            
            print(f"\n💰 RECHARGE DEBUG:")
            print(f"User: {request.user.email}")
            print(f"Amount: {amount}")
            print(f"Razorpay Key ID: {getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_key')}")
            
            if amount < 100:
                messages.error(request, 'Minimum recharge amount is ₹100')
                return render(request, 'wallet/recharge.html', {'wallet': wallet})
            
            # Create Razorpay order
            print(f"Creating Razorpay order...")
            try:
                razorpay_order = razorpay_client.order.create({
                    'amount': int(amount * 100),  # Amount in paise
                    'currency': 'INR',
                    'payment_capture': 1,
                    'notes': {
                        'user_id': str(request.user.id),
                        'user_email': request.user.email,
                        'transaction_type': 'wallet_recharge'
                    }
                })
                print(f"Razorpay order created: {razorpay_order['id']}")
            except Exception as razorpay_error:
                print(f"❌ Razorpay API Error: {str(razorpay_error)}")
                if "authentication" in str(razorpay_error).lower():
                    messages.error(request, 'Payment gateway configuration error. Please contact support.')
                else:
                    messages.error(request, f'Payment gateway error: {str(razorpay_error)}')
                return render(request, 'wallet/recharge.html', {'wallet': wallet})
            
            # Create pending transaction
            transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='recharge',
                amount=amount,
                payment_gateway_ref=razorpay_order['id'],
                status='pending',
                description=f'Wallet recharge of ₹{amount}',
                balance_before=wallet.current_balance,
                balance_after=wallet.current_balance
            )
            
            context = {
                'wallet': wallet,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_key'),
                'amount': amount,
                'amount_paise': int(amount * 100),  # Amount in paise for Razorpay
                'transaction_id': transaction.id,
                'user_name': request.user.full_name or request.user.username,
                'user_email': request.user.email,
                'user_phone': request.user.mobile_number or '',
            }
            
            return render(request, 'wallet/payment_direct.html', context)
            
        except Exception as e:
            print(f"❌ RECHARGE ERROR: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            messages.error(request, f'Error creating payment: {str(e)}')
    
    context = {
        'wallet': wallet,
        'prefill_amount': request.GET.get('prefill_amount', ''),
        'recent_recharges': WalletTransaction.objects.filter(
            wallet=wallet,
            transaction_type='recharge',
            status='completed'
        ).order_by('-created_at')[:5]
    }
    
    return render(request, 'wallet/recharge.html', context)


@login_required
def transaction_history(request):
    """Detailed transaction history"""
    # Redirect vendors
    if hasattr(request.user, 'vendor_profile'):
        messages.info(request, "Transaction history is not available for vendors.")
        return redirect('vendors:dashboard')
    
    wallet = get_object_or_404(Wallet, user=request.user)
    
    # Filter transactions
    transaction_type = request.GET.get('type', 'all')
    transactions = WalletTransaction.objects.filter(wallet=wallet)
    
    if transaction_type != 'all':
        transactions = transactions.filter(transaction_type=transaction_type)
    
    transactions = transactions.order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'wallet': wallet,
        'transactions': page_obj,
        'transaction_type': transaction_type,
    }
    
    return render(request, 'wallet/transactions.html', context)


@csrf_exempt
@require_POST
def payment_callback(request):
    """Handle Razorpay payment callback"""
    try:
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        transaction_id = request.POST.get('transaction_id')
        
        # Verify payment signature
        generated_signature = hmac.new(
            getattr(settings, 'RAZORPAY_KEY_SECRET', 'rzp_test_secret').encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature == razorpay_signature:
            # Payment successful - capture the payment
            try:
                # Capture payment to ensure it appears in dashboard
                payment_capture = razorpay_client.payment.capture(razorpay_payment_id, int(transaction.amount * 100))
                print(f"✅ Payment captured: {payment_capture}")
            except Exception as capture_error:
                print(f"⚠️ Payment capture warning: {str(capture_error)}")
                # Continue even if capture fails as payment is already verified
            
            # Payment successful
            transaction = get_object_or_404(WalletTransaction, id=transaction_id)
            
            # Update transaction
            transaction.status = 'completed'
            transaction.payment_gateway_ref = razorpay_payment_id
            transaction.save()
            
            # Update wallet balance
            wallet = transaction.wallet
            wallet.current_balance += transaction.amount
            wallet.total_recharged += transaction.amount
            transaction.balance_after = wallet.current_balance
            wallet.save()
            transaction.save()
            
            # Send recharge success email
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            
            try:
                # Generate PDF invoice
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib.colors import HexColor, black, white
                from reportlab.lib.units import inch
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from io import BytesIO
                import os
                
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
                
                # Define colors
                primary_color = HexColor('#198754')
                secondary_color = HexColor('#f8f9fa')
                
                # Get styles
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    spaceAfter=30,
                    textColor=primary_color,
                    alignment=1  # Center
                )
                
                # Build invoice content
                story = []
                
                # Header
                story.append(Paragraph("KABAADWALA™", title_style))
                story.append(Paragraph("Hyperlocal Scrap Marketplace", styles['Normal']))
                story.append(Spacer(1, 20))
                
                # Invoice title
                invoice_title = ParagraphStyle(
                    'InvoiceTitle',
                    parent=styles['Heading2'],
                    fontSize=18,
                    textColor=primary_color,
                    alignment=1
                )
                story.append(Paragraph("WALLET RECHARGE INVOICE", invoice_title))
                story.append(Spacer(1, 20))
                
                # Invoice details table
                invoice_data = [
                    ['Invoice ID:', f'INV-{transaction.id}'],
                    ['Date:', transaction.created_at.strftime('%B %d, %Y at %I:%M %p')],
                    ['Customer:', transaction.wallet.user.full_name or transaction.wallet.user.username],
                    ['Email:', transaction.wallet.user.email],
                    ['Payment ID:', razorpay_payment_id],
                ]
                
                invoice_table = Table(invoice_data, colWidths=[2*inch, 4*inch])
                invoice_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ]))
                story.append(invoice_table)
                story.append(Spacer(1, 30))
                
                # Transaction details
                story.append(Paragraph("TRANSACTION DETAILS", styles['Heading3']))
                story.append(Spacer(1, 10))
                
                transaction_data = [
                    ['Description', 'Amount'],
                    ['Wallet Recharge', f'₹{transaction.amount:,.2f}'],
                    ['Gateway Charges', '₹0.00'],
                    ['Total Amount', f'₹{transaction.amount:,.2f}'],
                ]
                
                transaction_table = Table(transaction_data, colWidths=[4*inch, 2*inch])
                transaction_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, black),
                    ('BACKGROUND', (0, -1), (-1, -1), secondary_color),
                ]))
                story.append(transaction_table)
                story.append(Spacer(1, 30))
                
                # Wallet balance
                story.append(Paragraph("WALLET SUMMARY", styles['Heading3']))
                story.append(Spacer(1, 10))
                
                balance_data = [
                    ['Previous Balance:', f'₹{transaction.balance_before:,.2f}'],
                    ['Amount Added:', f'₹{transaction.amount:,.2f}'],
                    ['New Balance:', f'₹{wallet.current_balance:,.2f}'],
                ]
                
                balance_table = Table(balance_data, colWidths=[3*inch, 3*inch])
                balance_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('BACKGROUND', (0, -1), (-1, -1), primary_color),
                    ('TEXTCOLOR', (0, -1), (-1, -1), white),
                ]))
                story.append(balance_table)
                story.append(Spacer(1, 40))
                
                # Footer
                footer_style = ParagraphStyle(
                    'Footer',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=HexColor('#666666'),
                    alignment=1
                )
                story.append(Paragraph("Thank you for using KABAADWALA™", footer_style))
                story.append(Paragraph("For support, contact us at support@kabaadwala.com", footer_style))
                
                # Build PDF
                doc.build(story)
                pdf_content = buffer.getvalue()
                buffer.close()
                
                subject = f"KABAADWALA™ - Wallet Recharge Invoice"
                html_message = render_to_string('emails/recharge_success.html', {
                    'user': transaction.wallet.user,
                    'amount': transaction.amount,
                    'new_balance': wallet.current_balance,
                    'transaction_id': transaction.id,
                })
                
                from django.core.mail import EmailMessage
                email = EmailMessage(
                    subject=subject,
                    body=f'Your wallet has been recharged with ₹{transaction.amount}. New balance: ₹{wallet.current_balance}',
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'KABAADWALA <noreply@kabaadwala.com>'),
                    to=[transaction.wallet.user.email],
                )
                email.attach(f'invoice_{transaction.id}.pdf', pdf_content, 'application/pdf')
                email.send(fail_silently=True)
                
                print(f"✅ Recharge email with PDF invoice sent to {transaction.wallet.user.email}")
            except Exception as e:
                print(f"❌ Email/PDF generation failed: {str(e)}")
                # Fallback to simple email
                try:
                    subject = f"KABAADWALA™ - Wallet Recharged Successfully"
                    html_message = render_to_string('emails/recharge_success.html', {
                        'user': transaction.wallet.user,
                        'amount': transaction.amount,
                        'new_balance': wallet.current_balance,
                        'transaction_id': transaction.id,
                    })
                    
                    send_mail(
                        subject=subject,
                        message=f'Your wallet has been recharged with ₹{transaction.amount}. New balance: ₹{wallet.current_balance}',
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'KABAADWALA <noreply@kabaadwala.com>'),
                        recipient_list=[transaction.wallet.user.email],
                        html_message=html_message,
                        fail_silently=True
                    )
                    print(f"✅ Simple recharge email sent to {transaction.wallet.user.email}")
                except Exception as e2:
                    print(f"❌ Fallback email also failed: {str(e2)}")
            
            messages.success(request, f'Wallet recharged successfully with ₹{transaction.amount}!')
            return redirect('wallet:detail')
        else:
            # Payment verification failed
            transaction = get_object_or_404(WalletTransaction, id=transaction_id)
            transaction.status = 'failed'
            transaction.save()
            
            messages.error(request, 'Payment verification failed. Please try again.')
            return redirect('wallet:recharge')
            
    except Exception as e:
        messages.error(request, f'Payment processing error: {str(e)}')
        return redirect('wallet:recharge')


@csrf_exempt
@require_POST
def payment_error_log(request):
    """Log payment errors from frontend"""
    try:
        import json
        from django.http import JsonResponse
        
        data = json.loads(request.body)
        error = data.get('error', {})
        transaction_id = data.get('transaction_id')
        
        print(f"\n❌ RAZORPAY PAYMENT ERROR:")
        print(f"Transaction ID: {transaction_id}")
        print(f"Error Code: {error.get('code')}")
        print(f"Error Description: {error.get('description')}")
        print(f"Error Source: {error.get('source')}")
        print(f"Error Step: {error.get('step')}")
        print(f"Error Reason: {error.get('reason')}")
        
        # Update transaction status if exists
        if transaction_id:
            try:
                transaction = WalletTransaction.objects.get(id=transaction_id)
                transaction.status = 'failed'
                transaction.description += f" - Failed: {error.get('description', 'Unknown error')}"
                transaction.save()
                print(f"✅ Transaction {transaction_id} marked as failed")
            except WalletTransaction.DoesNotExist:
                print(f"❌ Transaction {transaction_id} not found")
        
        return JsonResponse({'status': 'logged'})
        
    except Exception as e:
        print(f"❌ Error logging payment failure: {str(e)}")
        return JsonResponse({'status': 'error'})
