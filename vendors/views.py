from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Vendor, VendorKYC, VendorPayout
from .serializers import VendorSerializer, VendorKYCSerializer, VendorPayoutSerializer, VendorRegistrationSerializer
from orders.models import Order
from products.models import Product


# Web Views
@login_required
def vendor_dashboard(request):
    """Vendor dashboard with analytics"""
    try:
        vendor = request.user.vendor_profile
    except Vendor.DoesNotExist:
        return redirect('vendors:register_form')
    
    # Analytics data
    total_products = vendor.products.count()
    active_products = vendor.products.filter(is_active=True).count()
    total_orders = Order.objects.filter(vendor=vendor).count()
    pending_orders = Order.objects.filter(vendor=vendor, order_status__in=['placed', 'confirmed', 'packed']).count()
    completed_orders = Order.objects.filter(vendor=vendor, order_status='completed').count()
    
    # Revenue calculations
    total_revenue = Order.objects.filter(vendor=vendor, order_status='completed').aggregate(
        total=Sum('total_amount'))['total'] or 0
    
    # Recent orders
    recent_orders = Order.objects.filter(vendor=vendor).order_by('-created_at')[:5]
    
    # Top products
    top_products = Product.objects.filter(vendor=vendor).annotate(
        order_count=Count('orderitem')).order_by('-order_count')[:5]
    
    context = {
        'vendor': vendor,
        'stats': {
            'total_products': total_products,
            'active_products': active_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
        },
        'recent_orders': recent_orders,
        'top_products': top_products,
    }
    
    return render(request, 'vendors/dashboard.html', context)


@login_required
def vendor_register_form(request):
    """Vendor registration form"""
    if hasattr(request.user, 'vendor_profile'):
        return redirect('vendors:dashboard')
    
    if request.method == 'POST':
        # Handle vendor registration
        store_name = request.POST.get('store_name')
        business_email = request.POST.get('business_email')
        business_phone = request.POST.get('business_phone')
        store_description = request.POST.get('store_description', '')
        
        # Address data
        address_data = {
            'street': request.POST.get('street'),
            'city': request.POST.get('city'),
            'state': request.POST.get('state'),
            'pincode': request.POST.get('pincode'),
        }
        
        try:
            vendor = Vendor.objects.create(
                user=request.user,
                store_name=store_name,
                business_email=business_email,
                business_phone=business_phone,
                store_description=store_description,
                store_address=address_data
            )
            
            messages.success(request, 'Vendor registration successful! Please complete KYC verification.')
            return redirect('vendors:kyc_form')
            
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'vendors/register.html')


@login_required
def vendor_kyc_form(request):
    """KYC document submission form"""
    vendor = get_object_or_404(Vendor, user=request.user)
    
    try:
        kyc = vendor.kyc_documents
    except VendorKYC.DoesNotExist:
        kyc = None
    
    if request.method == 'POST':
        # Handle KYC submission
        bank_account_number = request.POST.get('bank_account_number')
        bank_ifsc = request.POST.get('bank_ifsc')
        bank_account_holder = request.POST.get('bank_account_holder')
        
        if kyc:
            # Update existing KYC
            kyc.bank_account_number = bank_account_number
            kyc.bank_ifsc = bank_ifsc
            kyc.bank_account_holder = bank_account_holder
            if 'pan_document' in request.FILES:
                kyc.pan_document = request.FILES['pan_document']
            if 'gstin_document' in request.FILES:
                kyc.gstin_document = request.FILES['gstin_document']
            kyc.verification_status = 'pending'
            kyc.save()
        else:
            # Create new KYC
            kyc = VendorKYC.objects.create(
                vendor=vendor,
                pan_document=request.FILES.get('pan_document'),
                gstin_document=request.FILES.get('gstin_document'),
                bank_account_number=bank_account_number,
                bank_ifsc=bank_ifsc,
                bank_account_holder=bank_account_holder
            )
        
        messages.success(request, 'KYC documents submitted successfully! Awaiting admin approval.')
        return redirect('vendors:dashboard')
    
    return render(request, 'vendors/kyc_form.html', {'vendor': vendor, 'kyc': kyc})


@login_required
def vendor_orders(request):
    """Vendor orders management"""
    vendor = get_object_or_404(Vendor, user=request.user)
    orders = Order.objects.filter(vendor=vendor).order_by('-created_at')
    
    return render(request, 'vendors/orders.html', {'vendor': vendor, 'orders': orders})


@login_required
def vendor_products(request):
    """Vendor products management"""
    vendor = get_object_or_404(Vendor, user=request.user)
    products = Product.objects.filter(vendor=vendor).order_by('-created_at')
    
    return render(request, 'vendors/products.html', {'vendor': vendor, 'products': products})


@login_required
def vendor_payouts(request):
    """Vendor payout requests"""
    vendor = get_object_or_404(Vendor, user=request.user)
    payouts = VendorPayout.objects.filter(vendor=vendor).order_by('-requested_at')
    
    # Calculate available balance for payout
    completed_orders = Order.objects.filter(vendor=vendor, order_status='completed', payment_status='paid')
    total_earnings = completed_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    paid_payouts = VendorPayout.objects.filter(vendor=vendor, status='processed').aggregate(
        total=Sum('amount'))['total'] or 0
    available_balance = total_earnings - paid_payouts
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        if amount > 0 and amount <= available_balance:
            # Create payout request
            VendorPayout.objects.create(
                vendor=vendor,
                amount=amount,
                orders_included=[],  # Can be enhanced to include specific orders
                bank_details={
                    'account_number': vendor.kyc_documents.bank_account_number,
                    'ifsc': vendor.kyc_documents.bank_ifsc,
                    'holder_name': vendor.kyc_documents.bank_account_holder,
                }
            )
            messages.success(request, f'Payout request for ₹{amount} submitted successfully!')
            return redirect('vendors:payouts')
        else:
            messages.error(request, 'Invalid payout amount!')
    
    context = {
        'vendor': vendor,
        'payouts': payouts,
        'available_balance': available_balance,
        'total_earnings': total_earnings,
        'paid_payouts': paid_payouts,
    }
    
    return render(request, 'vendors/payouts.html', context)


# API Views
class VendorProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return Vendor.objects.get(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_registration(request):
    """Register as vendor with KYC"""
    if hasattr(request.user, 'vendor_profile'):
        return Response({'error': 'User already registered as vendor'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = VendorRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        vendor = serializer.save(user=request.user)
        return Response({
            'message': 'Vendor registration successful. KYC under review.',
            'vendor_id': vendor.id
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorKYCView(generics.RetrieveUpdateAPIView):
    serializer_class = VendorKYCSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        vendor = Vendor.objects.get(user=self.request.user)
        return vendor.kyc_documents


class VendorPayoutListView(generics.ListCreateAPIView):
    serializer_class = VendorPayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        vendor = Vendor.objects.get(user=self.request.user)
        return VendorPayout.objects.filter(vendor=vendor)
    
    def perform_create(self, serializer):
        vendor = Vendor.objects.get(user=self.request.user)
        serializer.save(vendor=vendor)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vendor_analytics(request):
    """Get vendor analytics data"""
    try:
        vendor = Vendor.objects.get(user=request.user)
        
        # Calculate analytics
        total_products = vendor.products.count()
        active_products = vendor.products.filter(is_active=True).count()
        total_orders = Order.objects.filter(vendor=vendor).count()
        pending_orders = Order.objects.filter(vendor=vendor, order_status__in=['placed', 'confirmed', 'packed']).count()
        completed_orders = Order.objects.filter(vendor=vendor, order_status='completed').count()
        total_revenue = Order.objects.filter(vendor=vendor, order_status='completed').aggregate(
            total=Sum('total_amount'))['total'] or 0
        
        analytics = {
            'total_products': total_products,
            'active_products': active_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_revenue': float(total_revenue),
            'kyc_status': vendor.kyc_status,
            'store_name': vendor.store_name,
        }
        
        return Response(analytics)
        
    except Vendor.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
