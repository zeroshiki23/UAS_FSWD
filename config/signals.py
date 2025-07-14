# config/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ServiceOrder, OrderStatusHistory

@receiver(pre_save, sender=ServiceOrder)
def log_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  # Jika objek baru, tidak catat histori status

    try:
        old_instance = ServiceOrder.objects.get(pk=instance.pk)
    except ServiceOrder.DoesNotExist:
        return

    if old_instance.status != instance.status:
        OrderStatusHistory.objects.create(
            order=instance,
            status=instance.status
        )
