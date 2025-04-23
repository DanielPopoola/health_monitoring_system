from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile
from data_simulation.models import SimulationConfig

@receiver(post_save, sender=UserProfile)
def create_simulation_config(sender, instance, created, **kwargs):
    if created:
        SimulationConfig.create_for_user(user_profile=instance)