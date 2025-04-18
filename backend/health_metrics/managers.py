from django.db import models
from django.utils import timezone
from django.db.models import Avg, StdDev
from datetime import timedelta


class HealthMetricsManager(models.Manager):
    """
    Model manager for querying objects
    
    """
    def for_user(self, user):
        """Filter metrics for a specific user."""
        return self.filter(user=user)
    
    def in_date_range(self, start_date, end_date):
        """Get metrics within date range."""
        return self.filter(timestamp__range=(start_date, end_date))
    
    def latest_for_user(self, user, count=1):
        """Get latest user metrics."""
        return self.for_user(user).order_by('-timestamp')[:count]
    
    def daily_average(self, user, days=30):
        """Get daily averages over a period."""
        since = timezone.now() - timedelta(days=days)
        return self.for_user(user).filter(timestamp__gte=since).extra(
            {'day': "date(timestamp)"}
        ).values('day').annotate(avg_value=Avg('value'))
    
    def get_outliers(self, user, std_devs=2):
        """Get measurements outside normal distribution."""
        metrics = self.for_user(user)
        avg = metrics.aaggregate(avg=Avg('value'))['avg']
        stddev = metrics.aaggregate(stddev=StdDev('value'))['stddev']
        return metrics.filter(value__gt=avg + std_devs * stddev | \
                               metrics.filter(value__lt=avg - std_devs * stddev))