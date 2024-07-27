from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from student_management_app.models import Group

@shared_task
def delete_empty_groups():
    threshold_date = timezone.now() - timedelta(days=4)
    empty_groups = Group.objects.filter(students__isnull=True, created_at__lte=threshold_date)
    empty_groups.delete()
