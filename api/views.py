from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from config.models import ServiceCategory, Device, ServiceOrder, OrderStatusHistory, Feedback
from .serializers import (
    ServiceCategorySerializer,
    DeviceSerializer,
    ServiceOrderSerializer,
    OrderStatusHistorySerializer,
    FeedbackSerializer
)


# 1. ServiceCategory API
class ServiceCategoryListCreateAPIView(APIView):
    def get(self, request):
        categories = ServiceCategory.objects.all()
        serializer = ServiceCategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ServiceCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2. Device API
class DeviceListCreateAPIView(APIView):
    def get(self, request):
        devices = Device.objects.all()
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=request.user)  # Auto-assign customer
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceDetailAPIView(APIView):
    def get(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        serializer = DeviceSerializer(device)
        return Response(serializer.data)

    def put(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        serializer = DeviceSerializer(device, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        device = get_object_or_404(Device, pk=pk)
        device.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceOrderListCreateAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = ServiceOrder.objects.all()
        serializer = ServiceOrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        device_id = data.get("device")

        if not device_id:
            return Response({"error": "Device wajib diisi."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return Response({"error": "Device tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)

        # 🔍 Debug info
        print("DEBUG - Device ID from request:", device_id)
        print("DEBUG - Logged in user ID:", request.user.id)
        print("DEBUG - Device.customer ID:", device.customer.id)
        print("DEBUG - User is authenticated:", request.user.is_authenticated)

        # Cek apakah device milik user yang login
        if device.customer != request.user:
            return Response(
                {"error": "Anda tidak memiliki hak atas device ini."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ServiceOrderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ServiceOrderDetailAPIView(APIView):
    def get(self, request, pk):
        order = get_object_or_404(ServiceOrder, pk=pk)
        serializer = ServiceOrderSerializer(order)
        return Response(serializer.data)

    def put(self, request, pk):
        order = get_object_or_404(ServiceOrder, pk=pk)
        serializer = ServiceOrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 4. OrderStatusHistory API
class OrderStatusHistoryListAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        history = OrderStatusHistory.objects.all()
        serializer = OrderStatusHistorySerializer(history, many=True)
        return Response(serializer.data)


# 5. Feedback API
class FeedbackCreateAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order")
        if not order_id:
            return Response({"error": "Order tidak ditemukan."}, status=status.HTTP_400_BAD_REQUEST)

        # Validasi order milik user
        try:
            order = ServiceOrder.objects.get(id=order_id, created_by=request.user)
        except ServiceOrder.DoesNotExist:
            return Response({"error": "Order tidak ditemukan atau bukan milik Anda."}, status=status.HTTP_403_FORBIDDEN)

        # Cek jika sudah ada feedback sebelumnya
        if hasattr(order, "feedback"):
            return Response({"error": "Feedback untuk pesanan ini sudah dikirim."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = FeedbackSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FeedbackDetailAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        feedbacks = Feedback.objects.all()
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)

