from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Group

@receiver(post_save, sender=Group)
def group_created_handler(sender, instance, created, **kwargs):
    if created:
        Group.create_initial_schedule(instance)