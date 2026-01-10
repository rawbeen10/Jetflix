# Jetflix eSewa Payment Integration

## Implementation Summary

### 1. Payment Model (home/models.py)
- Created `Payment` model to track user payments
- Fields: user, amount (Rs. 500), transaction_id, esewa_ref_id, status, created_at, expires_at
- Auto-expires after 30 days
- Status tracking: pending, completed, failed

### 2. Authentication Flow Changes
- **Root URL (/)** now redirects to login page
- **Auth URLs** moved to `/auth/` prefix:
  - `/auth/login/` - Login page
  - `/auth/register/` - Registration page  
  - `/auth/payment/` - Payment page
  - `/auth/home/` - Homepage (after payment)

### 3. Payment Middleware (home/middleware.py)
- `PaymentRequiredMiddleware` enforces payment requirement
- Blocks access to all pages except login/register/payment for unpaid users
- Automatically redirects to payment page if no active payment

### 4. eSewa Integration
- **Payment Page**: `/auth/payment/` - Shows Rs. 500 payment option
- **eSewa Redirect**: Auto-submits form to eSewa sandbox
- **Success Handler**: `/auth/payment/success/` - Marks payment as completed
- **Failure Handler**: `/auth/payment/failure/` - Shows error message

### 5. User Flow
1. User visits site → Redirected to `/auth/login/`
2. New user clicks "Register" → Creates account → Auto-login → Redirected to payment
3. Existing user logs in → Checks payment status:
   - Has payment → Goes to homepage
   - No payment → Goes to payment page
4. Payment page → Click "Pay with eSewa" → eSewa integration → Success → Homepage

### 6. eSewa Configuration
```python
esewa_config = {
    'merchant_code': 'EPAYTEST',  # Sandbox merchant code
    'success_url': '/auth/payment/success/',
    'failure_url': '/auth/payment/failure/',
    'total_amount': '500',
}
```

### 7. Security Features
- CSRF protection on all forms
- Payment verification via transaction ID
- Middleware blocks unauthorized access
- Auto-logout redirects to login

### 8. Database Changes
- New `home_payment` table created
- Migration applied successfully
- Test user and payment created

## Usage Instructions

### For Development:
1. Use eSewa sandbox environment (uat.esewa.com.np)
2. Test with merchant code: `EPAYTEST`
3. Create test payments via admin or payment page

### For Production:
1. Change eSewa URL to production: `esewa.com.np/epay/main`
2. Update merchant code to your actual eSewa merchant ID
3. Configure proper success/failure URLs
4. Add SSL certificate for secure payments

## Files Modified/Created:
- `home/models.py` - Added Payment model
- `home/middleware.py` - Created payment middleware
- `home/views.py` - Added payment views
- `home/urls.py` - Added payment routes
- `Jetflix/urls.py` - Modified root routing
- `Jetflix/settings.py` - Added middleware
- `home/templates/home/payment.html` - Payment page
- `home/templates/home/payment_redirect.html` - eSewa redirect
- `home/migrations/0001_initial.py` - Payment model migration

The system is now fully functional with eSewa payment integration!