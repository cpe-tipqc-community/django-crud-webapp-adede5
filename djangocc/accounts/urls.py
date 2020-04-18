from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('user/<str:pk>/', views.user_page, name="user_page"),
    path('account/<str:pk>/', views.account_settings, name="account"),

    path('login/', views.login_page, name="login"),
    path('register/', views.register_page, name="register"),
    path('logout/', views.logout_user, name="logout"),

    path('products/', views.products, name="products"),
    path('customer/<str:pk_test>/', views.customer, name="customer"),
    path('create_order/<str:pk>/', views.create_order, name="create_order"),
    path('update_order/<str:pk>/', views.update_order, name="update_order"),
    path('delete_order/<str:pk>/', views.delete_order, name="delete_order"),

    path('customer_create_order/<str:pk>/', views.customer_create_order, name="customer_create_order"),

    path('view_report/', views.view_order_report, name='view_order_report'),
    path('print_report/', views.print_order_report, name='print_order_report'),
]
