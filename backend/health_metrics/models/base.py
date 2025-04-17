from managers import HealthMetricsManager
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Avg, Max, Min, StdDev
from datetime import timedelta

User = get_user_model()

class HealthMetric(models.Model):
    """
    Abstract Base Class for various metrics
    
    """
    SOURCE_CHOICES  = [
        ('manual', 'Manual'),
        ('device', 'Device'),
        ('simulated', 'Simulated')
    ]

    # Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = HealthMetricsManager()

    # Meta Options
    class Meta:
        abstract = True
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp'])
        ]
    
    # Abstract methods  
    def clean(self):
        if not self.timestamp:
            raise ValidationError("Timestamp is required")
        
    def is_within_normal_range(self):
        raise NotImplementedError("Subclasses must implement this method.")
    
    # Concrete methods
    def get_trend(self, days=7):
        since = timezone.now() - timedelta(days=days)
        return self.__class__.objects.for_user(self.user).filter(
            timestamp__gte=since).values('timestamp', 'value'
        )
    
    def get_time_series_data(self, start_date, end_date):
        return self.__class__.objects.for_user(self.user).in_date_range(start_date, end_date).\
        values('timestamp', 'value')
    
    def as_dict(self):
        return {
            'user': self.user.id,
            'timestamp': self.timestamp,
            'source': self.source,
            'value': getattr(self, 'value', None)
        }
