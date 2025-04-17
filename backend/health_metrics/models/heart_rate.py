from .base import HealthMetric
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Avg


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
    def is_tarchycardia(self):
        return self.value > 100
    
    @property
    def is_bardycardia(self):
        return self.value < 60
    
    def get_resting_average(self):
        return HeartRate.objects.filter(user=self.user, activity_level='resting').aaggregate(avg=Avg('value'))['avg']