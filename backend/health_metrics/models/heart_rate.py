from .base import HealthMetric
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Avg
from datetime import timedelta
import math

class HeartRate(HealthMetric):
    """
    This is a metric that measures user's heart rate - one of the concrete classes to be defined.
    It has 3 different states - resting, active, sleeping.
    """

    ACTIVITY_CHOICES = [
        ('resting', 'Resting'),
        ('active', 'Active'),
        ('sleeping', 'Sleeping')
    ]

    value = models.PositiveSmallIntegerField()
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)

    def clean(self):
        super().clean()
        if not (30 <= self.value <= 220):
            raise ValidationError("Heart rate must be between 30 and 220 BPM")
        
    def is_within_normal_range(self):
        return 60 <= self.value <= 100
    
    @property
    def heart_rate_zone(self):
        if self.value < 60:
            return 'Below Normal'
        elif self.value <= 100:
            return 'Normal'
        elif self.value <= 140:
            return 'Fat Burn'
        elif self.value <= 170:
            return 'Cardio'
        else:
            return 'Peak'

    @property
    def is_tachycardia(self):
        return self.value > 100
    
    @property
    def is_bradycardia(self):
        return self.value < 60
    
    def get_resting_average(self):
        return HeartRate.objects.filter(user=self.user, activity_level='resting').aggregate(avg=Avg('value'))['avg']
    
    def calculate_hrv(self, time_window=24):
        """
        Calculate heart rate variability using RMSSD method
        (Root Mean Square of Successive Differences)

        Args:
            time_window: Hours to look back for measurements, default 24 hours
            
        Returns:
            HRV value or None if insufficient data
        """
        # Get recent heart rate measurements in chronological order
        since = self.timestamp - timedelta(hours=time_window)
        measurements = HeartRate.objects.filter(
            user=self.user,
            timestamp__gte=since,
            timestamp__lte=self.timestamp
        ).order_by('timestamp').values_list('value', flat=True)

        # Need at least two measurements to calculate variability.
        if len(measurements) < 2:
            return None
        
        # Calculate successive differences
        successive_diffs = []
        for i in range(1, len(measurements)):
            diff = measurements[i] - measurements[i-1]
            successive_diffs.append(diff ** 2)

        if not successive_diffs:
            return None
        
        mean_squared_diff =  sum(successive_diffs) / len(successive_diffs)
        hrv = math.sqrt(mean_squared_diff)
        
        return round(hrv, 2)
    
    def compare_to_baseline(self, baseline_days=30, baseline_activity=None):
        """
        Compare current heart rate to user's baseline

        Args:
        baseline_days: Number of days to use for baseline calculation
        baseline_activity: If provided, only compare to this activity level

        Returns:
        Dictionary with difference from baseline and percent change
        """
        # Calculate baseline from historical data.
        query = HeartRate.objects.filter(
            user=self.user,
            timestamp__lt=self.timestamp,
            timestamp__gte=self.timestamp - timedelta(days=baseline_days)
        )

        # Filter by activity if specified.
        if baseline_activity:
            query = query.filter(activity_level=baseline_activity)
        else:
            #If comparing against all activities, prefer to compare against same activity
            same_activity = query.filter(activity_level=self.activity_level)
            if same_activity.exists():
                query = same_activity

        baseline = query.aggregate(avg=Avg('value'))['avg']

        if baseline is None:
            return None
        
        absolute_diff = self.value - baseline
        percent_change = (absolute_diff / baseline) * 100 if baseline else 0

        return{
            'baseline': round(baseline, 1),
            'current':  self.value,
            'difference': round(absolute_diff, 1),
            'percent_change': round(percent_change, 1),
            'is_elevated': absolute_diff > 0,
            'is_significant': abs(percent_change) > 10
        }