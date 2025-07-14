from django.urls import path
from . import views
from . import views as frontend_views


urlpatterns = [
    path('', views.home_page, name='home'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # USER AREA
    path('user/dashboard/', views.user_dashboard, name='dashboard_user'),
    path('user/order/', views.order_form, name='order_form'),
    path('user/orders/', views.user_orders, name='user_orders'),
    path('user/order/detail/<int:order_id>/', views.user_order_detail, name='user_order_detail'),
    path('user/order/history/<int:order_id>/', views.user_order_history, name='user_order_history'),
    path('user/feedback/', views.user_feedback_form, name='user_feedback_form'),
    path('user/feedbacks/', views.user_feedback_list, name='user_feedback_list'),

    # Tambahan ADMIN AREA
    path('admin/dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/orders/', views.admin_orders_list, name='admin-orders'), 
    path('admin/orders/<int:order_id>/', views.admin_order_detail, name='admin-order-detail'),
    path('admin/technicians/', views.admin_technician_list, name='admin-technician'),
    path('admin/feedbacks/', views.admin_feedback_list, name='admin-feedback-list'),

    path('user/orders/status/<str:status>/', views.user_orders_by_status, name='user_orders_by_status'),
]
