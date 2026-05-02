from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create_account/', views.create_account, name='create_account'),
    path('setpin/<int:acc_no>/', views.set_pin, name='setpin'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('deposit/', views.deposit, name='deposit'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('logout/', views.logout_view, name='logout'),
    path('reset_pin/', views.reset_pin, name='reset_pin'),
    path('transfer/', views.transfer, name='transfer'),
    path('transactions/', views.transaction_history, name='transaction_history'),
]
