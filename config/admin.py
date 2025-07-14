from django.contrib import admin
from .models import (
    ServiceCategory, Device, ServiceOrder,
    OrderStatusHistory, Feedback, UserProfile
)

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "device_type", "brand", "model")
    list_filter = ("device_type",)
    search_fields = ("brand", "model")


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "device", "category", "status", "technician", "created_by", "created_at")
    list_filter = ("status", "category", "technician")
    search_fields = ("description",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "timestamp")
    list_filter = ("status", "timestamp")
    date_hierarchy = "timestamp"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "get_device", "get_user", "rating", "submitted_at")
    search_fields = ("comment",)
    date_hierarchy = "submitted_at"

    def get_device(self, obj):
        return obj.order.device
    get_device.short_description = "Device"

    def get_user(self, obj):
        return obj.order.created_by
    get_user.short_description = "User"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "role")
    list_filter = ("role",)
