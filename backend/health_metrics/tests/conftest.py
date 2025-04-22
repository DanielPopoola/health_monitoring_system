import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta


User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(
        email="test@example.com",
        password="testpassword123",
        first_name="Test",
        last_name="User"
    )

@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@example.com",
        password="adminpassword123",
        first_name="Admin",
        last_name="User",
        is_staff=True
    )

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def blood_pressure_data():
    return {
        "systolic": 120,
        "diastolic": 80,
        "pulse": 72,
        "timestamp": timezone.now().isoformat(),
        "source": "manual"
    }

@pytest.fixture
def daily_steps_data():
    return {
        "count": 8000,
        "goal": 10000,
        "device": "WATCH",
        "distance": 6.2,
        "timestamp": timezone.now().isoformat(),
        "source": "device"
    }

@pytest.fixture
def heart_rate_data():
    return {
        "value": 75,
        "activity_level": "resting",
        "timestamp": timezone.now().isoformat(),
        "source": "device"
    }

@pytest.fixture
def sleep_duration_data():
    start_time = timezone.now() - timedelta(hours=8)
    end_time = timezone.now()
    return {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "quality": 8,
        "interruptions": 2,
        "timestamp": start_time.isoformat(),
        "source": "device"
    }

@pytest.fixture
def spo2_data():
    return {
        "value": 98,
        "measurement_method": "WEARABLE",
        "timestamp": timezone.now().isoformat(),
        "source": "device"
    }

    