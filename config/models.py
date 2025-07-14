from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
# from .device import Device
# from .servicecategory import ServiceCategory

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('technician', 'Technician'),
        ('customer', 'Customer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

# 1. ServiceCategory
class ServiceCategory(models.Model):
    name = models.CharField(max_length=50)  # e.g., Repair, Maintenance, etc.

    def __str__(self):
        return self.name


# 2. Device
class Device(models.Model):
    DEVICE_TYPES = (
        ('Laptop', 'Laptop'),
        ('Smartphone', 'Smartphone'),
    )

    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)

    def __str__(self):
        return f"{self.device_type} - {self.brand} {self.model}"


# 3. ServiceOrder (core of the system)

class ServiceOrder(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Finished', 'Finished'),
        ('Cancelled', 'Cancelled'),
    )

    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_orders'
    )

    created_by = models.ForeignKey(
    User,
    on_delete=models.CASCADE,
    related_name='user_orders',
    null=True,  
    blank=True
)


    def __str__(self):
        return f"Order #{self.id} - {self.device} - {self.status}"


# 4. OrderStatusHistory (status log/timeline)
class OrderStatusHistory(models.Model):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order.id} → {self.status} at {self.timestamp}"


# 5. Feedback (after order is completed)
class Feedback(models.Model):
    order = models.OneToOneField(ServiceOrder, on_delete=models.CASCADE)
    rating = models.IntegerField()  # usually 1–5
    comment = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for Order #{self.order.id} – Rating: {self.rating}"
    
@receiver(pre_save, sender=ServiceOrder)
def log_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # jika belum disimpan di DB, berarti ini adalah data baru

    try:
        old_instance = ServiceOrder.objects.get(pk=instance.pk)
    except ServiceOrder.DoesNotExist:
        return

    # Jika status berubah, simpan ke OrderStatusHistory
    if old_instance.status != instance.status:
        OrderStatusHistory.objects.create(
            order=instance,
            status=instance.status
        )
