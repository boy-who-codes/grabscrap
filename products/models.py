from django.db import models
from django.contrib.auth import get_user_model
from core.models import BaseModel, Category
from vendors.models import Vendor

User = get_user_model()


class Product(BaseModel):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('piece', 'Piece'),
        ('ton', 'Ton'),
        ('liter', 'Liter'),
        ('meter', 'Meter'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=255)
    description = models.TextField()
    images = models.JSONField(default=list)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='kg')
    stock_quantity = models.IntegerField(default=0)
    minimum_order_quantity = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    tags = models.JSONField(default=list)
    specifications = models.JSONField(default=dict)
    views_count = models.IntegerField(default=0)
    orders_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"PRD-{self.vendor.id}-{self.id or 'NEW'}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_images')
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.product.title} - Image"


class Cart(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    
    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())
    
    def __str__(self):
        return f"{self.user.username}'s Cart"


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['cart', 'product']
    
    @property
    def total_price(self):
        return self.product.price * self.quantity
    
    def __str__(self):
        return f"{self.cart.user.username} - {self.product.title} x{self.quantity}"


class Wishlist(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    
    class Meta:
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.title}"


class ProductReview(BaseModel):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField(blank=True)
    is_verified_purchase = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.title} - {self.rating}★"
