import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from datetime import timedelta


@pytest.mark.django_db
class TestPermissions:

    def test_admin_can_see_other_users_data(self, admin_client, user, blood_pressure_data):
        """Test that admin can see other users' data using user_id query param"""
        # First create blood pressure data for the regular user
        url = reverse('bloodpressure-list')

        # Create data for specific user
        from django.db import models
        from ..models import BloodPressure

        bp = BloodPressure.objects.create(
            user=user,
            systolic=blood_pressure_data['systolic'],
            diastolic=blood_pressure_data['diastolic'],
            pulse=blood_pressure_data['pulse'],
            timestamp=timezone.now(),
            source=blood_pressure_data['source']
        )

        # Admin tries to access it with user_id parameter
        response = admin_client.get(f"{url}?user_id={user.id}")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_user_cannot_see_other_users_data(self, authenticated_client, admin_user, blood_pressure_data):
        """Test that regular user cannot see other users' data even with user_id query param"""
        # First create blood pressure data for the admin user
        from ..models import BloodPressure

        bp = BloodPressure.objects.create(
            user=admin_user,
            systolic=blood_pressure_data['systolic'],
            diastolic=blood_pressure_data['diastolic'],
            pulse=blood_pressure_data['pulse'],
            timestamp=timezone.now(),
            source=blood_pressure_data['source']
        )

        # Regular user tries to access it with user_id parameter
        url = reverse('bloodpressure-list')
        response = authenticated_client.get(f"{url}?user_id={admin_user.id}")

        # User should only see their own data (which is none)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 0
