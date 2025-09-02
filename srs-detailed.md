# KABAADWALA™ - System Requirements Specification (SRS)

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [User Roles and Permissions](#user-roles-and-permissions)
4. [Authentication System](#authentication-system)
5. [User Management](#user-management)
6. [Product and Order Management](#product-and-order-management)
7. [Payment and Escrow System](#payment-and-escrow-system)
8. [Communication System](#communication-system)
9. [Administrative Features](#administrative-features)
10. [Analytics and Reporting](#analytics-and-reporting)
11. [API Specifications](#api-specifications)
12. [Security Requirements](#security-requirements)
13. [Technical Stack](#technical-stack)
14. [Database Schema](#database-schema)
15. [Deployment Requirements](#deployment-requirements)

---

## 1. Project Overview

### 1.1 Purpose
KABAADWALA™ is a hyperlocal, multi-vendor scrap marketplace platform that connects scrap buyers with vendors within a configurable geographical radius. The platform operates on an escrow-based payment system with comprehensive vendor verification and order management capabilities.

### 1.2 Key Features
- **Hyperlocal Discovery**: Configurable radius-based vendor and product filtering (default: 250km)
- **Secure Transactions**: Escrow payment system with manual/automatic release
- **Vendor Verification**: Complete KYC workflow with admin approval
- **Real-time Communication**: WebSocket-based chat system per order
- **Multi-address Support**: Amazon/Flipkart-style address management
- **Comprehensive Analytics**: Vendor and admin dashboards with detailed insights
- **Mobile-First API**: RESTful API ready for mobile app integration
- **Background Processing**: Async task handling with Celery and Redis

### 1.3 Target Scale
Designed for enterprise-level scalability comparable to Flipkart/Amazon with ASGI deployment architecture.

---

## 2. System Architecture

### 2.1 High-Level Architecture
```
Frontend (Web/Mobile) → API Gateway → Django Backend → Database
                                  ↓
                            Celery Workers → Redis
                                  ↓
                            WebSocket (Channels)
```

### 2.2 Core Components
- **Backend**: Django with Django REST Framework
- **Real-time Features**: Django Channels with ASGI
- **Background Tasks**: Celery with Redis broker
- **Database**: PostgreSQL with spatial extensions
- **File Storage**: AWS S3 or DigitalOcean Spaces
- **Search**: Elasticsearch (optional for advanced search)
- **Monitoring**: Sentry for error tracking, Prometheus for metrics

---

## 3. User Roles and Permissions

### 3.1 User (Buyer)
**Registration Requirements:**
- Email address (must be unique and verified)
- Username (real-time availability check)
- Strong password (minimum 8 characters, alphanumeric + special chars)

**Core Capabilities:**
- Browse products within configured radius from active address
- Manage multiple delivery addresses with default selection
- Add products to wishlist for future reference
- Place orders with escrow payment protection
- Track order status through complete lifecycle
- Download PDF invoices for completed orders
- Communicate with vendors via order-specific chat
- Report inappropriate vendors or products
- Access complete order history with reorder functionality
- Manage account settings and preferences

**Profile Requirements:**
- Full name, mobile number, profile photo (optional)
- At least one complete delivery address
- Email verification mandatory before platform access

### 3.2 Vendor (Seller)
**Registration Requirements:**
- Business email (verified)
- Username (unique across platform)
- KYC documentation (PAN, GSTIN, Bank details)
- Admin approval required before selling

**Core Capabilities:**
- Complete store profile management (logo, banner, address, contact)
- Product catalog management (CRUD operations)
- Inventory tracking and stock management
- Order processing and status updates
- Commission structure visibility (global/category/product level)
- Analytics dashboard access
- Customer communication via order chat
- Refund request initiation
- Data export functionality (orders/products to CSV)
- Payout request management

**KYC Requirements:**
- Store name (unique constraint)
- Store logo and banner images
- Business address with map coordinates
- PAN card document (.jpg/.pdf format)
- GSTIN certificate
- Complete bank account details (account number, IFSC, holder name)

### 3.3 Admin (Superuser)
**User Management:**
- Vendor KYC approval/rejection workflow
- User and vendor account suspension/banning
- Account status management and monitoring

**System Configuration:**
- Global search radius configuration
- Escrow payment mode settings (manual/automatic)
- Commission rate management (global/category/product level)
- Platform-wide settings and preferences

**Content Management:**
- Product price override capabilities
- Advertisement management (upload, schedule, track)
- Content moderation and report handling
- Push/email/SMS notification management

**Financial Management:**
- Payout request approval (manual mode)
- Refund processing and approval
- Commission tracking and adjustment
- Financial analytics and reporting

**Analytics and Monitoring:**
- Comprehensive sales and performance analytics
- Regional activity heatmaps
- User behavior analysis
- System audit logs and admin action tracking

---

## 4. Authentication System

### 4.1 Registration Flow
```
User Registration → Email Verification → Profile Setup → Platform Access
```

**Step 1: Initial Registration**
- Username availability check (real-time, Instagram-style)
- Email uniqueness validation
- Password strength validation
- Account created with `is_active=False`, `is_verified=False`

**Step 2: Email Verification**
- Activation email sent via Celery background task
- Email contains secure token with expiration
- User must verify before login access

**Step 3: Profile Completion**
- Mandatory profile setup wizard on first login
- Phase 1: Personal information (name, phone, photo)
- Phase 2: Address management (minimum one required)
- Phase 3: User preferences and settings

### 4.2 Login Process
**Pre-login Validations:**
- Email verification status check
- Account ban status verification
- Account activation status

**Two-Factor Authentication (2FA):**
- Primary authentication: username/email + password
- Secondary authentication: Email OTP (6-digit numeric)
- OTP expiration: 10 minutes
- Maximum OTP attempts: 3 per session

**Login States:**
- Unverified email: Block with resend activation option
- Banned account: Block with support contact information
- Incomplete profile: Redirect to profile completion wizard

### 4.3 Password Management
- Password reset via email token
- Password strength requirements enforced
- Password history tracking (prevent reuse of last 5 passwords)
- Account lockout after 5 failed attempts (30-minute lockout)

---

## 5. User Management

### 5.1 User Profile Structure
**Personal Information:**
```json
{
  "user_id": "uuid",
  "username": "string (unique)",
  "email": "string (unique, verified)",
  "full_name": "string",
  "mobile_number": "string (with country code)",
  "profile_photo": "url (optional)",
  "date_joined": "datetime",
  "last_login": "datetime",
  "is_active": "boolean",
  "is_verified": "boolean",
  "is_banned": "boolean"
}
```

**Address Management:**
```json
{
  "address_id": "uuid",
  "user_id": "uuid (foreign key)",
  "address_type": "enum (home, office, other)",
  "recipient_name": "string",
  "recipient_phone": "string",
  "flat_number": "string",
  "street_address": "string",
  "landmark": "string (optional)",
  "city": "string",
  "pincode": "string (6 digits)",
  "state": "string",
  "country": "string (default: India)",
  "latitude": "decimal (optional)",
  "longitude": "decimal (optional)",
  "is_default": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 5.2 Vendor Profile Structure
**Business Information:**
```json
{
  "vendor_id": "uuid",
  "user_id": "uuid (foreign key)",
  "store_name": "string (unique)",
  "store_logo": "url",
  "store_banner": "url (optional)",
  "business_email": "string (verified)",
  "business_phone": "string",
  "store_description": "text (optional)",
  "store_address": "json (complete address object)",
  "business_hours": "json (optional)",
  "kyc_status": "enum (pending, approved, rejected)",
  "kyc_rejection_reason": "text (optional)",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**KYC Documentation:**
```json
{
  "kyc_id": "uuid",
  "vendor_id": "uuid (foreign key)",
  "pan_document": "url",
  "gstin_document": "url",
  "bank_account_number": "string (encrypted)",
  "bank_ifsc": "string",
  "bank_account_holder": "string",
  "verification_status": "enum (pending, verified, rejected)",
  "verified_by": "uuid (admin user_id)",
  "verified_at": "datetime",
  "rejection_reason": "text (optional)",
  "submitted_at": "datetime"
}
```

---

## 6. Product and Order Management

### 6.1 Product Catalog Structure
```json
{
  "product_id": "uuid",
  "vendor_id": "uuid (foreign key)",
  "category_id": "uuid (foreign key)",
  "title": "string (max 200 chars)",
  "description": "text",
  "images": "array of urls (max 10)",
  "price": "decimal (2 decimal places)",
  "unit": "enum (kg, piece, ton, etc.)",
  "stock_quantity": "integer",
  "minimum_order_quantity": "integer (default: 1)",
  "is_active": "boolean",
  "is_featured": "boolean",
  "sku": "string (unique, auto-generated)",
  "tags": "array of strings (optional)",
  "specifications": "json (key-value pairs)",
  "created_at": "datetime",
  "updated_at": "datetime",
  "views_count": "integer (default: 0)",
  "orders_count": "integer (default: 0)"
}
```

### 6.2 Category Management
```json
{
  "category_id": "uuid",
  "name": "string (unique)",
  "description": "text (optional)",
  "parent_category_id": "uuid (optional, for subcategories)",
  "icon": "url (optional)",
  "is_active": "boolean",
  "sort_order": "integer",
  "commission_rate": "decimal (optional, overrides global)",
  "created_at": "datetime"
}
```

### 6.3 Order Management System

**Order Lifecycle:**
```
Placed → Confirmed → Packed → Shipped → Out for Delivery → Delivered → Completed
```

**Order Structure:**
```json
{
  "order_id": "uuid",
  "order_number": "string (unique, auto-generated)",
  "user_id": "uuid (foreign key)",
  "vendor_id": "uuid (foreign key)",
  "delivery_address": "json (complete address)",
  "order_items": "array of order_item objects",
  "subtotal": "decimal",
  "tax_amount": "decimal",
  "delivery_charges": "decimal",
  "total_amount": "decimal",
  "payment_status": "enum (pending, paid, refunded, failed)",
  "order_status": "enum (placed, confirmed, packed, shipped, out_for_delivery, delivered, completed, cancelled)",
  "payment_method": "enum (escrow, cod, online)",
  "escrow_status": "enum (held, released, disputed)",
  "notes": "text (optional)",
  "estimated_delivery": "datetime",
  "actual_delivery": "datetime (optional)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Order Item Structure:**
```json
{
  "order_item_id": "uuid",
  "order_id": "uuid (foreign key)",
  "product_id": "uuid (foreign key)",
  "quantity": "integer",
  "unit_price": "decimal",
  "total_price": "decimal",
  "product_snapshot": "json (product details at time of order)"
}
```

### 6.4 Order Status Management
**Status Update Rules:**
- Only vendors can update order status (except cancellation)
- Each status change triggers notification to user
- Automatic escrow release after delivery confirmation
- Status history maintained for audit trail

**Notification Triggers:**
- Order placed: Immediate notification to vendor
- Status updates: Real-time notification to user
- Delivery confirmation: Auto-escrow release (if enabled)
- Cancellation: Immediate refund processing

---

## 7. Wallet and Payment System

### 7.1 Wallet System
**Wallet-First Payment Flow:**
```
User Wallet Recharge → Wallet Balance Check → Order Payment → Delivery Confirmation → Money Deduction
```

**Key Wallet Rules:**
- Users must recharge wallet before making any purchase
- Sufficient balance check before order placement
- Money deducted only after delivery confirmation by both parties
- No withdrawal option - wallet is for purchases only
- Wallet balance carries forward indefinitely

**Wallet Structure:**
```json
{
  "wallet_id": "uuid",
  "user_id": "uuid (foreign key)",
  "current_balance": "decimal (10,2)",
  "total_recharged": "decimal (10,2)",
  "total_spent": "decimal (10,2)",
  "is_active": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Wallet Transaction Structure:**
```json
{
  "transaction_id": "uuid",
  "wallet_id": "uuid (foreign key)",
  "transaction_type": "enum (recharge, hold, deduct, release)",
  "amount": "decimal (10,2)",
  "order_id": "uuid (optional, for order-related transactions)",
  "payment_gateway_ref": "string (for recharge transactions)",
  "status": "enum (pending, completed, failed, cancelled)",
  "description": "text",
  "created_at": "datetime",
  "processed_at": "datetime (optional)"
}
```

### 7.2 Payment Process Flow

**Step 1: Wallet Recharge**
- User adds money to wallet via payment gateway (Razorpay/Stripe)
- Minimum recharge: ₹100, Maximum: ₹50,000
- Recharge methods: UPI, Cards, Net Banking
- Instant credit after successful payment

**Step 2: Order Placement**
- Check wallet balance >= order total
- If insufficient: Show recharge prompt with required amount
- If sufficient: Create order and hold amount in wallet
- Wallet balance reduced but money held in escrow

**Step 3: Order Processing**
- Money remains in held state during order processing
- User cannot use held money for other orders
- If order cancelled: Held money released back to available balance

**Step 4: Delivery Confirmation**
- Both user and vendor must confirm delivery
- After dual confirmation: Held money deducted from wallet
- Money transferred to vendor account minus commission

**Wallet Transaction Types:**
- **RECHARGE**: Money added to wallet
- **HOLD**: Money held for pending order
- **DEDUCT**: Money deducted after successful delivery
- **RELEASE**: Held money released back (order cancelled)
- **REFUND**: Money credited back (in case of refunds)

### 7.3 Escrow Integration with Wallet
**Enhanced Payment Structure:**
```json
{
  "payment_id": "uuid",
  "order_id": "uuid (foreign key)",
  "wallet_id": "uuid (foreign key)",
  "amount": "decimal",
  "payment_method": "wallet",
  "wallet_transaction_id": "uuid (foreign key)",
  "escrow_status": "enum (held, released, disputed, refunded)",
  "held_at": "datetime",
  "released_at": "datetime (optional)",
  "released_by": "uuid (admin user_id, optional)",
  "created_at": "datetime"
}
```

### 7.2 Commission Management
**Commission Structure:**
- Global commission rate (default)
- Category-specific rates (override global)
- Product-specific rates (override category)
- Vendor-specific rates (override all, admin set)

**Commission Calculation:**
```json
{
  "commission_id": "uuid",
  "order_id": "uuid (foreign key)",
  "vendor_id": "uuid (foreign key)",
  "gross_amount": "decimal",
  "commission_rate": "decimal (percentage)",
  "commission_amount": "decimal",
  "net_amount": "decimal (gross - commission)",
  "calculated_at": "datetime"
}
```

### 7.3 Payout Management
```json
{
  "payout_id": "uuid",
  "vendor_id": "uuid (foreign key)",
  "amount": "decimal",
  "orders_included": "array of order_ids",
  "bank_details": "json (account info)",
  "status": "enum (requested, approved, processed, failed)",
  "requested_at": "datetime",
  "processed_at": "datetime (optional)",
  "processed_by": "uuid (admin user_id)",
  "transaction_reference": "string (optional)"
}
```

---

## 8. Communication System

### 8.1 Real-Time Chat
**Architecture**: WebSocket implementation using Django Channels

**Chat Features:**
- Order-specific chat rooms (user ↔ vendor)
- Real-time message delivery
- Typing indicators
- File/image attachments (max 10MB per file)
- Message history persistence
- Admin monitoring capabilities

**Chat Room Structure:**
```json
{
  "room_id": "uuid",
  "order_id": "uuid (foreign key)",
  "participants": "array of user_ids",
  "created_at": "datetime",
  "last_activity": "datetime",
  "is_active": "boolean"
}
```

**Message Structure:**
```json
{
  "message_id": "uuid",
  "room_id": "uuid (foreign key)",
  "sender_id": "uuid (foreign key)",
  "message_type": "enum (text, image, file, system)",
  "content": "text",
  "attachments": "array of urls (optional)",
  "is_read": "boolean",
  "sent_at": "datetime",
  "edited_at": "datetime (optional)"
}
```

### 8.2 Notification System
**Notification Channels:**
- Email notifications (transactional)
- SMS notifications (order updates)
- Push notifications (mobile app)
- In-app notifications (web interface)

**Email Templates:**
- Account activation: `activation_email.html`
- Email verification resend: `resend_activation.html`
- 2FA OTP: `otp_email.html`
- Password reset: `password_reset.html`
- KYC status updates: `kyc_status.html`
- Order confirmation: `order_placed.html`
- Order status updates: `order_update.html`
- Refund notifications: `refund_email.html`
- Chat message alerts: `chat_alert.html`
- Account suspension: `ban_notice.html`
- Payout notifications: `payout_update.html`

---

## 9. Administrative Features

### 9.1 User Management
**Capabilities:**
- View all users with advanced filtering
- User account suspension/activation
- Ban/unban user accounts with reason logging
- View user activity logs
- Manual email verification override
- Password reset for users (emergency)

### 9.2 Vendor Management
**KYC Workflow:**
- Review submitted KYC documents
- Approve/reject with detailed reasons
- Request additional documentation
- Set vendor-specific commission rates
- Monitor vendor performance metrics

**Vendor Controls:**
- Suspend vendor accounts
- Override product prices
- Set vendor-specific radius limits
- Monitor vendor chat communications

### 9.3 Order Management
**Administrative Controls:**
- View all orders with advanced filtering
- Manual order status updates
- Dispute resolution management
- Refund approval workflow
- Cancel orders on behalf of users/vendors

### 9.4 Content Management
**Product Moderation:**
- Review reported products
- Moderate product descriptions and images
- Bulk product operations
- Category management

**Advertisement Management:**
```json
{
  "ad_id": "uuid",
  "title": "string",
  "description": "text (optional)",
  "image_url": "url",
  "click_url": "url",
  "start_date": "datetime",
  "end_date": "datetime",
  "is_active": "boolean",
  "impressions": "integer (default: 0)",
  "clicks": "integer (default: 0)",
  "ctr": "decimal (calculated field)",
  "created_by": "uuid (admin user_id)",
  "created_at": "datetime"
}
```

### 9.5 System Configuration
**Global Settings:**
- Search radius configuration (default: 250km)
- Escrow release mode (automatic/manual)
- Global commission rates
- Payment gateway configuration
- Email/SMS service configuration
- Maximum file upload sizes
- Order auto-cancellation timeouts

---

## 10. Analytics and Reporting

### 10.1 Vendor Dashboard Analytics
**Sales Metrics:**
- Total revenue (lifetime and period-based)
- Order count and average order value
- Best-selling products and categories
- Sales trends and forecasting
- Commission deductions summary

**Performance Metrics:**
- Profile views and conversion rates
- Product view-to-order conversion
- Customer ratings and reviews
- Response time to customer inquiries
- Order fulfillment performance

### 10.2 Admin Analytics
**Business Intelligence:**
- Platform-wide sales analytics
- User acquisition and retention metrics
- Geographic distribution heatmaps
- Top-performing vendors and products
- Revenue breakdown by categories

**Operational Metrics:**
- Order processing times
- Customer support ticket analytics
- System performance metrics
- User engagement analytics
- Refund and dispute statistics

**Financial Reports:**
- Commission earned reports
- Payout summaries
- Tax calculation reports
- Revenue forecasting
- Cost analysis

### 10.3 Reporting Features
**Automated Reports:**
- Daily sales summary (email to admins)
- Weekly vendor performance reports
- Monthly platform analytics
- Quarterly financial reports

**Export Capabilities:**
- CSV export for all major data entities
- PDF reports with charts and graphs
- Excel exports with advanced formatting
- API endpoints for third-party integrations

---

## 11. API Specifications

### 11.1 RESTful API Design
**Base URL**: `https://api.kabaadwala.com/v1/`

**Authentication**: JWT-based authentication with refresh tokens

**Rate Limiting**: 
- Authenticated users: 1000 requests/hour
- Anonymous users: 100 requests/hour
- Admin users: Unlimited

### 11.2 Core API Endpoints

**Authentication Endpoints:**
```
POST /auth/register/          # User registration
POST /auth/login/             # User login
POST /auth/logout/            # User logout
POST /auth/refresh/           # Token refresh
POST /auth/verify-email/      # Email verification
POST /auth/resend-activation/ # Resend activation email
POST /auth/forgot-password/   # Password reset request
POST /auth/reset-password/    # Password reset confirmation
POST /auth/send-otp/          # Send 2FA OTP
POST /auth/verify-otp/        # Verify 2FA OTP
```

**User Management:**
```
GET    /users/profile/        # Get user profile
PUT    /users/profile/        # Update user profile
GET    /users/addresses/      # List user addresses
POST   /users/addresses/      # Create new address
PUT    /users/addresses/{id}/ # Update address
DELETE /users/addresses/{id}/ # Delete address
POST   /users/set-default-address/{id}/ # Set default address
```

**Product Catalog:**
```
GET    /products/             # List products (with filters)
GET    /products/{id}/        # Get product details
POST   /products/             # Create product (vendor only)
PUT    /products/{id}/        # Update product (vendor only)
DELETE /products/{id}/        # Delete product (vendor only)
GET    /categories/           # List categories
GET    /products/search/      # Search products
POST   /products/{id}/wishlist/ # Add to wishlist
```

**Order Management:**
```
GET    /orders/               # List user orders
POST   /orders/               # Create new order
GET    /orders/{id}/          # Get order details
PUT    /orders/{id}/status/   # Update order status (vendor)
POST   /orders/{id}/cancel/   # Cancel order
GET    /orders/{id}/invoice/  # Download invoice PDF
```

**Vendor Operations:**
```
GET    /vendor/profile/       # Get vendor profile
PUT    /vendor/profile/       # Update vendor profile
POST   /vendor/kyc/           # Submit KYC documents
GET    /vendor/orders/        # List vendor orders
GET    /vendor/analytics/     # Vendor analytics data
POST   /vendor/payout-request/ # Request payout
GET    /vendor/payouts/       # List payout history
```

**Communication:**
```
GET    /chat/rooms/           # List chat rooms for user
GET    /chat/rooms/{id}/messages/ # Get chat messages
POST   /chat/rooms/{id}/messages/ # Send message
WebSocket: /ws/chat/{room_id}/ # Real-time chat
```

### 11.3 API Response Format
**Success Response:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": { ... }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 11.4 Mobile App Considerations
- Offline capability for product browsing
- Image compression and optimization
- Progressive loading for large product lists
- Push notification integration
- Biometric authentication support
- Location-based services integration

---

## 12. Security Requirements

### 12.1 Authentication Security
- JWT tokens with secure expiration (15 minutes access, 7 days refresh)
- Password hashing using bcrypt with salt rounds ≥ 12
- Account lockout after 5 failed login attempts
- 2FA mandatory for all user types
- Session management with secure cookies

### 12.2 Data Protection
- HTTPS enforcement across all endpoints
- Database encryption for sensitive data (PAN, bank details)
- File upload restrictions and virus scanning
- Input validation and sanitization
- SQL injection prevention
- XSS protection headers

### 12.3 API Security
- Rate limiting per user/IP
- Request size limitations
- CORS policy configuration
- API key validation for third-party integrations
- Request logging and monitoring

### 12.4 File Security
- Allowed file types: `.jpg`, `.jpeg`, `.png`, `.pdf`, `.doc`, `.docx`
- Maximum file size: 10MB per file
- Virus scanning for all uploads
- Secure file storage with access controls
- Image optimization and resizing

### 12.5 Privacy Compliance
- GDPR compliance for data handling
- User data export functionality
- Right to deletion implementation
- Privacy policy and terms of service
- Cookie consent management

---

## 13. Technical Stack

### 13.1 Backend Framework
- **Language**: Python 3.11+
- **Framework**: Django 4.2+ with Django REST Framework
- **ASGI Server**: Uvicorn or Daphne for WebSocket support
- **Task Queue**: Celery with Redis broker
- **Database**: PostgreSQL 14+ with PostGIS extension

### 13.2 Frontend Technologies
- **Admin Panel**: Django Admin (customized) or React-based dashboard
- **API Documentation**: Django REST Framework + Swagger/OpenAPI
- **Real-time**: Django Channels with WebSocket support

### 13.3 Infrastructure
- **Web Server**: Nginx (reverse proxy and static files)
- **Application Server**: Gunicorn (WSGI) + Uvicorn (ASGI)
- **Cache**: Redis (session storage, task broker, caching)
- **Search**: Elasticsearch (optional, for advanced search)
- **File Storage**: AWS S3 or DigitalOcean Spaces
- **CDN**: CloudFlare or AWS CloudFront

### 13.4 Development Tools
- **Version Control**: Git with GitFlow workflow
- **Containerization**: Docker and Docker Compose
- **Testing**: pytest with factory_boy for test data
- **Code Quality**: Black (formatting), flake8 (linting), mypy (type checking)
- **Documentation**: Sphinx for code documentation

### 13.5 Monitoring and Logging
- **Error Tracking**: Sentry
- **Application Monitoring**: New Relic or DataDog
- **Log Management**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Performance Monitoring**: Prometheus + Grafana
- **Uptime Monitoring**: Pingdom or UptimeRobot

---

## 14. Database Schema

### 14.1 Core Tables
**Users Table:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    full_name VARCHAR(255),
    mobile_number VARCHAR(20),
    profile_photo VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Addresses Table:**
```sql
CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    address_type VARCHAR(20) DEFAULT 'home',
    recipient_name VARCHAR(255) NOT NULL,
    recipient_phone VARCHAR(20) NOT NULL,
    flat_number VARCHAR(100),
    street_address TEXT NOT NULL,
    landmark VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    state VARCHAR(100) NOT NULL,
    country VARCHAR(100) DEFAULT 'India',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 14.2 Vendor Tables
**Vendors Table:**
```sql
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    store_name VARCHAR(255) UNIQUE NOT NULL,
    store_logo VARCHAR(500),
    store_banner VARCHAR(500),
    business_email VARCHAR(254) NOT NULL,
    business_phone VARCHAR(20) NOT NULL,
    store_description TEXT,
    store_address JSONB NOT NULL,
    business_hours JSONB,
    kyc_status VARCHAR(20) DEFAULT 'pending',
    kyc_rejection_reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 14.3 Product Tables
**Categories Table:**
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    parent_category_id UUID REFERENCES categories(id),
    icon VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    commission_rate DECIMAL(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Products Table:**
```sql
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID REFERENCES vendors(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    images JSONB DEFAULT '[]',
    price DECIMAL(10, 2) NOT NULL,
    unit VARCHAR(20) DEFAULT 'piece',
    stock_quantity INTEGER DEFAULT 0,
    minimum_order_quantity INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    sku VARCHAR(100) UNIQUE,
    tags JSONB DEFAULT '[]',
    specifications JSONB DEFAULT '{}',
    views_count INTEGER DEFAULT 0,
    orders_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 14.4 Order Tables
**Orders Table:**
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id),
    vendor_id UUID REFERENCES vendors(id),
    delivery_address JSONB NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    delivery_charges DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',
    order_status VARCHAR(30) DEFAULT 'placed',
    payment_method VARCHAR(20) DEFAULT 'escrow',
    escrow_status VARCHAR(20) DEFAULT 'held',
    notes TEXT,
    estimated_delivery TIMESTAMP WITH TIME ZONE,
    actual_delivery TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 14.6 Wallet Database Schema

**Wallets Table:**
```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    current_balance DECIMAL(10, 2) DEFAULT 0.00 CHECK (current_balance >= 0),
    total_recharged DECIMAL(10, 2) DEFAULT 0.00,
    total_spent DECIMAL(10, 2) DEFAULT 0.00,
    held_amount DECIMAL(10, 2) DEFAULT 0.00 CHECK (held_amount >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT wallet_balance_check CHECK (current_balance >= held_amount)
);
```

**Wallet Transactions Table:**
```sql
CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    wallet_id UUID REFERENCES wallets(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('recharge', 'hold', 'deduct', 'release', 'refund')),
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    payment_gateway_ref VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    description TEXT,
    balance_before DECIMAL(10, 2) NOT NULL,
    balance_after DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for wallet operations
CREATE INDEX idx_wallets_user_id ON wallets(user_id);
CREATE INDEX idx_wallet_transactions_wallet_id ON wallet_transactions(wallet_id);
CREATE INDEX idx_wallet_transactions_order_id ON wallet_transactions(order_id);
CREATE INDEX idx_wallet_transactions_type ON wallet_transactions(transaction_type);
CREATE INDEX idx_wallet_transactions_status ON wallet_transactions(status);
```
```sql
-- Performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_addresses_user_id ON addresses(user_id);
CREATE INDEX idx_addresses_is_default ON addresses(is_default);
CREATE INDEX idx_vendors_user_id ON vendors(user_id);
CREATE INDEX idx_vendors_kyc_status ON vendors(kyc_status);
CREATE INDEX idx_products_vendor_id ON products(vendor_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_products_is_active ON products(is_active);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_vendor_id ON orders(vendor_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Spatial indexes for location-based queries
CREATE INDEX idx_addresses_location ON addresses USING GIST(ST_MakePoint(longitude, latitude));

-- Composite indexes for common queries
CREATE INDEX idx_products_active_vendor ON products(vendor_id, is_active);
CREATE INDEX idx_orders_user_status ON orders(user_id, order_status);
CREATE INDEX idx_products_category_active ON products(category_id, is_active);
```

---

## 15. Django Frontend UI Specifications

### 15.1 Bootstrap Integration
**CDN Links (Bootstrap 5.3.0):**
```html
<!-- CSS -->
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">

<!-- JavaScript -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
```

### 15.2 Base Template Structure
**base.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}KABAADWALA™{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <style>
        :root {
            --primary-color: #2563eb;
            --secondary-color: #64748b;
            --success-color: #16a34a;
            --warning-color: #d97706;
            --danger-color: #dc2626;
            --dark-color: #1e293b;
        }
        
        .navbar-brand {
            font-weight: bold;
            color: var(--primary-color) !important;
        }
        
        .wallet-balance {
            background: linear-gradient(135deg, var(--primary-color), #3b82f6);
            color: white;
            border-radius: 10px;
            padding: 1rem;
        }
        
        .product-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: none;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        
        .btn-wallet {
            background: linear-gradient(135deg, var(--success-color), #22c55e);
            border: none;
            color: white;
        }
        
        .btn-wallet:hover {
            background: linear-gradient(135deg, #15803d, var(--success-color));
            color: white;
        }
        
        .order-status {
            font-size: 0.8rem;
            padding: 0.25rem 0.5rem;
            border-radius: 15px;
            font-weight: 500;
        }
        
        .status-placed { background-color: #dbeafe; color: #1e40af; }
        .status-confirmed { background-color: #fef3c7; color: #92400e; }
        .status-shipped { background-color: #e0e7ff; color: #5b21b6; }
        .status-delivered { background-color: #dcfce7; color: #166534; }
        .status-completed { background-color: #d1fae5; color: #065f46; }
    </style>
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
        <div class="container">
            <a class="navbar-brand" href="{% url 'home' %}">
                <i class="bi bi-recycle"></i> KABAADWALA™
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'products:list' %}">Products</a>
                    </li>
                    {% if user.is_authenticated %}
                        {% if user.is_vendor %}
                            <li class="nav-item">
                                <a class="nav-link" href="{% url 'vendor:dashboard' %}">Vendor Dashboard</a>
                            </li>
                        {% endif %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'orders:list' %}">My Orders</a>
                        </li>
                    {% endif %}
                </ul>
                
                <ul class="navbar-nav">
                    {% if user.is_authenticated %}
                        <!-- Wallet Balance -->
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle btn btn-outline-success btn-sm me-2" href="#" role="button" data-bs-toggle="dropdown">
                                <i class="bi bi-wallet2"></i> ₹{{ user.wallet.current_balance|floatformat:2 }}
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="{% url 'wallet:recharge' %}">
                                    <i class="bi bi-plus-circle"></i> Recharge Wallet
                                </a></li>
                                <li><a class="dropdown-item" href="{% url 'wallet:transactions' %}">
                                    <i class="bi bi-list-ul"></i> Transaction History
                                </a></li>
                            </ul>
                        </li>
                        
                        <!-- User Menu -->
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                                {% if user.profile_photo %}
                                    <img src="{{ user.profile_photo.url }}" alt="Profile" class="rounded-circle" width="24" height="24">
                                {% else %}
                                    <i class="bi bi-person-circle"></i>
                                {% endif %}
                                {{ user.full_name|default:user.username }}
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="{% url 'users:profile' %}">
                                    <i class="bi bi-person"></i> Profile
                                </a></li>
                                <li><a class="dropdown-item" href="{% url 'users:addresses' %}">
                                    <i class="bi bi-geo-alt"></i> Addresses
                                </a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="{% url 'auth:logout' %}">
                                    <i class="bi bi-box-arrow-right"></i> Logout
                                </a></li>
                            </ul>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'auth:login' %}">Login</a>
                        </li>
                        <li class="nav-item">
                            <a class="btn btn-primary btn-sm" href="{% url 'auth:register' %}">Sign Up</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <!-- Messages -->
    {% if messages %}
        <div class="container mt-3">
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    <i class="bi bi-{% if message.tags == 'success' %}check-circle{% elif message.tags == 'error' %}exclamation-circle{% elif message.tags == 'warning' %}exclamation-triangle{% else %}info-circle{% endif %}"></i>
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        </div>
    {% endif %}

    <!-- Main Content -->
    <main>
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="bg-dark text-white mt-5 py-4">
        <div class="container">
            <div class="row">
                <div class="col-md-4">
                    <h5><i class="bi bi-recycle"></i> KABAADWALA™</h5>
                    <p class="text-muted">Your trusted hyperlocal scrap marketplace</p>
                </div>
                <div class="col-md-4">
                    <h6>Quick Links</h6>
                    <ul class="list-unstyled">
                        <li><a href="{% url 'pages:about' %}" class="text-muted">About Us</a></li>
                        <li><a href="{% url 'pages:contact' %}" class="text-muted">Contact</a></li>
                        <li><a href="{% url 'pages:privacy' %}" class="text-muted">Privacy Policy</a></li>
                        <li><a href="{% url 'pages:terms' %}" class="text-muted">Terms of Service</a></li>
                    </ul>
                </div>
                <div class="col-md-4">
                    <h6>Support</h6>
                    <p class="text-muted">
                        <i class="bi bi-envelope"></i> support@kabaadwala.com<br>
                        <i class="bi bi-phone"></i> +91-9999999999
                    </p>
                </div>
            </div>
        </div>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 15.3 User Dashboard Template
**dashboard.html:**
```html
{% extends 'base.html' %}

{% block title %}Dashboard - KABAADWALA™{% endblock %}

{% block content %}
<div class="container my-4">
    <div class="row">
        <!-- Sidebar -->
        <div class="col-md-3">
            <div class="card">
                <div class="card-body">
                    <div class="text-center mb-3">
                        {% if user.profile_photo %}
                            <img src="{{ user.profile_photo.url }}" alt="Profile" class="rounded-circle mb-2" width="80" height="80">
                        {% else %}
                            <i class="bi bi-person-circle display-3 text-muted"></i>
                        {% endif %}
                        <h6>{{ user.full_name|default:user.username }}</h6>
                        <small class="text-muted">{{ user.email }}</small>
                    </div>
                    
                    <!-- Wallet Card -->
                    <div class="wallet-balance text-center mb-3">
                        <h5><i class="bi bi-wallet2"></i> Wallet Balance</h5>
                        <h3>₹{{ user.wallet.current_balance|floatformat:2 }}</h3>
                        <a href="{% url 'wallet:recharge' %}" class="btn btn-light btn-sm">
                            <i class="bi bi-plus-circle"></i> Recharge
                        </a>
                    </div>
                    
                    <!-- Navigation -->
                    <div class="list-group list-group-flush">
                        <a href="{% url 'users:dashboard' %}" class="list-group-item list-group-item-action">
                            <i class="bi bi-speedometer2"></i> Dashboard
                        </a>
                        <a href="{% url 'orders:list' %}" class="list-group-item list-group-item-action">
                            <i class="bi bi-box-seam"></i> My Orders
                        </a>
                        <a href="{% url 'users:addresses' %}" class="list-group-item list-group-item-action">
                            <i class="bi bi-geo-alt"></i> Addresses
                        </a>
                        <a href="{% url 'wallet:transactions' %}" class="list-group-item list-group-item-action">
                            <i class="bi bi-list-ul"></i> Wallet History
                        </a>
                        <a href="{% url 'users:profile' %}" class="list-group-item list-group-item-action">
                            <i class="bi bi-person"></i> Profile Settings
                        </a>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="col-md-9">
            <div class="row">
                <!-- Stats Cards -->
                <div class="col-md-4 mb-3">
                    <div class="card bg-primary text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4>{{ stats.total_orders }}</h4>
                                    <small>Total Orders</small>
                                </div>
                                <i class="bi bi-box-seam display-6"></i>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-3">
                    <div class="card bg-success text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4>₹{{ stats.total_spent|floatformat:2 }}</h4>
                                    <small>Total Spent</small>
                                </div>
                                <i class="bi bi-currency-rupee display-6"></i>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-3">
                    <div class="card bg-info text-white">
                        <div class="card-body">
                            <div class="d-flex justify-content-between">
                                <div>
                                    <h4>{{ stats.pending_orders }}</h4>
                                    <small>Pending Orders</small>
                                </div>
                                <i class="bi bi-clock display-6"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Orders -->
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0">Recent Orders</h5>
                    <a href="{% url 'orders:list' %}" class="btn btn-sm btn-outline-primary">View All</a>
                </div>
                <div class="card-body">
                    {% if recent_orders %}
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Order #</th>
                                        <th>Vendor</th>
                                        <th>Amount</th>
                                        <th>Status</th>
                                        <th>Date</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for order in recent_orders %}
                                    <tr>
                                        <td><strong>#{{ order.order_number }}</strong></td>
                                        <td>{{ order.vendor.store_name }}</td>
                                        <td>₹{{ order.total_amount|floatformat:2 }}</td>
                                        <td>
                                            <span class="order-status status-{{ order.order_status }}">
                                                {{ order.get_order_status_display }}
                                            </span>
                                        </td>
                                        <td>{{ order.created_at|date:"M d, Y" }}</td>
                                        <td>
                                            <a href="{% url 'orders:detail' order.id %}" class="btn btn-sm btn-outline-primary">
                                                View
                                            </a>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    {% else %}
                        <div class="text-center py-4">
                            <i class="bi bi-box-seam display-1 text-muted"></i>
                            <h5 class="mt-3">No orders yet</h5>
                            <p class="text-muted">Start shopping to see your orders here</p>
                            <a href="{% url 'products:list' %}" class="btn btn-primary">Browse Products</a>
                        </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 15.4 Wallet Recharge Template
**wallet/recharge.html:**
```html
{% extends 'base.html' %}

{% block title %}Recharge Wallet - KABAADWALA™{% endblock %}

{% block content %}
<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="card shadow">
                <div class="card-header bg-success text-white text-center">
                    <h4><i class="bi bi-wallet2"></i> Recharge Wallet</h4>
                </div>
                <div class="card-body">
                    <!-- Current Balance -->
                    <div class="wallet-balance text-center mb-4">
                        <h6>Current Balance</h6>
                        <h3>₹{{ user.wallet.current_balance|floatformat:2 }}</h3>
                    </div>
                    
                    <!-- Recharge Form -->
                    <form method="post" id="recharge-form">
                        {% csrf_token %}
                        <div class="mb-3">
                            <label for="amount" class="form-label">Recharge Amount</label>
                            <div class="input-group">
                                <span class="input-group-text">₹</span>
                                <input type="number" class="form-control" id="amount" name="amount" 
                                       min="100" max="50000" step="1" required>
                            </div>
                            <div class="form-text">Minimum: ₹100, Maximum: ₹50,000</div>
                        </div>
                        
                        <!-- Quick Amount Buttons -->
                        <div class="mb-3">
                            <label class="form-label">Quick Select</label>
                            <div class="d-flex gap-2 flex-wrap">
                                <button type="button" class="btn btn-outline-success btn-sm quick-amount" data-amount="500">₹500</button>
                                <button type="button" class="btn btn-outline-success btn-sm quick-amount" data-amount="1000">₹1,000</button>
                                <button type="button" class="btn btn-outline-success btn-sm quick-amount" data-amount="2000">₹2,000</button>
                                <button type="button" class="btn btn-outline-success btn-sm quick-amount" data-amount="5000">₹5,000</button>
                                <button type="button" class="btn btn-outline-success btn-sm quick-amount" data-amount="10000">₹10,000</button>
                            </div>
                        </div>
                        
                        <!-- Payment Method -->
                        <div class="mb-3">
                            <label class="form-label">Payment Method</label>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="payment_method" id="upi" value="upi" checked>
                                <label class="form-check-label" for="upi">
                                    <i class="bi bi-phone"></i> UPI
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="payment_method" id="card" value="card">
                                <label class="form-check-label" for="card">
                                    <i class="bi bi-credit-card"></i> Credit/Debit Card
                                </label>
                            </div>
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="payment_method" id="netbanking" value="netbanking">
                                <label class="form-check-label" for="netbanking">
                                    <i class="bi bi-bank"></i> Net Banking
                                </label>
                            </div>
                        </div>
                        
                        <!-- Terms -->
                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" id="terms" required>
                            <label class="form-check-label" for="terms">
                                I agree to the <a href="{% url 'pages:terms' %}" target="_blank">Terms & Conditions</a>
                            </label>
                        </div>
                        
                        <button type="submit" class="btn btn-success w-100" id="recharge-btn">
                            <i class="bi bi-shield-check"></i> Proceed to Pay
                        </button>
                    </form>
                </div>
            </div>
            
            <!-- Recent Recharges -->
            <div class="card mt-4">
                <div class="card-header">
                    <h6 class="mb-0">Recent Recharges</h6>
                </div>
                <div class="card-body">
                    {% if recent_recharges %}
                        {% for transaction in recent_recharges %}
                        <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                            <div>
                                <strong>₹{{ transaction.amount|floatformat:2 }}</strong>
                                <small class="text-muted d-block">{{ transaction.created_at|date:"M d, Y H:i" }}</small>
                            </div>
                            <span class="badge bg-success">Completed</span>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p class="text-muted text-center">No recent recharges</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
$(document).ready(function() {
    // Quick amount selection
    $('.quick-amount').click(function() {
        $('#amount').val($(this).data('amount'));
        $('.quick-amount').removeClass('btn-success').addClass('btn-outline-success');
        $(this).removeClass('btn-outline-success').addClass('btn-success');
    });
    
    // Form submission
    $('#recharge-form').submit(function(e) {
        e.preventDefault();
        
        const amount = $('#amount').val();
        if (amount < 100 || amount > 50000) {
            alert('

### 15.1 Infrastructure Architecture
```
Internet → Load Balancer → Nginx → Django App Servers
                                 ↓
                            WebSocket Servers
                                 ↓
                         Database Cluster (PostgreSQL)
                                 ↓
                           Cache Layer (Redis)
                                 ↓
                         Background Workers (Celery)
```

### 15.2 Server Specifications

**Production Environment:**
- **Application Servers**: 3+ instances (2 CPU cores, 4GB RAM each)
- **Database Server**: 1 primary + 1 read replica (4 CPU cores, 8GB RAM, SSD storage)
- **Redis Server**: 1 instance (2 CPU cores, 4GB RAM)
- **Load Balancer**: 1 instance (2 CPU cores, 2GB RAM)
- **File Storage**: AWS S3 or equivalent cloud storage

**Staging Environment:**
- **Application Server**: 1 instance (2 CPU cores, 2GB RAM)
- **Database Server**: 1 instance (2 CPU cores, 4GB RAM)
- **Redis Server**: 1 instance (1 CPU core, 1GB RAM)

### 15.3 Docker Configuration

**Dockerfile for Django Application:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "kabaadwala.wsgi:application"]
```

**Docker Compose Configuration:**
```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:14-3.2
    environment:
      POSTGRES_DB: kabaadwala
      POSTGRES_USER: kabaadwala_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn kabaadwala.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://kabaadwala_user:${DB_PASSWORD}@db:5432/kabaadwala
      - REDIS_URL=redis://redis:6379/0

  celery:
    build: .
    command: celery -A kabaadwala worker -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://kabaadwala_user:${DB_PASSWORD}@db:5432/kabaadwala
      - REDIS_URL=redis://redis:6379/0

  celery-beat:
    build: .
    command: celery -A kabaadwala beat -l info
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://kabaadwala_user:${DB_PASSWORD}@db:5432/kabaadwala
      - REDIS_URL=redis://redis:6379/0

volumes:
  postgres_data:
```

### 15.4 Environment Configuration

**Environment Variables:**
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/kabaadwala
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kabaadwala
DB_USER=kabaadwala_user
DB_PASSWORD=secure_password

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=api.kabaadwala.com,www.kabaadwala.com
CORS_ALLOWED_ORIGINS=https://kabaadwala.com,https://www.kabaadwala.com

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@kabaadwala.com
EMAIL_HOST_PASSWORD=email_password

# File Storage
USE_S3=True
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=kabaadwala-media
AWS_S3_REGION_NAME=us-east-1

# Payment Gateway
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# SMS Service
SMS_API_KEY=your_sms_api_key
SMS_SENDER_ID=KBDWLA

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
```

### 15.5 SSL/TLS Configuration

**Nginx SSL Configuration:**
```nginx
server {
    listen 80;
    server_name api.kabaadwala.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.kabaadwala.com;

    ssl_certificate /etc/letsencrypt/live/api.kabaadwala.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.kabaadwala.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/www/kabaadwala/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/kabaadwala/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

### 15.6 Backup and Recovery

**Database Backup Strategy:**
```bash
#!/bin/bash
# Daily backup script
BACKUP_DIR="/backups/postgresql"
DB_NAME="kabaadwala"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -h localhost -U kabaadwala_user $DB_NAME | gzip > "$BACKUP_DIR/backup_${DATE}.sql.gz"

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/backup_${DATE}.sql.gz" s3://kabaadwala-backups/database/
```

**Media Files Backup:**
```bash
#!/bin/bash
# Weekly media backup
MEDIA_DIR="/var/www/kabaadwala/media"
BACKUP_DIR="/backups/media"
DATE=$(date +%Y%m%d)

# Create backup
tar -czf "$BACKUP_DIR/media_backup_${DATE}.tar.gz" -C "$MEDIA_DIR" .

# Upload to S3
aws s3 cp "$BACKUP_DIR/media_backup_${DATE}.tar.gz" s3://kabaadwala-backups/media/
```

### 15.7 Monitoring and Alerting

**Health Check Endpoints:**
```python
# In Django views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """System health check endpoint"""
    try:
        # Database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Redis check
        cache.set('health_check', 'ok', 30)
        cache.get('health_check')
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=503)
```

**Prometheus Metrics Configuration:**
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Custom metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_USERS = Gauge('active_users_total', 'Total active users')
ORDER_COUNT = Counter('orders_total', 'Total orders placed')
```

---

## 16. Testing Strategy

### 16.1 Testing Framework
- **Unit Tests**: pytest with factory_boy for test data generation
- **Integration Tests**: Django TestCase with database transactions
- **API Tests**: Django REST Framework APITestCase
- **Load Testing**: Locust or Artillery for performance testing
- **Security Testing**: OWASP ZAP for vulnerability scanning

### 16.2 Test Coverage Requirements
- **Minimum Coverage**: 80% overall code coverage
- **Critical Functions**: 95% coverage for payment and authentication
- **API Endpoints**: 100% coverage for all public endpoints
- **Models**: 90% coverage for model methods and properties

### 16.3 Test Data Management
```python
# factories.py
import factory
from django.contrib.auth import get_user_model
from .models import Vendor, Product, Order

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    full_name = factory.Faker('name')
    is_verified = True
    is_active = True

class VendorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vendor
    
    user = factory.SubFactory(UserFactory)
    store_name = factory.Faker('company')
    business_email = factory.LazyAttribute(lambda obj: f"{obj.store_name.lower()}@business.com")
    kyc_status = 'approved'

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product
    
    vendor = factory.SubFactory(VendorFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text')
    price = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    stock_quantity = factory.Faker('random_int', min=1, max=100)
```

### 16.4 Continuous Integration
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgis/postgis:14-3.2
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_kabaadwala
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install coverage pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_kabaadwala
        REDIS_URL: redis://localhost:6379/0
      run: |
        coverage run -m pytest
        coverage report --fail-under=80
        coverage xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

---

## 17. Performance Optimization

### 17.1 Database Optimization
- **Query Optimization**: Use select_related() and prefetch_related() for foreign key relationships
- **Database Indexing**: Strategic indexes on frequently queried fields
- **Connection Pooling**: pgbouncer for PostgreSQL connection management
- **Read Replicas**: Separate read and write operations
- **Query Monitoring**: pg_stat_statements for query analysis

### 17.2 Caching Strategy
```python
# cache.py
from django.core.cache import cache
from django.conf import settings

def cache_product_list(category_id=None, radius=None):
    """Cache product listings by category and location"""
    cache_key = f"products:{category_id}:{radius}"
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        # Generate product list
        products = Product.objects.filter(is_active=True)
        if category_id:
            products = products.filter(category_id=category_id)
        
        cached_data = list(products.values())
        cache.set(cache_key, cached_data, timeout=300)  # 5 minutes
    
    return cached_data

# Cache invalidation
def invalidate_product_cache(product_instance):
    """Invalidate related cache entries when product changes"""
    category_id = product_instance.category_id
    vendor_id = product_instance.vendor_id
    
    # Clear category-based cache
    cache.delete_pattern(f"products:{category_id}:*")
    cache.delete_pattern(f"vendor:{vendor_id}:products")
```

### 17.3 API Performance
- **Pagination**: Implement cursor-based pagination for large datasets
- **Field Selection**: Allow clients to specify required fields
- **Response Compression**: Enable gzip compression
- **API Versioning**: Maintain backward compatibility

```python
# serializers.py
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """Serializer that allows dynamic field selection"""
    
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
```

### 17.4 File Upload Optimization
```python
# utils.py
from PIL import Image
import boto3
from django.conf import settings

def optimize_image(image_file, max_width=800, quality=85):
    """Optimize uploaded images for web delivery"""
    img = Image.open(image_file)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    
    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    # Save optimized version
    from io import BytesIO
    output = BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    output.seek(0)
    
    return output
```

---

## 18. Maintenance and Support

### 18.1 Regular Maintenance Tasks
**Daily Tasks:**
- Database backup verification
- Log file rotation and cleanup
- System resource monitoring
- Failed job retry processing

**Weekly Tasks:**
- Database performance analysis
- Security patch updates
- Cache hit rate analysis
- User activity reports

**Monthly Tasks:**
- Full system backup testing
- Performance benchmarking
- Security vulnerability scanning
- Capacity planning review

### 18.2 Monitoring Dashboards
**System Metrics:**
- CPU and memory usage
- Database connection pool status
- Redis memory usage
- Disk space utilization
- Network throughput

**Application Metrics:**
- Request response times
- Error rates by endpoint
- Active user count
- Order processing times
- Payment success rates

**Business Metrics:**
- Daily/monthly active users
- Revenue trends
- Order conversion rates
- Vendor onboarding rates
- Customer satisfaction scores

### 18.3 Troubleshooting Guide
**Common Issues and Solutions:**

1. **High Database Load**
   - Check for missing indexes
   - Analyze slow query log
   - Review connection pool settings
   - Consider read replica scaling

2. **Memory Issues**
   - Monitor Celery worker memory usage
   - Check for memory leaks in background tasks
   - Review cache memory allocation
   - Optimize image processing

3. **Authentication Problems**
   - Verify email service configuration
   - Check OTP generation and expiry
   - Review JWT token settings
   - Monitor failed login attempts

4. **File Upload Issues**
   - Check S3 credentials and permissions
   - Verify file size limits
   - Monitor storage quotas
   - Test virus scanning service

---

## 19. Future Enhancements

### 19.1 Phase 2 Features
- **Advanced Search**: Elasticsearch integration with filters and facets
- **Recommendation Engine**: ML-based product recommendations
- **Multi-language Support**: i18n for regional expansion
- **Advanced Analytics**: Business intelligence dashboards
- **Vendor Subscriptions**: Premium vendor accounts with additional features

### 19.2 Phase 3 Features
- **Mobile Apps**: Native Android and iOS applications
- **Voice Search**: Voice-based product search
- **AR Integration**: Augmented reality for product visualization
- **Blockchain Integration**: Supply chain transparency
- **IoT Integration**: Smart weighing and quality assessment

### 19.3 Scalability Roadmap
- **Microservices Migration**: Break monolith into domain services
- **Event-Driven Architecture**: Implement event sourcing
- **Global CDN**: Multi-region content delivery
- **AI/ML Platform**: Dedicated ML infrastructure
- **Real-time Analytics**: Stream processing with Kafka

---

## 20. Conclusion

This comprehensive System Requirements Specification provides a detailed blueprint for developing KABAADWALA™, a production-ready hyperlocal scrap marketplace. The specification covers all aspects from authentication and user management to deployment and monitoring, ensuring a scalable, secure, and maintainable platform.

### 20.1 Key Deliverables
- Complete user authentication system with 2FA
- Hyperlocal vendor and product discovery
- Secure escrow payment system
- Real-time communication platform
- Comprehensive admin dashboard
- Mobile-ready API architecture
- Production deployment guide

### 20.2 Success Metrics
- **User Engagement**: 70%+ monthly active user retention
- **Transaction Success**: 95%+ payment success rate
- **Performance**: <2 second average response time
- **Availability**: 99.9% uptime SLA
- **Security**: Zero critical security vulnerabilities

### 20.3 Development Timeline
- **Phase 1** (Months 1-4): Core platform development
- **Phase 2** (Months 5-6): Testing and optimization
- **Phase 3** (Months 7-8): Deployment and launch
- **Phase 4** (Ongoing): Maintenance and enhancements

This SRS serves as the definitive guide for development teams, ensuring consistent implementation across all platform components while maintaining the flexibility


read this and tell me do it have wallet system?