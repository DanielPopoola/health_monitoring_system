from celery import shared_task
from users.models import UserProfile
from .generators import(
    BloodPressureGenerator,
    DailyStepsGenerator,
    HeartRateGenerator,
    SleepDurationGenerator,
    SpO2Generator
)


@shared_task
def generate_blood_pressure_for_all_users():
    for user_profile in UserProfile.objects.all():
        BloodPressureGenerator(user_profile).generate()

@shared_task
def generate_heart_rate_for_all_users():
    for user_profile in UserProfile.objects.all():
        HeartRateGenerator(user_profile).generate()

@shared_task
def generate_spo2_for_all_users():
    for user_profile in UserProfile.objects.all():
        SpO2Generator(user_profile).generate()

@shared_task
def generate_daily_metrics_for_all_users():
    """Generate daily metrics like steps and sleep"""
    for user_profile in UserProfile.objects.all():
        DailyStepsGenerator(user_profile).generate()
        SleepDurationGenerator(user_profile).generate()