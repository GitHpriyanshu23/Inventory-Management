from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsepoint.settings')

app = Celery('pulsepoint')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# Namespace 'CELERY_' means all celery-related configs start with 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY_')

# Discover tasks in all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

app.conf.beat_schedule = {
    'check-low-stock-daily': {
        'task': 'inventory.tasks.check_low_stock',
        'schedule': crontab(hour=9, minute=0),  # Runs daily at 9:00 AM
    },
}