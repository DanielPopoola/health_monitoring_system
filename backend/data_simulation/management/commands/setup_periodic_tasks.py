from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule

class Command(BaseCommand):
    help = 'Setup periodic tasks for data simulation'

    def handle(self, *args, **options):
        # Clean up previously created tasks
        task_names = [
            'Generate Heart Rate',
            'Generate Blood Pressure',
            'Generate Oxygen Levels',
            'Generate Daily Metrics',
        ]
        PeriodicTask.objects.filter(name__in=task_names).delete()

        # Create schedules
        heart_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=60,
            period=IntervalSchedule.SECONDS,
        )

        bp_morning, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='6',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )

        bp_evening, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='18',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )

        sp_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=120,
            period=IntervalSchedule.SECONDS,
        )

        daily_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='9', 
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
        )

        # Recreate tasks
        PeriodicTask.objects.create(
            interval=heart_schedule,
            name='Generate Heart Rate',
            task='data_simulation.tasks.generate_heart_rate_for_only_users',
        )

        PeriodicTask.objects.create(
            crontab=bp_morning,
            name='Generate Blood Pressure (Morning)',
            task='data_simulation.tasks.generate_blood_pressure_for_only_users'
        )

        PeriodicTask.objects.create(
            crontab=bp_evening,
            name='Generate Blood Pressure (Evening)',
            task='data_simulation.tasks.generate_blood_pressure_for_only_users'
        )

        PeriodicTask.objects.create(
            interval=sp_schedule,
            name='Generate Oxygen Levels',
            task='data_simulation.tasks.generate_spo2_for_all_users',
        )

        PeriodicTask.objects.create(
            crontab=daily_schedule,
            name='Generate Daily Metrics',
            task='data_simulation.tasks.generate_daily_metrics_for_all_users',
        )

        self.stdout.write(self.style.SUCCESS('Successfully reset periodic tasks'))
