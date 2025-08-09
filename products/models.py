import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User, VendorProfile


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='subcategories')
    icon = models.ImageField(upload_to='category_icons/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Commission rate in percentage (overrides global)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    @property
    def has_subcategories(self):
        return self.subcategories.exists()

    @property
    def total_products(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('piece', 'Piece'),
        ('ton', 'Ton'),
        ('quintal', 'Quintal'),
        ('gram', 'Gram'),
        ('bundle', 'Bundle'),
        ('dozen', 'Dozen'),
        ('box', 'Box'),
        ('bag', 'Bag'),
        ('liter', 'Liter'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    stock_quantity = models.PositiveIntegerField(default=0)
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sku = models.CharField(max_length=50, unique=True, editable=False)
    tags = models.JSONField(default=list, blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    orders_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.title} - {self.vendor.store_name}"

    def save(self, *args, **kwargs):
        if not self.sku:
            # Generate SKU: PRD-{first 3 letters of title}-{random 6 digits}
            import random
            import string
            title_prefix = self.title[:3].upper().replace(' ', '')
            random_suffix = ''.join(random.choice(string.digits) for _ in range(6))
            self.sku = f"PRD-{title_prefix}-{random_suffix}"
        super().save(*args, **kwargs)

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def can_order(self):
        return self.is_active and self.is_in_stock and self.vendor.kyc_status == 'approved'

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def increment_orders(self):
        self.orders_count += 1
        self.save(update_fields=['orders_count'])


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.product.title}"

    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"Review by {self.user.full_name} for {self.product.title}"

    @property
    def average_rating(self):
        return self.product.reviews.filter(is_approved=True).aggregate(
            avg_rating=models.Avg('rating')
        )['avg_rating'] or 0


class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_users')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-added_at']
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.user.full_name} - {self.product.title}"
