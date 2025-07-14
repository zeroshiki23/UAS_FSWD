from rest_framework import serializers
from config.models import (
    Device, ServiceCategory, ServiceOrder,
    OrderStatusHistory, Feedback
)


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Device
        fields = '__all__'


class ServiceOrderSerializer(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)
    category = ServiceCategorySerializer(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)  # ✅ Ini penting

    class Meta:
        model = ServiceOrder
        fields = '__all__'


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
