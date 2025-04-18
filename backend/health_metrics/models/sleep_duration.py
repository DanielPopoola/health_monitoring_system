from .base import HealthMetric
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

class SleepDuration(HealthMetric):
    """
    This metric tracks a user's sleep duration between start and end times.
    """
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    quality = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Subjective sleep quality on a scale of 1-10"
    )
    interruptions = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Number of times sleep was interrupted."
    )

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Stop time must be after start time.")
        
        # Calculate duration in hours
        duration = (self.end_time - self.start_time).total_seconds() / 3600

        if duration > 16:
            raise ValidationError("Sleep duration exceeds reasonable limit (16 hours)")
        if duration < 1:
            raise ValidationError("Sleep duration is too short (< 1 hour)")
        
        # Check if sleep occured within the same 36 hour period.
        if (self.end_time - self.start_time).days > 1:
            raise ValidationError("Sleep start and end times must be within a 36-hour period")
        
        if self.quality is not None and not (1 <= self.quality <= 10):
            raise ValidationError("Sleep quality must be between 1 and 10.")
        
    def is_within_normal_range(self):
        return 7 <= self.duration <= 9
    
    @property
    def duration(self):
        """Returns sleep duration in hours."""
        delta = self.end_time - self.start_time
        return round(delta.total_seconds() / 3600, 2)
    
    @property
    def is_sufficient(self, age=None):
        """Determines if sleep duration meets recommended guidelines based on age."""
        min_sleep, max_sleep = 7, 9

        if age:
            if age < 1:
                min_sleep, max_sleep = 12,  16
            elif age < 3:
                min_sleep, max_sleep = 11, 14
            elif age < 6:
                min_sleep, max_sleep = 10, 13
            elif age < 13:
                min_sleep, max_sleep = 9, 11
            elif age < 18:
                min_sleep, max_sleep = 8, 10
            elif age > 65:
                min_sleep, max_sleep = 7, 8

        return min_sleep <= self.duration <= max_sleep
    
    @property
    def sleep_midpoint(self):
        """Calculate midpoint of sleep (for circadian analysis)."""
        midpoint_time = self.start_time + datetime.timedelta(hours=self.duration/2)
        return midpoint_time
    
    def get_weekly_average(self):
        pass

    def __str__(self):
        duration_str = f"{self.duration:.1f} hours" 
        return f"{self.user.get_full_name()} - {duration_str} @ {self.start_time.strftime('%Y-%m-%d')}"
            