from .base import HealthMetric
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class SpO2(HealthMetric):
    """
    This metric measures blood oxygen saturation levels.
    """
    value = models.PositiveSmallIntegerField() # Percentage of oxygen saturation
    measurement_method = models.CharField(
        max_length=50, 
        choices=[
            ('FINGERTIP', 'Fingertip Pulse Oximeter'),
            ('MEDICAL', 'Medical-Grade Device'),
            ('WEARABLE', 'Wearable Device'),
            ('OTHER', 'Other')
        ],
        default='OTHER'
    )

    def clean(self):
        if not (70 <= self.value <= 100):
            raise ValidationError("SpO2 value must be between 70%\ and 100%")
        
    def is_within_normal_range(self):
        return self.value >= 95
    
    @property
    def is_normal(self):
        return self.value >= 95
    
    @property
    def severity(self):
        if self.value >= 95:
            return "Normal"
        elif 90 <= self.value < 95:
            return "Mild Hypoxemia"
        elif 80 <= self.value < 90:
            return "Moderate Hypoxemia"
        else:
            return "Severe Hypoxemia"
        
    def get_lowest_reading(self, days=7):
        """Find lowest SpO2 reading in the specified period."""
        return self.__class__.objects.filter(
            user=self.user,
            timestamp__gte=timezone.now() - timezone.timedelta(days=days)
        ).order_by('value').first()
    
    def alert_required(self):
        """Determine if this reading requires medical attention."""
        return self.value < 90
    
    def __str__(self):
        return f"{self.user.get_full_name()} - SpO2: {self.value}% @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
