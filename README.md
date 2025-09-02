# KABAADWALA™ - Backend API

Hyperlocal scrap marketplace with wallet-based payments and real-time communication.

## Quick Setup

1. **Activate virtual environment:**
   ```bash
   source kabaadwala_env/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment setup:**
   ```bash
   cp .env.dev .env
   ```

4. **Database setup:**
   ```bash
   python manage.py migrate
   python manage.py setup_defaults
   python manage.py createsuperuser
   ```

5. **Run development servers:**
   ```bash
   # Terminal 1: Django server
   python manage.py runserver
   
   # Terminal 2: Celery worker
   python manage_celery.py worker
   
   # Terminal 3: Celery beat (scheduler)
   python manage_celery.py beat
   
   # Terminal 4: Redis server
   redis-server
   
   # Optional: Flower monitoring (Terminal 5)
   python manage_celery.py flower
   ```

## Core Features Implemented

- ✅ Django + DRF setup with JWT authentication
- ✅ Custom User model with email authentication
- ✅ Multi-address management system
- ✅ **Wallet System** - Recharge, hold, deduct with escrow
- ✅ **Vendor Management** - Registration, KYC, payouts
- ✅ **Product Catalog** - CRUD, categories, reviews, wishlist
- ✅ **Order Management** - Complete lifecycle with status tracking
- ✅ **Real-time Chat** - Order-specific communication
- ✅ Celery + Redis integration with background tasks
- ✅ WebSocket support (Channels) for real-time features
- ✅ Email notifications (async)
- ✅ Scheduled tasks (cleanup, reports)
- ✅ PostgreSQL configuration
- ✅ Admin interface for all models
- ✅ Comprehensive API endpoints

## App Structure

### 🏛️ Core App
- User authentication & profiles
- Address management
- Categories & system settings
- Base models & utilities

### 💰 Wallet App
- Wallet management with balance tracking
- Recharge functionality
- Hold/release mechanism for orders
- Transaction history

### 🏪 Vendors App
- Vendor registration & profiles
- KYC document management
- Payout requests
- Analytics dashboard

### 📦 Products App
- Product catalog management
- Image handling
- Wishlist functionality
- Reviews & ratings

### 📋 Orders App
- Complete order lifecycle
- Payment processing with wallet
- Status tracking & history
- Refund management

### 💬 Chat App
- Order-specific chat rooms
- Real-time messaging
- File attachments
- Read receipts

## API Endpoints

### Authentication & User Management
- `POST /api/v1/auth/register/` - User registration
- `POST /api/v1/auth/login/` - JWT login
- `GET/PUT /api/v1/profile/` - User profile
- `GET/POST /api/v1/addresses/` - Address management

### Wallet System
- `GET /api/v1/wallet/` - Wallet details
- `POST /api/v1/wallet/recharge/` - Recharge wallet
- `GET /api/v1/wallet/transactions/` - Transaction history

### Vendor Management
- `POST /api/v1/vendors/register/` - Vendor registration
- `GET/PUT /api/v1/vendors/profile/` - Vendor profile
- `GET/PUT /api/v1/vendors/kyc/` - KYC management
- `GET /api/v1/vendors/analytics/` - Vendor analytics

### Product Catalog
- `GET /api/v1/products/` - Product listing (with filters)
- `GET /api/v1/products/{id}/` - Product details
- `GET/POST /api/v1/products/vendor/` - Vendor products
- `POST /api/v1/products/{id}/wishlist/` - Toggle wishlist

### Order Management
- `GET /api/v1/orders/` - User orders
- `POST /api/v1/orders/create/` - Create order
- `GET /api/v1/orders/{id}/` - Order details
- `POST /api/v1/orders/{id}/status/` - Update status (vendor)

### Real-time Chat
- `GET /api/v1/chat/rooms/` - Chat rooms
- `POST /api/v1/chat/orders/{id}/chat/` - Create chat room
- `GET/POST /api/v1/chat/rooms/{id}/messages/` - Messages

### WebSocket Endpoints
- `ws/chat/{room_name}/` - Real-time chat
- `ws/notifications/` - User notifications

## Background Tasks

### Celery Tasks Available:
- `send_verification_email` - Email verification for new users
- `send_otp_email` - 2FA OTP delivery
- `send_notification` - Real-time notifications
- `process_wallet_recharge` - Payment processing
- `release_held_amount` - Order completion
- `cleanup_expired_sessions` - Daily cleanup (scheduled)
- `generate_daily_report` - Daily statistics (scheduled)

### Celery Management:
```bash
python manage_celery.py worker    # Start worker
python manage_celery.py beat      # Start scheduler
python manage_celery.py flower    # Start monitoring
python manage_celery.py purge     # Clear all tasks
```

## Key Features

### 💳 Wallet-First Payment System
- Users must recharge wallet before purchases
- Money held in escrow during order processing
- Automatic release after delivery confirmation
- Complete transaction history

### 🏪 Vendor Ecosystem
- KYC verification process
- Commission-based earnings
- Payout management
- Analytics dashboard

### 📦 Complete Order Flow
```
Order Placed → Payment Held → Vendor Confirms → 
Packed → Shipped → Delivered → Payment Released
```

### 💬 Real-time Communication
- Order-specific chat rooms
- WebSocket-based messaging
- File sharing capabilities
- Notification system

### 🔧 Admin Features
- Complete admin interface
- User & vendor management
- Order monitoring
- System settings

## Next Steps

- Payment gateway integration (Razorpay/Stripe)
- Mobile app development
- Advanced search with Elasticsearch
- Analytics dashboard
- Notification system enhancement
