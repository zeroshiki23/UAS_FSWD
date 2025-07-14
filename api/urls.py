from django.urls import path
from . import views
from .views import FeedbackCreateAPIView, FeedbackDetailAPIView

urlpatterns = [
    # Service Categories
    path('categories/', views.ServiceCategoryListCreateAPIView.as_view(), name='category-list'),

    # Devices
    path('devices/', views.DeviceListCreateAPIView.as_view(), name='device-list'),
    path('devices/<int:pk>/', views.DeviceDetailAPIView.as_view(), name='device-detail'),

    # Service Orders
    path('orders/', views.ServiceOrderListCreateAPIView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.ServiceOrderDetailAPIView.as_view(), name='order-detail'),

    # Order Status History
    path('status-history/', views.OrderStatusHistoryListAPIView.as_view(), name='status-history'),

    # Feedback
    path('feedback/', views.FeedbackCreateAPIView.as_view(), name='feedback-create'),
    path('feedback/<int:pk>/', views.FeedbackDetailAPIView.as_view(), name='feedback-detail'),
    path('feedbacks/', views.FeedbackDetailAPIView.as_view(), name='feedback-list'),
]
