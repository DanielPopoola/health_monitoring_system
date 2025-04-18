from .base import HealthMetric
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Avg


class DailySteps(HealthMetric):
    """
    This metric tracks the number of steps taken by a user in a day.
    """
    count = models.PositiveIntegerField()
    goal = models.PositiveIntegerField(default=10000)
    device = models.CharField(
        max_length=50,
        choices=[
            ('PHONE', 'Smartphone'),
            ('WATCH', 'Smart Watch'),
            ('PEDOMETER', 'Dedicated Pedometer'),
            ('OTHER', 'Other Device')
        ],
        default='OTHER'
    )
    distance = models.FloatField(null=True, blank=True, help_text="Distance in kilometers")

    def clean(self):
        if self.count > 100000:
            raise ValidationError("Step count exceeds reasonable daily limit (100,000)")
        
        if self.distance is not None:
            steps_per_km = self.count / self.distance if self.distance > 0 else 0
            if not(1000 <= steps_per_km <= 2000) and self.count > 1000:
                raise ValidationError("Step to distance ratio is unrealistic")
            
    def is_within_normal_range(self):
        return self.count >= 5000
    
    @property
    def goal_percentage(self):
        return round((self.count / self.goal) * 100, 1) if self.goal > 0 else 0
    
    @property
    def active_level(self):
        if self.count < 5000:
            return "Sedentary"
        elif self.count < 7500:
            return "Lightly Active"
        elif self.count < 12000:
            return "Active"
        else:
            return "Very Active"
        
    def get_weekly_average(self):
        """Calculate average steps per day over the last week."""
        end_date = self.timestamp.date()
        start_date = end_date - timezone.timedelta(days=6)

        return self.__class__.objects.filter(
            user=self.user,
            timestam__date__range=(start_date, end_date)
        ).aggregate(avg_steps=Avg('count'))['avg_steps'] or 0
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.count} steps on {self.timestamp.strftime('%Y-%m-%d')}"