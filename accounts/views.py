from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import authenticate, login
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Sum, Count
from django.apps import apps

from core.models import User, Address
from wallet.models import Wallet, WalletTransaction
from orders.models import Order
from .forms import UnifiedSignupForm, CustomAuthenticationForm, ProfileUpdateForm, AddressForm


def login_view(request):
    """Enhanced login with 2FA (skip OTP for admin users)"""
    if request.method == 'POST':
        step = request.POST.get('step', '1')
        
        if step == '1':
            # Step 1: Username/Password verification
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            user = authenticate(request, username=username, password=password)
            if user:
                if not user.is_verified:
                    messages.error(request, 'Please verify your email before logging in.')
                    return redirect('accounts:login')
                
                # Skip OTP for admin users
                if user.is_staff or user.is_superuser:
                    login(request, user)
                    
                    # Create login history
                    try:
                        LoginHistory = apps.get_model('core', 'LoginHistory')
                        from core.utils import get_client_ip
                        
                        LoginHistory.objects.create(
                            user=user,
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', ''),
                            is_successful=True
                        )
                    except Exception as e:
                        print(f"Failed to create login history: {e}")
                    
                    messages.success(request, f'Welcome back, {user.full_name or user.username}!')
                    return redirect('core:home')
                
                # Generate and send OTP for regular users
                TwoFactorAuth = apps.get_model('core', 'TwoFactorAuth')
                from core.utils import generate_otp, send_otp_email, get_client_ip
                from datetime import timedelta
                
                otp_code = generate_otp()
                expires_at = now() + timedelta(minutes=10)
                
                print(f"\n📧 OTP CREATION DEBUG:")
                print(f"User: {user.email}")
                print(f"Generated OTP: {otp_code}")
                print(f"Expires at: {expires_at}")
                print(f"Current time: {now()}")
                
                TwoFactorAuth.objects.create(
                    user=user,
                    otp_code=otp_code,
                    purpose='login',
                    expires_at=expires_at
                )
                
                # Send OTP email
                from core.utils import send_otp_email
                send_otp_email(user, otp_code, 'login', request)
                
                # Store user ID in session for step 2 (convert UUID to string)
                request.session['pending_user_id'] = str(user.id)
                request.session['login_step'] = '2'
                
                messages.success(request, 'Verification code sent to your email!')
                return render(request, 'accounts/login.html', {
                    'step': '2',
                    'email_hint': f"{user.email[:3]}***@{user.email.split('@')[1]}"
                })
            else:
                messages.error(request, 'Invalid username or password')
        
        elif step == '2':
            # Step 2: OTP verification
            otp_code = request.POST.get('otp_code')
            user_id = request.session.get('pending_user_id')
            
            if not user_id:
                messages.error(request, 'Session expired. Please login again.')
                return redirect('accounts:login')
            
            try:
                TwoFactorAuth = apps.get_model('core', 'TwoFactorAuth')
                LoginHistory = apps.get_model('core', 'LoginHistory')
                from core.utils import get_client_ip, send_login_alert
                
                user = User.objects.get(id=user_id)
                otp_obj = TwoFactorAuth.objects.filter(
                    user=user,
                    otp_code=otp_code,
                    purpose='login',
                    is_used=False
                ).first()
                
                # Debug OTP validation
                print(f"\n🔍 OTP DEBUG:")
                print(f"User: {user.email}")
                print(f"Entered OTP: {otp_code}")
                print(f"OTP Object Found: {otp_obj is not None}")
                
                if otp_obj:
                    print(f"Stored OTP: {otp_obj.otp_code}")
                    print(f"Expires at: {otp_obj.expires_at}")
                    print(f"Current time: {now()}")
                    print(f"Is expired: {otp_obj.expires_at <= now()}")
                    print(f"Is used: {otp_obj.is_used}")
                else:
                    # Check if any OTP exists for this user
                    all_otps = TwoFactorAuth.objects.filter(user=user, purpose='login')
                    print(f"Total OTPs for user: {all_otps.count()}")
                    for otp in all_otps:
                        print(f"  OTP: {otp.otp_code}, Used: {otp.is_used}, Expires: {otp.expires_at}")
                
                if otp_obj and otp_obj.expires_at > now():
                    # Mark OTP as used
                    otp_obj.is_used = True
                    otp_obj.save()
                    
                    # Get login details
                    ip_address = get_client_ip(request)
                    
                    # Create login history
                    login_history = LoginHistory.objects.create(
                        user=user,
                        ip_address=ip_address,
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        is_successful=True
                    )
                    
                    # Send login alert email
                    send_login_alert(user, login_history, request)
                    
                    # Login user
                    login(request, user)
                    
                    # Clear session
                    request.session.pop('pending_user_id', None)
                    request.session.pop('login_step', None)
                    
                    messages.success(request, f'Welcome back, {user.full_name or user.username}!')
                    
                    # Redirect based on user type
                    if user.is_admin_user:
                        return redirect('accounts:admin_dashboard')
                    elif user.is_vendor:
                        return redirect('vendors:dashboard')
                    else:
                        return redirect('accounts:dashboard')
                else:
                    # Debug info for user
                    debug_msg = 'Invalid or expired verification code'
                    if settings.DEBUG:
                        if not otp_obj:
                            debug_msg += f' [DEBUG: No OTP found for code {otp_code}]'
                        elif otp_obj.expires_at <= now():
                            debug_msg += f' [DEBUG: OTP expired at {otp_obj.expires_at}, current time {now()}]'
                        elif otp_obj.is_used:
                            debug_msg += f' [DEBUG: OTP already used]'
                    
                    messages.error(request, debug_msg)
                    
            except User.DoesNotExist:
                messages.error(request, 'Invalid session. Please login again.')
                return redirect('accounts:login')
    
    # GET request or failed login
    step = request.session.get('login_step', '1')
    context = {'step': step}
    
    if step == '2':
        user_id = request.session.get('pending_user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                context['email_hint'] = f"{user.email[:3]}***@{user.email.split('@')[1]}"
            except:
                request.session.pop('login_step', None)
                context['step'] = '1'
    
    return render(request, 'accounts/login.html', context)


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    template_name = 'accounts/logout.html'
    next_page = reverse_lazy('core:home')
    http_method_names = ['get', 'post']
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        # Handle GET requests by logging out immediately
        return self.post(request, *args, **kwargs)


class SignupView(CreateView):
    """User registration view"""
    model = User
    form_class = UnifiedSignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # Send verification email
        from core.tasks import send_verification_email
        from core.utils import get_current_site_url
        
        # Get current host for email links
        current_host = get_current_site_url(self.request)
        
        try:
            send_verification_email.delay(str(user.id), current_host)
        except:
            send_verification_email(str(user.id), current_host)
        
        messages.success(
            self.request,
            f'Account created successfully! We have sent a verification email to {user.email}. '
            'Please verify your email before logging in.'
        )
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@login_required
def dashboard(request):
    """Customer dashboard"""
    if request.user.is_admin_user:
        return redirect('accounts:admin_dashboard')
    elif request.user.is_vendor:
        return redirect('vendors:dashboard')
    
    # Customer dashboard
    user = request.user
    
    # Get user statistics
    total_orders = Order.objects.filter(user=user).count()
    pending_orders = Order.objects.filter(user=user, order_status__in=['placed', 'confirmed', 'packed']).count()
    completed_orders = Order.objects.filter(user=user, order_status='completed').count()
    total_spent = Order.objects.filter(user=user, order_status='completed').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Recent transactions
    recent_transactions = WalletTransaction.objects.filter(
        wallet__user=user).order_by('-created_at')[:5]
    
    context = {
        'user_type': 'Customer',
        'stats': {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_spent': total_spent,
        },
        'recent_orders': recent_orders,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'accounts/customer_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard with KYC and moderation features"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('accounts:dashboard')
    
    from vendors.models import Vendor
    from chat.models import ChatMessage, ChatModeration
    
    # Admin statistics
    total_users = User.objects.count()
    total_vendors = Vendor.objects.count()
    pending_kyc = Vendor.objects.filter(kyc_status='pending').count()
    approved_vendors = Vendor.objects.filter(kyc_status='approved').count()
    rejected_kyc = Vendor.objects.filter(kyc_status='rejected').count()
    
    # Recent KYC submissions
    recent_kyc_submissions = Vendor.objects.filter(
        kyc_status='pending'
    ).select_related('user').order_by('-created_at')[:10]
    
    # Recently approved/rejected
    recent_kyc_actions = Vendor.objects.exclude(
        kyc_status='pending'
    ).select_related('user').order_by('-updated_at')[:10]
    total_customers = User.objects.filter(user_type='customer').count()
    total_vendors = User.objects.filter(user_type='vendor').count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(order_status__in=['placed', 'confirmed', 'packed']).count()
    completed_orders = Order.objects.filter(order_status='completed').count()
    total_revenue = Order.objects.filter(order_status='completed').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    # KYC statistics
    kyc_stats = {
        'pending': Vendor.objects.filter(kyc_status='pending').count(),
        'approved': Vendor.objects.filter(kyc_status='approved').count(),
        'rejected': Vendor.objects.filter(kyc_status='rejected').count(),
    }
    
    # Chat moderation statistics
    flagged_messages = ChatMessage.objects.filter(is_flagged=True).count()
    escrow_bypass_attempts = ChatModeration.objects.filter(
        violation_type__in=['contact_sharing', 'external_payment', 'escrow_bypass']
    ).count()
    
    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_orders = Order.objects.order_by('-created_at')[:5]
    pending_kyc_list = Vendor.objects.filter(kyc_status='pending').select_related('user')[:5]
    flagged_messages_list = ChatMessage.objects.filter(is_flagged=True).select_related(
        'sender', 'room'
    ).prefetch_related('moderations')[:5]
    
    context = {
        'user_type': 'Admin',
        'user_stats': {
            'total_users': total_users,
            'total_customers': total_customers,
            'total_vendors': total_vendors,
            'verified_users': verified_users,
        },
        'order_stats': {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
        },
        'kyc_stats': kyc_stats,
        'moderation_stats': {
            'flagged_messages': flagged_messages,
            'escrow_bypass_attempts': escrow_bypass_attempts,
        },
        'recent_users': recent_users,
        'recent_orders': recent_orders,
        'pending_kyc': kyc_stats['pending'],
        'flagged_messages': flagged_messages,
        'pending_kyc_list': pending_kyc_list,
        'flagged_messages_list': flagged_messages_list,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)
    
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@require_POST
def admin_update_kyc(request):
    """Update KYC status"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        vendor_id = request.POST.get('vendor_id')
        status = request.POST.get('status')
        
        if status not in ['approved', 'rejected']:
            messages.error(request, 'Invalid status')
            return redirect('accounts:dashboard')
        
        try:
            from vendors.models import Vendor
            vendor = Vendor.objects.get(id=vendor_id)
            vendor.kyc_status = status
            vendor.save()
            
            messages.success(request, f'KYC status updated to {status}')
            
        except Vendor.DoesNotExist:
            messages.error(request, 'Vendor not found')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('accounts:dashboard')


@login_required
@require_POST
def admin_moderate_message(request):
    """Moderate chat message"""
    if not request.user.is_admin_user:
        messages.error(request, 'Access denied')
        return redirect('accounts:dashboard')
    
    message_id = request.POST.get('message_id')
    action = request.POST.get('action')
    
    try:
        from chat.models import ChatMessage, ChatModeration
        message = ChatMessage.objects.get(id=message_id)
        
        if action == 'delete':
            message.content = '[Message deleted by admin]'
            message.is_flagged = False
            message.save()
            messages.success(request, 'Message deleted successfully')
        elif action == 'warning':
            ChatModeration.objects.filter(message=message).update(
                is_reviewed=True,
                admin_action='warning_sent'
            )
            message.is_flagged = False
            message.save()
            messages.success(request, 'Warning sent successfully')
        
    except ChatMessage.DoesNotExist:
        messages.error(request, 'Message not found')
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
    
    return redirect('accounts:dashboard')


@login_required
def profile(request):
    """User profile management"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def addresses(request):
    """User addresses management (buyers only)"""
    if request.user.user_type == 'vendor':
        messages.error(request, 'Address management is only available for customers!')
        return redirect('vendors:dashboard')
    
    user_addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'accounts/addresses.html', {'addresses': user_addresses})


@login_required
def add_address(request):
    """Add new address (buyers only)"""
    if request.user.user_type == 'vendor':
        messages.error(request, 'Address management is only available for customers!')
        return redirect('vendors:dashboard')
    
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('accounts:addresses')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/add_address.html', {'form': form})


@login_required
def edit_address(request, address_id):
    """Edit existing address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('accounts:addresses')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'accounts/edit_address.html', {'form': form, 'address': address})


@login_required
@require_http_methods(["POST"])
def delete_address(request, address_id):
    """Delete address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if address.is_default and Address.objects.filter(user=request.user).count() > 1:
        # Set another address as default
        next_address = Address.objects.filter(user=request.user).exclude(id=address_id).first()
        if next_address:
            next_address.is_default = True
            next_address.save()
    
    address.delete()
    messages.success(request, 'Address deleted successfully!')
    return redirect('accounts:addresses')


@login_required
@require_http_methods(["POST"])
def set_default_address(request, address_id):
    """Set address as default"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    # Remove default from all addresses
    Address.objects.filter(user=request.user).update(is_default=False)
    
    # Set this address as default
    address.is_default = True
    address.save()
    
    messages.success(request, 'Default address updated successfully!')
    return redirect('accounts:addresses')


def verify_email(request, uidb64, token):
    """Email verification view"""
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from django.contrib.auth.tokens import default_token_generator
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'Email verification link is invalid or has expired.')
        return redirect('accounts:login')





from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str


def verify_email(request, uidb64, token):
    """Verify user email address"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        if default_token_generator.check_token(user, token):
            user.is_verified = True
            user.save()
            messages.success(request, 'Email verified successfully! You can now login.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Invalid or expired verification link.')
            return redirect('accounts:register')
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid verification link.')
        return redirect('accounts:register')


def get_dev_email(request, user_id):
    """Get development email for modal display"""
    if not settings.DEBUG:
        messages.error(request, 'Not available in production')
        return redirect('accounts:dashboard')
    
    from django.core.cache import cache
    email_data = cache.get(f'dev_email_{user_id}')
    
    if email_data:
        messages.info(request, f'Email found: {email_data}')
    else:
        messages.warning(request, 'No email found')
    
    return redirect('accounts:dashboard')


@require_POST
def send_otp(request):
    """Send OTP to mobile number"""
    try:
        mobile_number = request.POST.get('mobile_number', '').strip()
        
        if not mobile_number:
            messages.error(request, 'Mobile number is required')
            return redirect('accounts:login')
        
        # Basic mobile number validation
        if not mobile_number.isdigit() or len(mobile_number) != 10:
            messages.error(request, 'Please enter a valid 10-digit mobile number')
            return redirect('accounts:login')
        
        # Generate OTP directly for immediate response
        import random
        from django.core.cache import cache
        
        otp = str(random.randint(100000, 999999))
        cache.set(f'mobile_otp_{mobile_number}', otp, timeout=300)
        
        # Console output for development
        print(f"\n" + "="*60)
        print(f"📱 OTP SENT TO: {mobile_number}")
        print(f"🔐 OTP CODE: {otp}")
        print(f"⏰ EXPIRES IN: 5 minutes")
        print("="*60 + "\n")
        
        # Send OTP asynchronously (for logging/future SMS integration)
        from core.tasks import send_mobile_otp
        send_mobile_otp.delay(mobile_number)
        
        # Show success message
        from django.conf import settings
        message = f'OTP sent to {mobile_number}. Please check your messages.'
        
        # In development, show OTP in message
        if settings.DEBUG:
            message += f' [DEV: OTP is {otp}]'
        
        messages.success(request, message)
        
        # Store mobile number in session for OTP verification
        request.session['otp_mobile'] = mobile_number
        return redirect('accounts:verify_otp')
        
    except Exception as e:
        print(f"❌ OTP Error: {str(e)}")
        messages.error(request, 'Failed to send OTP. Please try again.')
        return redirect('accounts:login')


def verify_otp_view(request):
    """Verify OTP for mobile login"""
    mobile_number = request.session.get('otp_mobile')
    
    if not mobile_number:
        messages.error(request, 'Session expired. Please request OTP again.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        
        if not entered_otp:
            messages.error(request, 'Please enter the OTP')
            return render(request, 'accounts/verify_otp.html', {'mobile_number': mobile_number})
        
        # Get OTP from cache
        from django.core.cache import cache
        stored_otp = cache.get(f'mobile_otp_{mobile_number}')
        
        if not stored_otp:
            messages.error(request, 'OTP expired. Please request a new one.')
            return redirect('accounts:login')
        
        if entered_otp == stored_otp:
            # OTP verified successfully
            cache.delete(f'mobile_otp_{mobile_number}')
            request.session.pop('otp_mobile', None)
            
            # Here you can implement user login logic
            messages.success(request, 'OTP verified successfully!')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
    
    return render(request, 'accounts/verify_otp.html', {'mobile_number': mobile_number})


@require_POST
def resend_otp(request):
    """Resend OTP to mobile number"""
    mobile_number = request.session.get('otp_mobile')
    
    if not mobile_number:
        messages.error(request, 'Session expired. Please request OTP again.')
        return redirect('accounts:login')
    
    try:
        # Generate new OTP
        import random
        from django.core.cache import cache
        
        otp = str(random.randint(100000, 999999))
        cache.set(f'mobile_otp_{mobile_number}', otp, timeout=300)
        
        # Console output for development
        print(f"\n" + "="*60)
        print(f"📱 OTP RESENT TO: {mobile_number}")
        print(f"🔐 NEW OTP CODE: {otp}")
        print(f"⏰ EXPIRES IN: 5 minutes")
        print("="*60 + "\n")
        
        # Send OTP asynchronously
        from core.tasks import send_mobile_otp
        send_mobile_otp.delay(mobile_number)
        
        # Show success message
        from django.conf import settings
        message = f'New OTP sent to {mobile_number}.'
        
        if settings.DEBUG:
            message += f' [DEV: OTP is {otp}]'
        
        messages.success(request, message)
        
    except Exception as e:
        print(f"❌ Resend OTP Error: {str(e)}")
        messages.error(request, 'Failed to resend OTP. Please try again.')
    
    return redirect('accounts:verify_otp')


@require_POST
def resend_2fa_otp(request):
    """Resend OTP for 2FA login"""
    user_id = request.session.get('pending_user_id')
    
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('accounts:login')
    
    try:
        user = User.objects.get(id=user_id)
        
        # Generate new OTP
        import random
        otp_code = str(random.randint(100000, 999999))
        
        # Create new 2FA record
        TwoFactorAuth = apps.get_model('core', 'TwoFactorAuth')
        from datetime import timedelta
        
        # Delete old OTPs
        TwoFactorAuth.objects.filter(user=user, purpose='login', is_used=False).delete()
        
        # Create new OTP
        TwoFactorAuth.objects.create(
            user=user,
            otp_code=otp_code,
            purpose='login',
            expires_at=now() + timedelta(minutes=10)
        )
        
        # Send OTP email
        from core.utils import send_otp_email
        send_otp_email(user, otp_code, 'login', request)
        
        messages.success(request, 'New verification code sent to your email!')
        
    except User.DoesNotExist:
        messages.error(request, 'Invalid session. Please login again.')
        return redirect('accounts:login')
    except Exception as e:
        print(f"❌ 2FA Resend Error: {str(e)}")
        messages.error(request, 'Failed to resend code. Please try again.')
    
    return redirect('accounts:login')


class RegisterView(CreateView):
    """Unified registration view for buyers and sellers"""
    model = User
    form_class = UnifiedSignupForm
    template_name = 'accounts/register.html'
    
    def get_success_url(self):
        if settings.DEBUG:
            return f"{reverse_lazy('accounts:login')}?show_email={self.object.id}"
        return reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        account_type = form.cleaned_data['user_type']
        
        if account_type == 'vendor':
            messages.success(
                self.request, 
                'Seller account created successfully! Please check your email for verification. You can start adding products after email verification.'
            )
        else:
            messages.success(
                self.request, 
                'Account created successfully! Please check your email for verification.'
            )
        
        # Send verification email with proper host
        from core.tasks import send_verification_email, send_email_with_fallback
        from core.utils import get_current_site_url
        
        # Get the current site URL
        site_url = get_current_site_url(self.request)
        
        # Send verification email with host info
        send_email_with_fallback(send_verification_email, str(self.object.id), site_url)
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)


@login_required
def dashboard(request):
    """User dashboard with comprehensive stats"""
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user=user)
    
    # Get user statistics
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    recent_transactions = WalletTransaction.objects.filter(
        wallet=wallet
    ).order_by('-created_at')[:5]
    
    stats = {
        'total_orders': Order.objects.filter(user=user).count(),
        'total_spent': wallet.total_spent,
        'pending_orders': Order.objects.filter(
            user=user, 
            order_status__in=['placed', 'confirmed', 'packed']
        ).count(),
        'completed_orders': Order.objects.filter(
            user=user, 
            order_status='completed'
        ).count(),
    }
    
    context = {
        'wallet': wallet,
        'recent_orders': recent_orders,
        'recent_transactions': recent_transactions,
        'stats': stats,
        'addresses_count': Address.objects.filter(user=user).count(),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile management"""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def addresses_view(request):
    """User addresses management"""
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def add_address(request):
    """Add new address"""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # Handle default address logic
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('accounts:addresses')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/add_address.html', {'form': form})


@login_required
def edit_address(request, address_id):
    """Edit existing address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            
            # Handle default address logic
            if updated_address.is_default:
                Address.objects.filter(user=request.user, is_default=True).exclude(
                    id=address.id
                ).update(is_default=False)
            
            updated_address.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('accounts:addresses')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'accounts/edit_address.html', {'form': form, 'address': address})


@login_required
@require_http_methods(["POST"])
def delete_address(request, address_id):
    """Delete address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if address.is_default and Address.objects.filter(user=request.user).count() > 1:
        # Set another address as default
        next_address = Address.objects.filter(user=request.user).exclude(id=address.id).first()
        if next_address:
            next_address.is_default = True
            next_address.save()
    
    address.delete()
    messages.success(request, 'Address deleted successfully!')
    return redirect('accounts:addresses')
