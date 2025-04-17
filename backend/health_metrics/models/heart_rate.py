from .base import HealthMetric
from django.db import models
from django.core.exceptions import ValidationError


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
            raise ValidationError("Heart ")

