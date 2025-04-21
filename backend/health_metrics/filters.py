import django_filters
from django.utils import timezone
from django.db import models
from datetime import timedelta
from .models import BloodPressure, DailySteps, HeartRate, SleepDuration, SpO2

class DateRangeFilterSet(django_filters.FilterSet):
    """Filter set that adds date filtering capabilities"""
    # Allows filtering by date range
    start_date = django_filters.DateFilter(field_name='timestamp', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='timestamp', lookup_expr='lte')

    # Allows filtering by last X days
    last_days = django_filters.NumberFilter(method='filter_last_days')

    def filter_last_days(self, queryset, name, value):
        """Filter for the last X days"""
        if value:
            start_date = timezone.now() - timedelta(days=int(value))
            return queryset.filter(timestamp__gte=start_date)
        return queryset
    
class BloodPressureFilterSet(DateRangeFilterSet):
    """Custom filters for BloodPressure"""
    systolic_min = django_filters.NumberFilter(field_name='systolic', lookup_expr='gte')
    systolic_max = django_filters.NumberFilter(field_name='systolic', lookup_expr='lte')
    diastolic_min = django_filters.NumberFilter(field_name='diastolic', lookup_expr='gte')
    diastolic_max = django_filters.NumberFilter(field_name='diastolic', lookup_expr='lte')

    class Meta:
        model = BloodPressure
        fields = ['source', 'timestamp', 'systolic', 'diastolic', 'pulse']


class DailyStepsFilterSet(DateRangeFilterSet):
    """Custom filters for DailySteps"""
    count_min = django_filters.NumberFilter(field_name='count', lookup_expr='gte')
    count_max = django_filters.NumberFilter(field_name='count', lookup_expr='lte')

    class Meta:
        model = DailySteps
        fields = ['source', 'timestamp', 'device', 'count']

class HeartRateFilterSet(DateRangeFilterSet):
    """Custom filters for HeartRate"""
    value_min = django_filters.NumberFilter(field_name='value', lookup_expr='gte')
    value_max = django_filters.NumberFilter(field_name='value', lookup_expr='lte')

    class Meta:
        model = HeartRate
        fields = ['source', 'timestamp', 'activity_level','value']

class SleepDurationFilterSet(DateRangeFilterSet):
    duration_min = django_filters.NumberFilter(method='filter_duration_min')
    duration_max = django_filters.NumberFilter(method='filter_duration_max')
    quality_min = django_filters.NumberFilter(field_name='quality', lookup_expr='gte')

    def filter_duration_min(self, queryset, name, value):
        """Filter for minimum sleep duration in hours"""
        # Convert hours to datetime diff in seconds
        seconds = float(value) * 3600
        return queryset.filter(end_time__gt=models.F('start_time') + timedelta(seconds=seconds))
    
    def filter_duration_max(self, queryset, name, value):
        """Filter for maximum sleep duration in hours"""
        seconds = float(value) * 3600
        return queryset.filter(end_time__lt=models.F('start_time') + timedelta(seconds=seconds))
    
    class Meta:
        model = SleepDuration
        fields = ['source', 'timestamp', 'start_time', 'end_time', 'quality', 'interruptions']


class SpO2FilterSet(DateRangeFilterSet):
    """Custom filters for SpO2"""
    value_min = django_filters.NumberFilter(field_name='value', lookup_expr='gte')
    value_max = django_filters.NumberFilter(field_name='value', lookup_expr='lte')
    
    class Meta:
        model = SpO2
        fields = ['source', 'timestamp', 'measurement_method', 'value']
    
