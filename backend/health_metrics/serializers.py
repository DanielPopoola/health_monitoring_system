from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import BloodPressure, DailySteps, HeartRate, SleepDuration, SpO2


User = get_user_model()

class HealthMetricsSerializer(serializers.ModelSerializer):
    """Base serializer for all health metrics"""
    
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    class Meta:
        fields = ['id', 'user', 'full_name', 'timestamp', 'source', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_name', 'user']
        abstract = True


class BloodPressureSerializer(HealthMetricsSerializer):
    """Serializer for BloodPressure metrics"""

    bp_category = serializers.ReadOnlyField()
    pulse_pressure = serializers.ReadOnlyField()
    mean_arterial_pressure = serializers.ReadOnlyField()

    class Meta(HealthMetricsSerializer.Meta):
        model = BloodPressure
        fields = HealthMetricsSerializer.Meta.fields + [
            'systolic', 'diastolic', 'pulse',
            'bp_category', 'pulse_pressure', 'mean_arterial_pressure'
        ]

    def create(self, validated_data):
        return BloodPressure.objects.create(**validated_data)

class DailyStepsSerializer(HealthMetricsSerializer):
    """Serializer for DailySteps metrics"""

    goal_percentage = serializers.ReadOnlyField()
    active_level = serializers.ReadOnlyField()

    class Meta(HealthMetricsSerializer.Meta):
        model = DailySteps
        fields = HealthMetricsSerializer.Meta.fields + [
            'count', 'goal', 'device', 'distance',
            'goal_percentage', 'active_level'
        ]

    def create(self, validated_data):
        return DailySteps.objects.create(**validated_data)

class HeartRateSerializer(HealthMetricsSerializer):
    """Serializer for HeartRate metrics"""

    heart_rate_zone = serializers.ReadOnlyField()
    is_tachycardia = serializers.ReadOnlyField()
    is_bradycardia = serializers.ReadOnlyField()

    class Meta(HealthMetricsSerializer.Meta):
        model = HeartRate
        fields = HealthMetricsSerializer.Meta.fields + [
            'value', 'activity_level', 'heart_rate_zone',
            'is_tarchycardia', 'is_bardycardia'
        ]

    def create(self, validated_data):
        return HeartRate.objects.create(**validated_data)

class SleepDurationSerializer(HealthMetricsSerializer):
    """Serializer for SleepDuration metrics"""

    duration = serializers.ReadOnlyField()
    is_sufficient = serializers.ReadOnlyField()
    sleep_midpoint = serializers.ReadOnlyField()

    class Meta(HealthMetricsSerializer.Meta):
        model = SleepDuration
        fields = HealthMetricsSerializer.Meta.fields + [
            'start_time', 'end_time', 'quality', 'interruptions',
            'duration', 'is_sufficient', 'sleep_midpoint'
        ]

    def create(self, validated_data):
        return SleepDuration.objects.create(**validated_data)

class SpO2Serializer(HealthMetricsSerializer):
    """Serializer for SpO2 metrics"""
    
    is_normal = serializers.ReadOnlyField()
    severity = serializers.ReadOnlyField()
    
    class Meta(HealthMetricsSerializer.Meta):
        model = SpO2
        fields = HealthMetricsSerializer.Meta.fields + [
            'value', 'measurement_method', 'is_normal', 'severity'
        ]

    def create(self, validated_data):
        return SpO2.objects.create(**validated_data)