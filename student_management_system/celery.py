from celery import Celery
from celery.schedules import crontab
from student_management_system import settings

app = Celery('student_management_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'delete-empty-groups-every-day': {
        'task': 'student_management_app.tasks.delete_empty_groups',
        'schedule': crontab(hour=0, minute=0),  # Runs every day at midnight
    },
}
