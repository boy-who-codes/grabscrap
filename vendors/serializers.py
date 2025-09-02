from rest_framework import serializers
from .models import Vendor, VendorKYC, VendorPayout


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['id', 'user', 'kyc_status', 'commission_rate']


class VendorKYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorKYC
        fields = '__all__'
        read_only_fields = ['id', 'vendor', 'verification_status', 'verified_by', 'verified_at']


class VendorPayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPayout
        fields = '__all__'
        read_only_fields = ['id', 'vendor', 'status', 'processed_at', 'processed_by']


class VendorRegistrationSerializer(serializers.ModelSerializer):
    kyc_documents = VendorKYCSerializer(write_only=True)
    
    class Meta:
        model = Vendor
        fields = ['store_name', 'business_email', 'business_phone', 'store_description', 
                 'store_address', 'kyc_documents']
    
    def create(self, validated_data):
        kyc_data = validated_data.pop('kyc_documents')
        vendor = Vendor.objects.create(**validated_data)
        VendorKYC.objects.create(vendor=vendor, **kyc_data)
        return vendor
