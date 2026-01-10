# 🎬 Jetflix - Netflix-Inspired Movie Streaming Platform

A premium movie streaming platform with eSewa payment integration and Netflix-like user experience.

## ✨ Features Implemented

### 🔐 Authentication & Access Control
- **Home Page = Login Page**: Landing page is the login/sign-up interface
- **Payment-Gated Access**: Movies are completely inaccessible without authentication AND payment
- **Secure Session Management**: Server-side payment verification
- **Middleware Protection**: Automatic redirect to payment for unpaid users

### 💳 Payment Integration
- **eSewa Sandbox Integration**: Real eSewa payment gateway (sandbox mode)
- **Demo Payment Option**: Instant access for testing purposes
- **Payment Flow**: Auth → Payment → Dashboard
- **Transaction Tracking**: Secure transaction ID and reference storage

### 🎨 Netflix-Inspired Design
- **Premium UI/UX**: Clean, minimal, Netflix-like interface
- **Consistent Design System**: Same colors, typography, and spacing throughout
- **Trust Signals**: Security badges, SSL indicators, privacy notices
- **Responsive Design**: Mobile-friendly across all devices

### 🛡️ Security & Best Practices
- **Server-Side Verification**: Backend validates all payments
- **CSRF Protection**: All forms protected against CSRF attacks
- **Session Security**: Secure authentication flow
- **Error Handling**: Graceful handling of payment failures

## 🚀 Quick Start

### 1. Start the Server
```bash
cd /Users/kushalbhattarai/Projects/Jetflix
python3 manage.py runserver
```

### 2. Access the Application
- **Home/Login Page**: http://localhost:8000
- **Registration**: http://localhost:8000/register/
- **Payment**: http://localhost:8000/payment/
- **Dashboard**: http://localhost:8000/dashboard/ (after payment)

### 3. Test the Flow
1. Visit http://localhost:8000 (login page)
2. Click "Sign up now" to create account
3. Complete registration → Auto-redirect to payment
4. Choose "Demo Payment" for instant access
5. Login again → Access movies dashboard

## 🔄 User Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Landing Page  │───▶│   Registration   │───▶│     Payment     │
│   (Login Form)  │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                                               │
         │                                               ▼
┌─────────────────┐                              ┌─────────────────┐
│ Movies Dashboard│◀─────────────────────────────│  Payment Success│
│   (Home Page)   │                              │   (Redirect)    │
└─────────────────┘                              └─────────────────┘
```

## 💰 Payment Options

### eSewa Sandbox
- **Merchant Code**: EPAYTEST
- **Amount**: Rs. 500 (one-time)
- **Status**: May be temporarily unavailable
- **Redirect**: Automatic form submission to eSewa

### Demo Payment
- **Purpose**: Testing and development
- **Process**: Instant completion
- **Access**: Immediate movie access
- **Recommended**: For demonstration purposes

## 🎯 Key Implementation Details

### URL Structure
```
/                    → Login page (home)
/register/           → Registration
/payment/            → Payment selection
/payment/success/    → eSewa success callback
/payment/failure/    → eSewa failure callback
/dashboard/          → Movies dashboard (post-payment)
/movies/             → Movie browsing and playback
```

### Authentication States
1. **Anonymous User**: Redirected to login page
2. **Authenticated + No Payment**: Redirected to payment page
3. **Authenticated + Paid**: Access to movies dashboard

### Payment Verification
```python
# Server-side payment check
has_payment = Payment.objects.filter(
    user=request.user,
    status='completed'
).exists()
```

## 🎨 Design System

### Colors
- **Primary Red**: #e50914 (Netflix red)
- **Background**: #141414 (Dark)
- **Cards**: rgba(0, 0, 0, 0.75) (Semi-transparent black)
- **Text**: #fff (White), #b3b3b3 (Gray)
- **Success**: #46d369 (Green)
- **Warning**: #e87c03 (Orange)

### Typography
- **Font Family**: 'Helvetica Neue', Helvetica, Arial, sans-serif
- **Headings**: 700-900 weight
- **Body**: 400-500 weight
- **Consistent Sizing**: rem-based scaling

### Components
- **Hero Sections**: Full-screen with background images
- **Form Cards**: Semi-transparent with backdrop blur
- **Trust Badges**: Subtle security indicators
- **Footer**: Minimal with essential links

## 🔧 Technical Architecture

### Models
```python
# Payment tracking
class Payment(models.Model):
    user = models.ForeignKey(User)
    amount = models.DecimalField(default=500.00)
    transaction_id = models.CharField(unique=True)
    esewa_ref_id = models.CharField()
    status = models.CharField(choices=PAYMENT_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
```

### Middleware
```python
# Payment-required middleware
class PaymentRequiredMiddleware:
    def __call__(self, request):
        if user.is_authenticated and not has_payment:
            return redirect('/payment/')
```

### Views
- **login_view**: Handles authentication and payment checks
- **register_view**: User creation with auto-login
- **payment_view**: Payment method selection
- **payment_success_view**: eSewa callback handling
- **home_page**: Movies dashboard (payment-gated)

## 🚨 Error Handling

### eSewa Service Unavailable
- **Detection**: Automatic service availability check
- **Fallback**: Clear messaging with demo payment option
- **User Experience**: Graceful degradation

### Payment Failures
- **Validation**: Server-side transaction verification
- **Retry Logic**: Allow users to retry payments
- **Clear Messaging**: Informative error messages

### Authentication Errors
- **Invalid Credentials**: Clear error messaging
- **Session Expiry**: Automatic redirect to login
- **CSRF Protection**: Built-in Django protection

## 📱 Responsive Design

### Breakpoints
- **Desktop**: 1024px+
- **Tablet**: 768px - 1023px
- **Mobile**: 480px - 767px
- **Small Mobile**: < 480px

### Adaptations
- **Grid Layouts**: Single column on mobile
- **Font Sizes**: Scaled appropriately
- **Touch Targets**: Minimum 44px for mobile
- **Navigation**: Simplified mobile navigation

## 🔒 Security Features

### Payment Security
- **Server-Side Validation**: All payments verified server-side
- **Transaction IDs**: Unique, non-guessable identifiers
- **HTTPS Ready**: SSL/TLS encryption support
- **No Client-Side Trust**: Frontend cannot bypass payment

### Authentication Security
- **Session Management**: Django's built-in session security
- **CSRF Protection**: All forms protected
- **Password Validation**: Django's password validators
- **Secure Redirects**: Validated redirect URLs

## 🎬 Content Protection

### Access Control
- **Middleware Protection**: Automatic enforcement
- **URL Protection**: Direct URL access blocked
- **API Protection**: All endpoints require authentication + payment
- **Video Streaming**: Protected video URLs

### User Experience
- **Seamless Flow**: Smooth transitions between states
- **Clear Messaging**: Users always know their status
- **Trust Building**: Security indicators throughout
- **Professional Feel**: Netflix-quality experience

## 🚀 Deployment Notes

### Environment Variables
```bash
# eSewa Configuration
ESEWA_MERCHANT_CODE=EPAYTEST
ESEWA_SUCCESS_URL=your-domain.com/payment/success/
ESEWA_FAILURE_URL=your-domain.com/payment/failure/

# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com
```

### Production Checklist
- [ ] Set DEBUG=False
- [ ] Configure proper SECRET_KEY
- [ ] Set up HTTPS/SSL
- [ ] Configure static files serving
- [ ] Set up proper database (PostgreSQL recommended)
- [ ] Configure email backend for notifications
- [ ] Set up monitoring and logging

## 📞 Support

### Testing Credentials
- **Demo User**: Create any username/password
- **Payment**: Use "Demo Payment" option
- **eSewa**: Use eSewa sandbox credentials (when available)

### Common Issues
1. **eSewa Unavailable**: Use demo payment option
2. **Payment Not Recognized**: Check transaction ID in admin
3. **Access Denied**: Ensure payment status is 'completed'

---

**Built with Django, Netflix-inspired design, and secure payment integration.**