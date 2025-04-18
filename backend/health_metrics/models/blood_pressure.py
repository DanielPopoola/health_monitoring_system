from .base import HealthMetric
from django.db import models
from django.db.models import Avg, Q
from django.core.exceptions import ValidationError
from django.utils import timezone


class BloodPressure(HealthMetric):
    """
    This a metric that measures user's blood pressure.
    """

    systolic = models.PositiveSmallIntegerField()
    diastolic = models.PositiveSmallIntegerField()
    pulse = models.PositiveSmallIntegerField(null=True, blank=True)


    def clean(self):
        if self.systolic <= self.diastolic:
            raise ValidationError("Systolic pressure must be greater than diastolic pressure.")
        if not (70 <= self.systolic <= 220):
            raise ValidationError("Systolic pressure out of expected range (70 - 220)")
        if not (40 <= self.diastolic <= 130):
            raise ValidationError("Diastolic pressure out of expected range (40 - 130)")
        if self.pulse is not None and not (40 <= self.pulse <= 200):
            raise ValidationError("Pulse must be between 40 and 200 if provided.")
        
    def is_within_normal_range(self):
        return self.systolic < 120 and self.diastolic < 80
    
    @property
    def bp_category(self):
        if self.systolic < 120 and self.diastolic < 80:
            return "Normal"
        elif 120 <= self.systolic < 130 and self.diastolic < 80:
            return "Elevated"
        elif 130 <= self.systolic < 140 or 80 <= self.diastolic < 90:
            return "Hypertension Stage 1"
        elif 140 <= self.systolic or 90 <= self.diastolic:
            return "Hypertension Stage 2"
        else:
            return "Unclassified"
        
    @property
    def pulse_pressure(self):
        return self.systolic - self.diastolic
    
    @property
    def mean_arterial_pressure(self):
        return round((self.systolic + (2 * self.diastolic))/3, 1)
    
    def get_average_by_time_of_day(self, days=30):
        """Analyze patterns in morning and evening readings."""
        recent_data = self.__class__.objects.filter(
            user=self.user,
            timestamp__gte=timezone.now() - timezone.timedelta(days=days)
        )

        morning = recent_data.filter(timestamp__hour__lt=12).aggregate(
            avg_systolic=Avg('systolic'),
            avg_diastolic=Avg('diastolic')
        )

        evening = recent_data.filter(timestamp__hour__gte=12).aggregate(
            avg_systolic=Avg('systolic'),
            avg_diastolic=Avg('diastolic')
        )

        return {'morning': morning, 'evening': evening}
    

    def is_consistently_elevated(self, days=7):
        recent = self.__class__.objects.filter(
            user=self.user,
            timestamp__gte=timezone.now() - timezone.timedelta(days=days)
        )

        elevated_readings = recent.filter(
            Q(systolic__gte=130) | Q(diastolic__gte=80)
        )

        return elevated_readings.count() >= (0.6 * recent.count()) if recent.exists() else False

    def compared_to_recommended_range(self, user_age):
        if user_age < 60:
            return self.systolic <= 120 and self.diastolic <= 80
        else:
            return self.systolic <= 140 and self.diastolic <= 90

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.systolic}/{self.diastolic} mmHg @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"        
