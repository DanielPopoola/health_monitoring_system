from django.db import models
from users.models import UserProfile

class SimulationConfig(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='simulation_config')
    heart_rate_mean = models.FloatField(default=75.0)
    heart_rate_variance = models.FloatField(default=5.0)
    systolic_mean = models.FloatField(default=120.0)
    systolic_variance = models.FloatField(default=10.0)
    diastolic_mean = models.FloatField(default=80.0)
    diastolic_variance = models.FloatField(default=5.0)
    spo2_mean = models.FloatField(default=97.0)
    spo2_variance = models.FloatField(default=1.0)
    steps_mean = models.IntegerField(default=8000)
    steps_variance = models.IntegerField(default=2000)
    sleep_mean = models.FloatField(default=7.5)
    sleep_variance = models.FloatField(default=1.0)

    # Auto-create config when a new user is created
    @classmethod
    def create_for_user(cls, user_profile):
        return cls.objects.create(user=user_profile)
    