import numpy as np
import random
from datetime import timedelta, datetime, time
from django.utils import timezone
from health_metrics.models import BloodPressure, DailySteps, HeartRate, SleepDuration, SpO2
from users.models import UserProfile
from .models import SimulationConfig


class BaseGenerator:
    def __init__(self, user_profile, simulation_config=None):
        self.user_profile = user_profile
        self.simulation_config = simulation_config  or user_profile.simulation_config
        self.now = timezone.now()

    def generate_value(self, mean, variance):
        """Generate a random value based on normal distribution"""
        return np.random.normal(mean, variance)
    
class BloodPressureGenerator(BaseGenerator):
    def generate(self):
        systolic = self.generate_value(
            self.simulation_config.systolic_mean,
            self.simulation_config.systolic_variance
        )
        diastolic = self.generate_value(
            self.simulation_config.diastolic_mean,
            self.simulation_config.diastolic_variance
        )
        pulse = self.generate_value(
            self.simulation_config.pulse_mean,
            self.simulation_config.pulse_variance
        )

        systolic = max(90, min(180, round(systolic)))
        diastolic = max(60, min(systolic - 10, round(diastolic)))
        pulse = max(40, min(100, pulse))

        return BloodPressure.objects.create(
            user=self.user_profile,
            systolic=systolic,
            diastolic=diastolic,
            pulse=pulse,
            timestamp=self.now,
            source='simulated'
        )


class DailyStepsGenerator(BaseGenerator):
    def generate(self):
        count = self.generate_value(
            self.simulation_config.steps_mean,
            self.simulation_config.steps_variance
        )
        goal = self.generate_value(
            self.simulation_config.steps_mean,
            self.simulation_config.steps_variance
        )

        count = max(1000, min(25000, count))
        goal = max(10000, min(50000, goal))

        steps_per_km = random.randint(1000, 2000)
        distance = round(count / steps_per_km, 2) # km

        return DailySteps.objects.create(
            user=self.user_profile,
            count=count,
            goal=goal,
            distance=distance,
            timestamp=self.now,
            source='simulated',
            device='other'
        )


class HeartRateGenerator(BaseGenerator):
    def generate(self):
        value = self.generate_value(
            self.simulation_config.heart_rate_mean,
            self.simulation_config.heart_rate_variance
        )

        hour = self.now.hour
        if hour < 6 or hour > 22:
            activity_level = 'sleeping'
            value *= 0.9
        elif 6 <= hour < 9 or 17 <= hour < 22:
            activity_level = 'resting'
            value *= 1.05
        elif 9 <= hour < 17:
            activity_level = 'active'
            value *= 1.1

        return HeartRate.objects.create(
            user=self.user_profile,
            value=max(40, min(180, round(value))),
            activity_level=activity_level,
            timestamp=self.now,
            source='simulated'
        )


class SleepDurationGenerator(BaseGenerator):
    def generate(self):
        # 1. Generate a bedtime between 9 PM and 1 AM
        bedtime_hour = random.randint(21, 24) if random.random() < 0.7 else random.randint(0, 1)
        bedtime_minute = random.choice([0, 15, 30, 45])
        bedtime = timezone.now().replace(
            hour=bedtime_hour % 24,
            minute=bedtime_minute,
            second=0,
            microsecond=0,
        ) - timedelta(days=1) # simulate last night's sleep

        # Generate a duration
        sleep_duration_hours = self.generate_value(
            self.simulation_config.sleep_mean,
            self.simulation_config.sleep_variance
        )
        sleep_duration_hours = max(3.0, min(14.0, sleep_duration_hours))
        end_time = bedtime + timedelta(hours=sleep_duration_hours)

        quality = random.randint(1, 10) 
        interruptions = random.randint(0, 3)

        return SleepDuration.objects.create(
            user=self.user_profile,
            start_time=bedtime,
            end_time=end_time,
            timestamp=bedtime,
            quality=quality,
            interruptions=interruptions,
            source='simulated'
        )
    

class SpO2Generator(BaseGenerator):
    def generate(self):
        value = self.generate_value(
            self.simulation_config.spo2_mean,
            self.simulation_config.spo2_variance
        )

        value =  max(70, min(100, round(value)))

        return SpO2.objects.create(
            user=self.user_profile,
            value=value,
            measurement_method='OTHER',
            timestamp=self.now,
            source='simulated'
        )