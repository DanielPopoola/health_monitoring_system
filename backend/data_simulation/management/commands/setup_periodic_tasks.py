from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule

class Command(BaseCommand):
    help = 'Setup periodic tasks for data simulation'

    def handle(self, *args, **options):
        # Create scheduls
        heart_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=60, # seconds
            period=IntervalSchedule.SECONDS,
        )

        bp_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=300, # 5 minutes
            period=IntervalSchedule.SECONDS,
        )

        sp_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=60,
            period=IntervalSchedule.SECONDS,
        )

        daily_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=24,
            period=IntervalSchedule.HOURS,
        )

        # Create tasks
        PeriodicTask.objects.get_or_create(
            interval=heart_schedule,
            name='Generate Heart Rate',
            task='data_simulation.tasks.generate_heart_rate_for_all_users',
        )

        PeriodicTask.objects.get_or_create(
            interval=bp_schedule,
            name='Generate Blood Pressure',
            task='data_simulation.tasks.generate_blood_pressure_for_all_users'
        )

        PeriodicTask.objects.get_or_create(
            interval=sp_schedule,
            name='Generate Oxygen Levels',
            task='data_simulation.tasks.generate_spo2_for_all_users',
        )

        PeriodicTask.objects.get_or_create(
            interval=daily_schedule,
            name='Generate Daily Metrics',
            task='data_simulation.tasks.generate_daily_metrics_for_all_users',
        )

        self.stdout.write(self.style.SUCCESS('Successfully set up periodic tasks'))