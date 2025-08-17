from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib import messages
from django.conf import settings
from .models import User, OTP, PhoneOTP, VendorProfile, VendorKYC, Wallet, WalletTransaction
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail
from django import forms
import logging
from django.urls import reverse
import random
import string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# Dummy Celery task fallback
try:
    from .tasks import send_email_task
except ImportError:
    def send_email_task(subject, recipient_list, template_name, context=None, from_email=None, **kwargs):
        """
        Send an email using Django's email backend
        """
        if context is None:
            context = {}
        
        # Get the email content from template
        html_content = render_to_string(template_name, context)
        
        # Create the email
        msg = EmailMultiAlternatives(
            subject=subject,
            body=html_content,  # Fallback text content
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=recipient_list if isinstance(recipient_list, list) else [recipient_list],
        )
        msg.attach_alternative(html_content, "text/html")
        
        try:
            msg.send()
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

class SignupForm(forms.Form):
    user_type = forms.ChoiceField(choices=[('buyer', 'Buyer'), ('vendor', 'Vendor')], widget=forms.RadioSelect)
    store_name = forms.CharField(required=False)
    email = forms.EmailField()
    full_name = forms.CharField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            raise forms.ValidationError('Passwords do not match.')
        if cleaned.get('user_type') == 'vendor' and not cleaned.get('store_name'):
            raise forms.ValidationError('Store name is required for vendors.')
        # Check for duplicate email
        if User.objects.filter(email=cleaned.get('email')).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return cleaned

def generate_unique_username():
    chars = string.ascii_letters + string.digits
    while True:
        username = ''.join(random.choices(chars, k=10))
        if not User.objects.filter(username=username).exists():
            return username

def send_activation_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    activation_link = request.build_absolute_uri(f"/accounts/activate/{uid}/{token}/")
    context = {"user": user, "activation_link": activation_link}
    subject = "Activate your KABAADWALA™ account"
    html_content = render_to_string("email/activation_email.html", context)
    try:
        # Try Celery async
        send_email_task.delay(subject, user.email, "email/activation_email.html", context)
        messages.success(request, 'A confirmation email has been sent to your email address. Please check your inbox.')
    except Exception as exc:
        logging.warning(f"Celery failed, sending email synchronously: {exc}")
        try:
            msg = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            messages.success(request, 'A confirmation email has been sent to your email address. Please check your inbox.')
        except Exception as exc2:
            logging.error(f"Email send failed: {exc2}")
            messages.error(request, 'There was a problem sending the confirmation email. Please try again later.')

def signup(request):
    if request.user.is_authenticated:
        user = request.user
        if user.user_type == 'vendor':
            return redirect('accounts:vendor_dashboard')
        elif user.user_type == 'admin':
            return redirect('accounts:admin_dashboard')
        else:
            return redirect('accounts:user_dashboard')
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                email=data['email'],
                password=data['password1'],
                full_name=data['full_name'],
                user_type=data['user_type'],
            )
            user.is_active = True
            user.is_verified = False
            user.save()
            
            # Create VendorProfile if vendor
            if data['user_type'] == 'vendor':
                VendorProfile.objects.create(
                    user=user,
                    store_name=data['store_name'],
                    business_email=data['email'],
                    business_phone='',
                    store_address={},
                    kyc_status='pending'
                )
                print(f"Created VendorProfile for vendor {user.id}")
            
            send_activation_email(request, user)
            messages.success(request, 'Signup successful! Please check your email to activate your account.')
            return redirect('accounts:confirmation_mail_sent')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

def confirmation_mail_sent(request):
    return render(request, 'accounts/confirmation_mail_sent.html')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, 'Your email has been verified. You can now log in.')
        return redirect('accounts:login')
    else:
        return HttpResponse('Activation link is invalid!', status=400)

def generate_otp_code():
    return str(random.randint(100000, 999999))

def login_view(request):
    if request.user.is_authenticated:
        # If user is already logged in, redirect to the next parameter or home
        next_url = request.GET.get('next') or request.session.get('next')
        if next_url:
            if 'next' in request.session:
                del request.session['next']
            return redirect(next_url)
        return redirect('home:index')  # Default redirect to home
        
    # Store the next URL from GET or POST parameters in session
    next_url = request.GET.get('next') or request.POST.get('next')
    if next_url:
        request.session['next'] = next_url
        
    class LoginForm(forms.Form):
        email = forms.EmailField()
        password = forms.CharField(widget=forms.PasswordInput)
        
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if not user.is_verified:
                    send_activation_email(request, user)
                    messages.error(request, 'Your email is not verified. A new activation email has been sent.')
                    return redirect('accounts:login')
                # Generate OTP and send via email
                otp_code = generate_otp_code()
                expires_at = timezone.now() + timezone.timedelta(minutes=10)
                OTP.objects.create(user=user, code=otp_code, expires_at=expires_at)
                
                # In development, show OTP in alert and console
                if settings.DEBUG:
                    print(f'\n\n=== DEVELOPMENT MODE: OTP for {user.email} is {otp_code} ===\n\n')
                    messages.info(request, f'DEVELOPMENT MODE: Your OTP is {otp_code}. This would be sent via email in production.')
                
                # Send OTP via email (Celery)
                subject = 'Your KABAADWALA™ Login OTP'
                context = {'user': user, 'otp_code': otp_code}
                
                # Log the OTP for debugging
                print(f'\n\n=== OTP for {user.email} is {otp_code} ===\n\n')
                
                try:
                    # Try Celery async
                    send_email_task.delay(subject, user.email, 'email/otp_email.html', context)
                    print(f'Email sent via Celery to {user.email}')
                except Exception as e:
                    print(f'Celery task failed: {e}')
                    try:
                        # Fallback to sync email sending
                        html_content = render_to_string('email/otp_email.html', context)
                        msg = EmailMultiAlternatives(
                            subject=subject,
                            body='',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            to=[user.email],
                            reply_to=[settings.DEFAULT_FROM_EMAIL]
                        )
                        msg.attach_alternative(html_content, 'text/html')
                        msg.send(fail_silently=False)
                        print(f'Email sent synchronously to {user.email}')
                    except Exception as email_error:
                        print(f'Failed to send email: {email_error}')
                        messages.error(request, 'Failed to send OTP email. Please try again.')
                        return redirect('accounts:login')
                
                # Store user ID in session for OTP verification
                request.session['otp_user_id'] = str(user.id)
                request.session['otp_email_sent'] = True
                return redirect('accounts:otp_verify')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

# The rest of the views remain as placeholders or simple renders for now

def phone_verify(request):
    """
    View for phone verification landing page
    """
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    return render(request, 'accounts/phone_verify.html', {'user': request.user})

def verify_phone_otp(request):
    """
    View for verifying phone OTP
    """
    if not request.user.is_authenticated:
        return redirect('accounts:login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        phone = request.POST.get('phone')
        
        # Verify OTP
        otp = PhoneOTP.objects.filter(
            user=request.user,
            phone_number=phone,
            code=otp_code,
            is_used=False,
            expires_at__gte=timezone.now()
        ).first()
        
        if otp:
            otp.is_used = True
            otp.save()
            
            # Update user's phone verification status
            request.user.phone_verified = True
            request.user.phone_number = phone
            request.user.save()
            
            messages.success(request, 'Phone number verified successfully!')
            return redirect('accounts:profile_setup')
        else:
            messages.error(request, 'Invalid or expired OTP code')
    
    return render(request, 'accounts/verify_phone_otp.html', {'user': request.user})

@require_http_methods(["GET", "POST"])
def test_email(request):
    """
    Test email functionality by sending a test email
    Only available in DEBUG mode
    """
    if not settings.DEBUG:
        return HttpResponse("Test email endpoint is only available in DEBUG mode", status=403)
    
    if request.method == 'POST':
        email = request.POST.get('email', request.user.email if request.user.is_authenticated else None)
        if not email:
            messages.error(request, 'Please provide an email address')
            return redirect('accounts:test_email')
        
        context = {
            'user': request.user if request.user.is_authenticated else None,
            'test_message': 'This is a test email from KABAADWALA™'
        }
        
        try:
            # Try to send the email
            success = send_email_task(
                subject='Test Email from KABAADWALA™',
                recipient_list=[email],
                template_name='email/test_email.html',
                context=context
            )
            
            if success:
                messages.success(request, f'Test email sent to {email}')
            else:
                messages.error(request, 'Failed to send test email. Check server logs for details.')
                
        except Exception as e:
            messages.error(request, f'Error sending test email: {str(e)}')
            
        return redirect('accounts:test_email')
    
    return render(request, 'accounts/test_email.html')

def otp_verify(request):
    class OTPForm(forms.Form):
        otp_code = forms.CharField(max_length=6)
    user_id = request.session.get('otp_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('accounts:login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please log in again.')
        return redirect('login')
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp_code']
            otp = OTP.objects.filter(user=user, code=otp_code, is_used=False, expires_at__gte=timezone.now()).first()
            if otp:
                otp.is_used = True
                otp.save()
                # Log the user in
                login(request, user)
                
                # Store the next URL from the session or GET parameters
                next_url = request.session.get('next') or request.GET.get('next')
                
                # If there's a next URL, use it and clean up the session
                if next_url:
                    if 'next' in request.session:
                        del request.session['next']
                    return redirect(next_url)
                
                # Otherwise, redirect based on user type and profile completion
                if not is_profile_complete(user):
                    return redirect('accounts:profile_setup')
                elif user.is_superuser:
                    return redirect('accounts:admin_dashboard')
                elif user.user_type == 'vendor':
                    return redirect('accounts:vendor_dashboard')
                else:
                    return redirect('home:index')  # Default to home
            else:
                messages.error(request, 'Invalid or expired OTP.')
    else:
        form = OTPForm()
    return render(request, 'accounts/otp_verify.html', {'form': form, 'account_type': user.user_type})

def logout_view(request):
    logout(request)
    return redirect('login')

def resend_activation(request):
    return render(request, 'accounts/resend_activation.html')

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField()

class SetPasswordForm(forms.Form):
    new_password1 = forms.CharField(widget=forms.PasswordInput)
    new_password2 = forms.CharField(widget=forms.PasswordInput)
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password1') != cleaned.get('new_password2'):
            raise forms.ValidationError('Passwords do not match.')
        return cleaned

def send_password_reset_email(request, user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_link = request.build_absolute_uri(reverse('accounts:password_reset_confirm', args=[uid, token]))
    context = {"user": user, "reset_link": reset_link}
    subject = "Reset your KABAADWALA™ password"
    html_content = render_to_string("email/password_reset_email.html", context)
    try:
        send_email_task.delay(subject, user.email, "email/password_reset_email.html", context)
    except Exception as exc:
        logging.warning(f"Celery failed, sending email synchronously: {exc}")
        msg = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                send_password_reset_email(request, user)
                messages.success(request, 'A password reset link has been sent to your email.')
            except User.DoesNotExist:
                messages.error(request, 'No user found with that email address.')
            return redirect('accounts:password_reset')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                messages.success(request, 'Your password has been reset. You can now log in.')
                return redirect('accounts:login')
        else:
            form = SetPasswordForm()
        
        return render(request, 'accounts/password_reset_confirm.html', {
            'form': form,
            'email': user.email
        })
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('accounts:password_reset')

def send_sms_otp(phone_number, code):
    # In production, integrate with SMS gateway (e.g., MSG91)
    # For dev, print to console
    print(f"[DEV] Sending OTP {code} to phone {phone_number}")
    # TODO: Add async SMS sending (Celery) and fallback

@login_required
def wallet_dashboard(request):
    """
    View for wallet dashboard showing balance and recent transactions
    """
    wallet = request.user.accounts_wallet
    transactions = wallet.transactions.all().order_by('-created_at')[:10]
    return render(request, 'accounts/wallet_dashboard.html', {
        'wallet': wallet,
        'transactions': transactions
    })

@login_required
@require_http_methods(["POST"])
def wallet_recharge(request):
    """
    View for handling wallet recharge requests
    """
    amount = Decimal(request.POST.get('amount', 0))
    if amount <= 0:
        messages.error(request, 'Invalid recharge amount')
        return redirect('accounts:wallet_dashboard')
    
    wallet = request.user.accounts_wallet
    try:
        # Create transaction record
        transaction = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='recharge',
            amount=amount,
            status='pending',
            balance_before=wallet.current_balance
        )
        
        # Process payment (integration with payment gateway would go here)
        # For now, we'll just update the balance
        wallet.current_balance += amount
        wallet.total_recharged += amount
        wallet.save()
        
        # Update transaction status
        transaction.balance_after = wallet.current_balance
        transaction.status = 'completed'
        transaction.processed_at = timezone.now()
        transaction.save()
        
        messages.success(request, f'Successfully recharged ₹{amount} to your wallet')
    except Exception as e:
        messages.error(request, f'Recharge failed: {str(e)}')
        
    return redirect('accounts:wallet_dashboard')

@csrf_exempt
def send_phone_otp(request):
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            user_id = request.POST.get('user_id')
            
            # Validate input
            if not phone or not user_id:
                return JsonResponse({'success': False, 'error': 'Missing phone number or user ID'})
            
            # Validate phone number format (basic validation)
            if not phone.isdigit() or len(phone) < 10:
                return JsonResponse({'success': False, 'error': 'Invalid phone number format'})
            
            # Check if user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found'})
            
            # Check if OTP was recently sent (prevent spam)
            recent_otp = PhoneOTP.objects.filter(
                user_id=user_id,
                phone_number=phone,
                created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
            ).first()
            
            if recent_otp:
                return JsonResponse({'success': False, 'error': 'Please wait 1 minute before requesting another OTP'})
            
            # Generate and save OTP
            otp_code = str(random.randint(100000, 999999))
            expires_at = timezone.now() + timezone.timedelta(minutes=10)
            
            PhoneOTP.objects.create(
                user_id=user_id, 
                phone_number=phone, 
                code=otp_code, 
                expires_at=expires_at
            )
            
            # Send OTP (for dev, prints to console)
            if settings.DEBUG:
                print(f'[DEV] OTP sent to {phone}: {otp_code}')
            else:
                # TODO: Integrate MSG91 API here
                send_sms_otp(phone, otp_code)
            
            print(f"OTP sent to {phone} for user {user_id}: {otp_code}")
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
            
        except Exception as e:
            print(f"Error in send_phone_otp: {e}")
            return JsonResponse({'success': False, 'error': 'Server error. Please try again.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def verify_phone_otp(request):
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            user_id = request.POST.get('user_id')
            otp_code = request.POST.get('otp')
            
            # Validate input
            if not phone or not user_id or not otp_code:
                return JsonResponse({'success': False, 'error': 'Missing required fields'})
            
            # Validate OTP format
            if not otp_code.isdigit() or len(otp_code) != 6:
                return JsonResponse({'success': False, 'error': 'OTP must be 6 digits'})
            
            # Check if user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'User not found'})
            
            # Find OTP
            otp = PhoneOTP.objects.filter(
                user_id=user_id, 
                phone_number=phone, 
                code=otp_code, 
                is_used=False
            ).first()
            
            if not otp:
                return JsonResponse({'success': False, 'error': 'Invalid OTP code'})
            
            # Check if OTP is expired
            if otp.expires_at <= timezone.now():
                return JsonResponse({'success': False, 'error': 'OTP has expired. Please request a new one.'})
            
            # Verify OTP
            otp.is_used = True
            otp.save()
            user.is_phone_verified = True
            user.save()
            
            print(f"Phone verified successfully for user {user.id}")
            return JsonResponse({'success': True, 'message': 'Phone number verified successfully!'})
            
        except Exception as e:
            print(f"Error in verify_phone_otp: {e}")
            return JsonResponse({'success': False, 'error': 'Server error. Please try again.'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def is_profile_complete(user):
    """Check if user profile is complete based on user type"""
    # Admins don't need profile setup - they go directly to admin dashboard
    if user.is_superuser:
        print(f"Admin user {user.id} - profile setup not required")
        return True
    
    if user.user_type == 'vendor':
        try:
            vp = user.vendor_profile
            kyc = vp.kyc
        except (VendorProfile.DoesNotExist, VendorKYC.DoesNotExist):
            print(f"Profile incomplete: Missing vendor profile or KYC for user {user.id}")
            return False
        
        # Check all required fields for vendors
        required_fields = {
            'full_name': user.full_name,
            'store_name': vp.store_name,
            'business_email': vp.business_email,
            'store_address': vp.store_address,
            'city': vp.store_address.get('city') if vp.store_address else None,
            'state': vp.store_address.get('state') if vp.store_address else None,
            'pincode': vp.store_address.get('pincode') if vp.store_address else None,
            'pan': vp.pan,
            'gstin': vp.gstin,
            'pan_document': kyc.pan_document,
            'kyc_status': vp.kyc_status
        }
        
        # Debug: Print missing fields
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            print(f"Profile incomplete for vendor {user.id}. Missing: {missing_fields}")
            return False
        
        # Check if all required fields are present
        is_complete = (
            user.full_name and
            vp.store_name and
            vp.business_email and
            vp.store_address and 
            vp.store_address.get('city') and 
            vp.store_address.get('state') and
            vp.store_address.get('pincode') and
            vp.pan and 
            vp.gstin and
            kyc.pan_document and
            vp.kyc_status == 'approved'
        )
        
        if is_complete:
            print(f"Profile complete for vendor {user.id}")
        else:
            print(f"Profile incomplete for vendor {user.id}")
        
        return is_complete
    else:
        # For buyers, only need full name and email verification
        is_complete = user.full_name and user.is_verified
        if not is_complete:
            print(f"Profile incomplete for buyer {user.id}. full_name: {bool(user.full_name)}, is_verified: {user.is_verified}")
        return is_complete

@login_required
def profile_setup(request):
    user = request.user
    
    # Ensure vendor_profile and kyc exist for vendor users
    if user.user_type == 'vendor':
        try:
            vp = user.vendor_profile
        except VendorProfile.DoesNotExist:
            vp = VendorProfile.objects.create(
                user=user, 
                store_name=f"Store_{user.id}", 
                business_email=user.email, 
                business_phone=user.mobile_number or '', 
                store_address={}, 
                kyc_status='pending'
            )
        try:
            kyc = vp.kyc
        except VendorKYC.DoesNotExist:
            kyc = VendorKYC.objects.create(vendor=vp)
    
    # Check if profile is already complete
    if is_profile_complete(user):
        if user.user_type == 'vendor':
            return redirect(reverse('vendor_dashboard'))
        elif user.user_type == 'admin':
            return redirect(reverse('admin_dashboard'))
        else:
            return redirect(reverse('user_dashboard'))
    
    if request.method == 'POST':
        try:
            # Basic info
            user.full_name = request.POST.get('full_name')
            user.save()
            
            # Store address and KYC (vendor only)
            if user.user_type == 'vendor':
                # Update store address
                address = {
                    'line1': request.POST.get('line1', ''),
                    'line2': request.POST.get('line2', ''),
                    'city': request.POST.get('city', ''),
                    'state': request.POST.get('state', ''),
                    'pincode': request.POST.get('pincode', ''),
                    'latitude': request.POST.get('latitude', ''),
                    'longitude': request.POST.get('longitude', ''),
                }
                vp.store_address = address
                vp.pan = request.POST.get('pan', '')
                vp.gstin = request.POST.get('gstin', '')
                vp.save()
                
                # Handle file uploads to VendorKYC
                if request.FILES.get('pan_image'):
                    kyc.pan_document = request.FILES['pan_image']
                    print(f"PAN document uploaded: {kyc.pan_document.name}")
                
                if request.FILES.get('gstin_doc'):
                    kyc.gstin_document = request.FILES['gstin_doc']
                    print(f"GSTIN document uploaded: {kyc.gstin_document.name}")
                
                kyc.save()
                
                # Auto-approve KYC if all required fields are present
                if (vp.pan and vp.gstin and kyc.pan_document and 
                    vp.store_address.get('city') and vp.store_address.get('state') and
                    vp.store_address.get('pincode')):
                    vp.kyc_status = 'approved'
                    vp.kyc_approved_at = timezone.now()
                    vp.save()
                    print(f"Auto-approved KYC for vendor {user.id}")
            
            # Handle phone verification (if provided)
            phone_otp = request.POST.get('phone_otp')
            if phone_otp:
                try:
                    # Verify the OTP
                    phone_otp_obj = PhoneOTP.objects.filter(
                        user=user,
                        code=phone_otp,
                        is_used=False,
                        expires_at__gt=timezone.now()
                    ).first()
                    
                    if phone_otp_obj:
                        user.is_phone_verified = True
                        phone_otp_obj.is_used = True
                        phone_otp_obj.save()
                        user.save()
                        print(f"Phone verified for user {user.id}")
                    else:
                        messages.warning(request, 'Invalid or expired phone OTP.')
                except Exception as e:
                    print(f"Error verifying phone OTP: {e}")
                    messages.warning(request, 'Error verifying phone OTP.')
            
            messages.success(request, 'Profile setup completed successfully!')
            
            # Redirect to dashboard based on user_type
            if user.user_type == 'vendor':
                return redirect(reverse('vendor_dashboard'))
            elif user.user_type == 'admin':
                return redirect(reverse('admin_dashboard'))
            else:
                return redirect(reverse('user_dashboard'))
                
        except Exception as e:
            print(f"Error in profile_setup: {e}")
            messages.error(request, f'Error saving profile: {str(e)}')
    
    # Set correct account type for profile setup
    if user.is_superuser:
        account_type = 'admin'
    else:
        account_type = user.user_type
    
    context = {'user': user, 'account_type': account_type}
    return render(request, 'accounts/profile_setup.html', context)

@login_required
def user_dashboard(request):
    user = request.user
    if user.user_type != 'buyer':
        return redirect('/')
    
    # Get or create wallet for user
    try:
        wallet, created = Wallet.objects.get_or_create(user=user)
        recent_transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:5]
        total_spent = wallet.total_spent
    except Exception as e:
        print(f"Wallet error for user {user.id}: {e}")
        wallet = None
        recent_transactions = []
        total_spent = 0
    
    # Get user stats
    context = {
        'user': user, 
        'account_type': user.user_type,
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'total_orders': 0,  # TODO: Connect with orders app
        'total_spent': total_spent,
    }
    
    if not is_profile_complete(user):
        return redirect(reverse('profile_setup'))
    
    return render(request, 'dashboard/user_dashboard.html', context)

@login_required
def admin_dashboard(request):
    user = request.user
    if not user.is_superuser:
        return redirect('/')
    
    # Get admin stats
    total_users = User.objects.filter(user_type='buyer').count()
    total_vendors = User.objects.filter(user_type='vendor').count()
    pending_kyc = VendorProfile.objects.filter(kyc_status='pending').count()
    approved_kyc = VendorProfile.objects.filter(kyc_status='approved').count()
    rejected_kyc = VendorProfile.objects.filter(kyc_status='rejected').count()
    pending_kyc = VendorProfile.objects.filter(kyc_status='pending').count()
    total_transactions = WalletTransaction.objects.count()
    
    context = {
        'user': user, 
        'account_type': 'admin',  # Force admin account type for superusers
        'total_users': total_users,
        'total_vendors': total_vendors,
        'pending_kyc': pending_kyc,
        'approved_kyc': approved_kyc,
        'rejected_kyc': rejected_kyc,
        'pending_kyc': pending_kyc,
        'total_transactions': total_transactions,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def vendor_dashboard(request):
    user = request.user
    if user.user_type != 'vendor':
        return redirect('/')
    
    # Ensure vendor profile exists
    try:
        vendor_profile = user.vendor_profile
    except VendorProfile.DoesNotExist:
        messages.error(request, 'Vendor profile not found. Please contact support.')
        return redirect('/')
    
    # Get or create wallet for vendor
    try:
        wallet, created = Wallet.objects.get_or_create(user=user)
        recent_transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')[:5]
    except Exception as e:
        print(f"Wallet error for vendor {user.id}: {e}")
        wallet = None
        recent_transactions = []
    
    # Get vendor stats
    context = {
        'user': user, 
        'account_type': user.user_type,
        'vendor_profile': vendor_profile,
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'total_orders': 0,  # TODO: Connect with orders app
        'total_revenue': 0,  # TODO: Connect with orders app
        'total_customers': 0,  # TODO: Connect with orders app
    }
    
    if not is_profile_complete(user):
        messages.warning(request, 'Please complete your profile and KYC to access selling features.')
        return redirect(reverse('profile_setup'))
    
    return render(request, 'dashboard/vendor_dashboard.html', context)

 