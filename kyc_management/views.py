from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction, models
from django.db.models import Q
from django.core.paginator import Paginator
import json
import os

from accounts.models import User, VendorProfile, VendorKYC
from .models import KYCApproval, KYCNotification
from .forms import VendorKYCForm, KYCReviewForm

def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_authenticated and (user.is_superuser or user.is_staff)

def is_vendor(user):
    """Check if user is a vendor"""
    return user.is_authenticated and hasattr(user, 'vendor_profile')

@login_required
@user_passes_test(is_admin)
def kyc_dashboard(request):
    """KYC Management Dashboard"""
    # Get counts for dashboard
    pending_count = KYCApproval.objects.filter(status='pending').count()
    approved_count = KYCApproval.objects.filter(status='approved').count()
    rejected_count = KYCApproval.objects.filter(status='rejected').count()
    
    # Get recent activity
    recent_activity = KYCApproval.objects.select_related('vendor_profile__user')\
        .order_by('-reviewed_at', '-submitted_at')[:10]
    
    # Get pending KYC applications
    pending_kyc = VendorProfile.objects.filter(
        kyc_status__in=['pending', 'submitted']
    ).select_related('user', 'kyc')[:5]
    
    context = {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'recent_activity': recent_activity,
        'pending_kyc': pending_kyc,
    }
    
    return render(request, 'kyc_management/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def pending_kyc_list(request):
    """List of pending KYC applications"""
    # Get pending KYC applications with related data
    pending_kyc = VendorProfile.objects.filter(
        kyc_status__in=['pending', 'submitted']
    ).select_related('user', 'kyc')
    
    # Handle search
    search_query = request.GET.get('q')
    if search_query:
        pending_kyc = pending_kyc.filter(
            Q(store_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(kyc__pan_number__icontains=search_query) |
            Q(kyc__gstin__icontains=search_query)
        )
    
    # Handle sorting
    sort_by = request.GET.get('sort', '-submitted_at')
    if sort_by in ['store_name', 'user__email', 'submitted_at']:
        pending_kyc = pending_kyc.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(pending_kyc, 20)  # Show 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query or '',
        'sort_by': sort_by,
    }
    
    return render(request, 'kyc_management/pending_list.html', context)

@login_required
@user_passes_test(is_admin)
def kyc_detail(request, vendor_id):
    """Detailed view of a vendor's KYC application"""
    vendor_profile = get_object_or_404(
        VendorProfile.objects.select_related('user', 'kyc'),
        id=vendor_id
    )
    
    # Get or create KYC approval record
    kyc_approval, created = KYCApproval.objects.get_or_create(
        vendor_profile=vendor_profile,
        defaults={'admin_user': request.user}
    )
    
    if request.method == 'POST':
        form = KYCReviewForm(request.POST, instance=kyc_approval)
        action = request.POST.get('action')
        
        if form.is_valid() and action in ['approve', 'reject']:
            with transaction.atomic():
                kyc_approval = form.save(commit=False)
                kyc_approval.status = 'approved' if action == 'approve' else 'rejected'
                kyc_approval.admin_user = request.user
                kyc_approval.reviewed_at = timezone.now()
                
                # If approving, clear rejection reason
                if action == 'approve':
                    kyc_approval.rejection_reason = ''
                
                kyc_approval.save()
                
                # Update vendor profile status
                vendor_profile.kyc_status = 'verified' if action == 'approve' else 'rejected'
                vendor_profile.save()
                
                # Send notifications
                send_kyc_notification(kyc_approval)
                
                messages.success(
                    request, 
                    f'KYC {action}d successfully for {vendor_profile.user.email}'
                )
                
                if action == 'approve':
                    return redirect('kyc_management:dashboard')
                return redirect('kyc_management:pending_list')
    else:
        form = KYCReviewForm(instance=kyc_approval)
    
    context = {
        'vendor_profile': vendor_profile,
        'kyc_approval': kyc_approval,
        'form': form,
    }
    
    return render(request, 'kyc_management/kyc_detail.html', context)

@login_required
@user_passes_test(is_admin)
def approve_kyc_ajax(request):
    """AJAX endpoint for KYC approval"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            vendor_id = data.get('vendor_id')
            action = data.get('action')  # 'approve' or 'reject'
            rejection_reason = data.get('rejection_reason', '')
            admin_notes = data.get('admin_notes', '')
            
            vendor_profile = get_object_or_404(VendorProfile, id=vendor_id)
            
            # Get or create KYC approval record
            kyc_approval, created = KYCApproval.objects.get_or_create(
                vendor_profile=vendor_profile,
                defaults={'admin_user': request.user}
            )
            
            kyc_approval.status = 'approved' if action == 'approve' else 'rejected'
            kyc_approval.rejection_reason = rejection_reason if action == 'reject' else ''
            kyc_approval.admin_notes = admin_notes
            kyc_approval.admin_user = request.user
            kyc_approval.save()
            
            # Send notifications
            send_kyc_notification(kyc_approval)
            
            return JsonResponse({
                'success': True,
                'message': f'KYC {action}d successfully',
                'status': kyc_approval.status
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def reapply_kyc(request):
    """Allow vendors to reapply for KYC after rejection"""
    if not hasattr(request.user, 'vendor_profile'):
        messages.error(request, 'Only vendors can reapply for KYC')
        return redirect('dashboard')
    
    vendor_profile = request.user.vendor_profile
    latest_approval = vendor_profile.kyc_approvals.order_by('-submitted_at').first()
    
    if not latest_approval or not latest_approval.can_reapply:
        messages.error(request, 'You cannot reapply for KYC at this time')
        return redirect('vendor_dashboard')
    
    if request.method == 'POST':
        # Create new KYC application
        new_approval = KYCApproval.objects.create(
            vendor_profile=vendor_profile,
            status='pending',
            admin_user=None
        )
        
        # Update vendor profile status
        vendor_profile.kyc_status = 'pending'
        vendor_profile.save()
        
        messages.success(request, 'KYC reapplication submitted successfully')
        return redirect('vendor_dashboard')
    
    context = {
        'latest_approval': latest_approval,
    }
    
    return render(request, 'kyc_management/reapply.html', context)

@login_required
@user_passes_test(is_vendor)
def kyc_submit(request):
    """Vendor KYC submission view"""
    vendor_profile = request.user.vendor_profile
    
    if vendor_profile.kyc_status == 'approved':
        messages.info(request, 'Your KYC is already approved.')
        return redirect('vendor_dashboard')
    
    pending_kyc = KYCApproval.objects.filter(
        vendor_profile=vendor_profile,
        status='pending'
    ).first()
    
    if pending_kyc and not pending_kyc.can_reapply:
        messages.warning(request, 'Your KYC application is under review.')
        return redirect('kyc_status')
    
    if request.method == 'POST':
        form = VendorKYCForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                kyc_approval, _ = KYCApproval.objects.update_or_create(
                    vendor_profile=vendor_profile,
                    status='pending',
                    defaults={'admin_user': None}
                )
                
                vendor_profile.kyc_status = 'pending'
                vendor_profile.save()
                
                kyc = vendor_profile.kyc
                for field in ['pan_document', 'gstin_document', 'bank_account_proof', 
                            'bank_account_number', 'bank_ifsc', 'bank_account_holder']:
                    setattr(kyc, field, form.cleaned_data[field])
                kyc.verification_status = 'pending'
                kyc.save()
                
                messages.success(request, 'KYC submitted successfully.')
                return redirect('kyc_status')
    else:
        form = VendorKYCForm()
    
    return render(request, 'kyc_management/kyc_submit.html', {'form': form})

@login_required
@user_passes_test(is_vendor)
def kyc_status(request):
    """Vendor KYC status view"""
    kyc_approval = KYCApproval.objects.filter(
        vendor_profile=request.user.vendor_profile
    ).order_by('-submitted_at').first()
    return render(request, 'kyc_management/kyc_status.html', {'kyc_approval': kyc_approval})

def send_kyc_notification(kyc_approval):
    """Send email and SMS notifications about KYC status"""
    vendor = kyc_approval.vendor_profile.user
    status = kyc_approval.status
    
    # Prepare context for email templates
    context = {
        'vendor': vendor,
        'status': status,
        'store_name': kyc_approval.vendor_profile.store_name,
        'rejection_reason': kyc_approval.rejection_reason if status == 'rejected' else None,
        'contact_email': settings.DEFAULT_FROM_EMAIL,
        'reviewed_at': kyc_approval.reviewed_at,
        'can_reapply': getattr(kyc_approval, 'can_reapply', False),
        'document_verified': kyc_approval.is_document_verified,
        'verification_notes': kyc_approval.document_verification_notes,
    }
    
    # Send email notification
    try:
        subject = f"Your KYC Application Has Been {status.capitalize()}"
        html_content = render_to_string('kyc_management/email/kyc_status_email.html', context)
        text_content = render_to_string('kyc_management/email/kyc_status_email.txt', context)
        
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[vendor.email],
            html_message=html_content,
            fail_silently=False,
        )
        
        # Record successful email notification
        KYCNotification.objects.create(
            vendor=vendor,
            kyc_approval=kyc_approval,
            notification_type='email',
            sent_successfully=True
        )
        
    except Exception as e:
        # Record failed email notification
        KYCNotification.objects.create(
            vendor=vendor,
            kyc_approval=kyc_approval,
            notification_type='email',
            sent_successfully=False,
            error_message=str(e)
        )
    
    # Send SMS notification (if phone number exists)
    if hasattr(vendor, 'mobile_number') and vendor.mobile_number:
        try:
            # TODO: Integrate with SMS gateway (MSG91, etc.)
            # For now, just print to console
            message = f"Your KYC application has been {status}. "
            if status == 'rejected' and kyc_approval.rejection_reason:
                message += f"Reason: {kyc_approval.rejection_reason}"
            
            print(f"SMS to {vendor.mobile_number}: {message}")
            
            # Record successful SMS notification
            KYCNotification.objects.create(
                vendor=vendor,
                kyc_approval=kyc_approval,
                notification_type='sms',
                sent_successfully=True
            )
            
        except Exception as e:
            # Record failed SMS notification
            KYCNotification.objects.create(
                vendor=vendor,
                kyc_approval=kyc_approval,
                notification_type='sms',
                sent_successfully=False,
                error_message=str(e)
            )
