from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),  # Home page = Login page
    path('register/', views.register_view, name='register'),          
    path('logout/', views.logout_view, name='logout'),
    path('payment/', views.payment_view, name='payment'),
    path('payment/success/', views.payment_success_view, name='payment_success'),
    path('payment/failure/', views.payment_failure_view, name='payment_failure'),
    path('dashboard/', views.home_page, name='home'),  # Movies dashboard
    path('search/', views.search_view, name='search'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('profile/', views.profile_view, name='profile'),
    path('watch_history/', views.watch_history_view, name='watch_history'),
    path('edit_profile/', views.edit_profile_view, name='edit_profile'),
    path('verify-payment/<str:transaction_uuid>/', views.verify_payment_status, name='verify_payment'),
]