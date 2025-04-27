from rest_framework import viewsets, filters, permissions, status
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import TruncHour, TruncDay
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db import models
from django.db.models import Avg, Min, Max
from datetime import timedelta  
from .models import BloodPressure, DailySteps, HeartRate, SleepDuration, SpO2
from .serializers  import (
    BloodPressureSerializer,
    DailyStepsSerializer,
    HeartRateSerializer,
    SleepDurationSerializer,
    SpO2Serializer
)
from .filters import(
    BloodPressureFilterSet,
    DailyStepsFilterSet, 
    HeartRateFilterSet,
    SleepDurationFilterSet, 
    SpO2FilterSet
)
# Create your views here.
class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for all viewsets"""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 100

class BaseHealthMetricsViewSet(viewsets.ModelViewSet):
    """Base viewset for all health metrics"""
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['timestamp', 'created_at', 'updated_at']
    ordering = ['-timestamp']

    def get_queryset(self):
        """
        Restricts the returned metrics to the authenticated user,
        unless the user is staff and a user_id parameter is provided
        """
        user = self.request.user
        queryset = self.queryset

        # If the request user is staff and a user_id is provided, filter by that user
        if user.is_staff and 'user_id' in self.request.query_params:
            user_id = self.request.query_params.get('user_id')
            return queryset.filter(user_id=user_id)
        
        return queryset.filter(user=user)
    
    def perform_create(self, serializer):
        """Automatically set the user to the current authenticated user"""
        serializer.save(user=self.request.user)

class BloodPressureViewSet(BaseHealthMetricsViewSet):
    """ViewSet for BloodPressure metrics"""
    queryset = BloodPressure.objects.all()
    serializer_class = BloodPressureSerializer
    filterset_class = BloodPressureFilterSet
    search_fields = ['source']

    @action(detail=False, methods=['get'])
    def time_of_day_analysis(self, request):
        """
        Analyze blood pressure patterns by time of day (morning vs evening).
        
        Query Parameters:
        - days: Number of days to analyze (default: 30)
        
        Returns:
        - Morning and evening averages for systolic and diastolic readings
        """
        try:
            days = int(request.query_params.get('days', 30))
            if days <= 0:
                return Response(
                    {"error": "Days parameter must be positive"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Days parameter must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No blood pressure readings found for analysis"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latest_bp = queryset.latest('timestamp')

        time_of_day_data = latest_bp.get_average_by_time_of_day(days=days)
        
        # Enhance the response with additional context
        response_data = {
            "analysis_period": {
                "days": days,
                "start_date": (timezone.now() - timedelta(days=days)).date().isoformat(),
                "end_date": timezone.now().date().isoformat(),
            },
            "morning_averages": time_of_day_data['morning'],
            "evening_averages": time_of_day_data['evening'],
            "reading_count": queryset.filter(
                timestamp__gte=timezone.now() - timedelta(days=days)
            ).count()
        }

        if (time_of_day_data['morning'].get('avg_systolic') and
            time_of_day_data['evening'].get('avg_systolic')):

            morning_sys = time_of_day_data['morning']['avg_systolic']
            evening_sys = time_of_day_data['evening']['avg_systolic']

            sys_diff = abs(morning_sys - evening_sys)

            # Add interpretation based on the difference
            if sys_diff >= 10:
                if morning_sys > evening_sys:
                    pattern = "morning-dominant"
                    description = "Blood pressure is significantly higher in the morning"
                else:
                    pattern = "evening-dominant"
                    description = "Blood pressure is significantly higher in the evening"
            else:
                pattern = "consistent"
                description = "Blood pressure is relatively consistent throughout the day"

            response_data["pattern"] = {
                "type": pattern,
                "description": description,
                "systolic_difference": round(sys_diff, 1)
            }

            return Response(response_data)
        
    @action(detail=False, methods=['get'])
    def elevation_check(self, request):
        """
        Checks whether blood pressure is consistently elevated.

        Query Parameters:
        - days: Number of days to analyze (default: 7)

        Returns:
        - True or False if blood pressure is consistenly elevated.

        """
        try:
            days = int(request.query_params.get('days', 7))
            if days <= 0:
                return Response(
                    {"error": "Days parameter must be positive"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Days parameter must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No blood pressure readings found for analysis"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latest_bp = queryset.latest('timestamp')

        constantly_elevated = latest_bp.is_consistently_elevated(days=days)

        return Response({
            "is_consistently_elevated": constantly_elevated,
            "days_checked": days,
            })
    
    @action(detail=False, methods=['get'])
    def age_comparison(self, request):
        """
        Compares latest reading to age appropriate recommendations

        Query Parameters:
        - age: User's age in years(required)

        Returns:
        - Latest blood pressure reading
        - Recommedation status based on age
        - Age-appropriate references
        """
        if 'age' not in request.query_params:
            return Response(
                {"error": "Age parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            age = int(request.query_params.get('age', 30))
            if age <= 0 or age >= 120:
                return Response(
                    {"error": "Age must be between 1 and 120"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Age parameter must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No blood pressure readings found."},
                status=status.HTTP_404_NOT_FOUND
            )

        latest_bp = queryset.latest('timestamp')
        
        is_within_range = latest_bp.compared_to_recommended_range(age)

        if age < 60:
            recommended_systolic = "<= 120"
            recommended_diastolic = "<= 80"
        else:
            recommended_systolic = "<= 140"
            recommended_diastolic = "<= 90"

        response_data = {
            "latest_reading": {
                "systolic": latest_bp.systolic,
                "diastolic": latest_bp.diastolic,
                "timestamp": latest_bp.timestamp.isoformat(),
                "category": latest_bp.bp_category
            },
            "age_specific_assessment":{
                "age": age,
                "within_recommended_range": is_within_range,
                "recommended_ranges":{
                    "systolic": recommended_systolic,
                    "diastolic": recommended_diastolic
                }
            },
            "recommendation": get_recommendation_message(latest_bp, age, is_within_range)
        }

        return Response(response_data)
    
def get_recommendation_message(bp_reading, age, is_within_range):
    """Helper function to generate appropriate recommendation message"""
    if is_within_range:
        return "Your blood pressure is within the recommended range for your age group."
    
    messages = []

    # Check if systolic is out of range
    if age < 60 and bp_reading.systolic > 120:
        messages.append(f"Your systolic pressure ({bp_reading.systolic}) is above the recommended level (120) for your age.")
    elif age >= 60 and bp_reading.systolic > 140:
        messages.append(f"Your systolic pressure ({bp_reading.systolic}) is above the recommended level (140) for your age.")

    # Check if diastolic is out of range
    if age < 60 and bp_reading.diastolic > 80:
        messages.append(f"Your diastolic pressure ({bp_reading.diastolic} is above the recommended level (80) for your age.")
    elif age >= 60 and bp_reading.diastolic > 90:
        messages.append(f"Your diastolic pressure ({bp_reading.diastolic} is above the recommended level (90) for your age.")

    if messages:
        advice = "Consider consulting with a healthcare provider about these readings."
        return " ".join(messages) + " " + advice
    
    return "Your blood pressure readings require attention based on your age group."


class DailyStepsViewSet(BaseHealthMetricsViewSet):
    """ViewSet for DailySteps metrics"""
    queryset = DailySteps.objects.all()
    serializer_class = DailyStepsSerializer
    filterset_class = DailyStepsFilterSet
    search_fields = ['source', 'device']

    @action(detail=False, methods=['get'])
    def weekly_average(self, request):
        """
        Get average number of steps per day over the past week.

        Returns:
        - Average steps per day for the last 7 days.
        - Date range for the calculation
        - Number of days with recorded data.
        """
        queryset = self.get_queryset()
        
        if not queryset.exists():
            return Response(
                {"error": "No step data found for analysis"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latest_steps = queryset.latest('timestamp')

        weekly_avg = latest_steps.weekly_average()

        end_date = latest_steps.timestamp.date()
        start_date = end_date - timezone.timedelta(days=6)

        days_with_data = queryset.filter(
            timestamp__date__range=(start_date, end_date)
        ).dates('timestamp', 'day').count()

        response_data = {
            "weekly_average": weekly_avg,
            "date_range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "days_with_data": days_with_data,
            "data_completeness": round((days_with_data / 7) * 100, 1)
        }

        # Add comparison to goal
        latest_goal = latest_steps.goal
        if weekly_avg and latest_goal:
            goal_percentage = (weekly_avg / latest_goal) * 100
            response_data["goal_metrics"] = {
                "current_goal": latest_goal,
                "average_percentage": round(goal_percentage, 1),
                "meeting_goal": goal_percentage >= 100
            }

        return Response(response_data)

        
class HeartRateViewSet(BaseHealthMetricsViewSet):
    """ViewSet for HeartRate metrics"""
    queryset = HeartRate.objects.all()
    serializer_class = HeartRateSerializer
    filterset_class = HeartRateFilterSet
    search_fields = ['source', 'activity_level']

    @action(detail=False, methods=['get'])
    def resting_average(self, request):
        """
        Returns the average heart rate at resting level.
        """
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No heart rate data found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latest_resting_hr = queryset.latest('timestamp')

        avg_resting_hr = latest_resting_hr.get_resting_average()

        return Response({
            "Average_resting_heart_rate": avg_resting_hr
        })
    
    @action(detail=False, methods=['get'])
    def hrv(self, request):
        """
        End-point for calculate_hrv function in HeartRate class
        """
        try:
            time_window = int(request.query_params.get('time_window', 24))
            if time_window <= 0 or time_window > 24:
                return Response(
                    {"error": "Time window must be within 24hrs"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Time window parameter must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No heart rate data found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latest_hr = queryset.latest('timestamp')

        hrv_value = latest_hr.calculate_hrv(time_window)

        if not hrv_value:
            return Response(
                {"message": "Insufficent data to calculate HRV"},
                status=status.HTTP_200_OK)
        
        return Response({
            "hrv": hrv_value,
            "time_window_hours": time_window,
            "unit": "milliseconds (ms)",   
        },status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def baseline_comparison(self, request):
        """
        End point for function compare_to_baseline in HeartRate class
        """
        try:
            baseline_days = int(request.query_params.get('baseline_days', 30))
            if baseline_days <= 0 or baseline_days >= 90:
                return Response(
                    {"error": "Baseline days must be between 1 and 90"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Baseline days must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        baseline_activity = request.query_params.get('baseline_activity', None)
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No heart rate data found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latest_hr = queryset.latest('timestamp')

        result = latest_hr.compare_to_baseline(baseline_days=baseline_days, baseline_activity=baseline_activity)

        if not result:
            return Response(
                {"message": "Insufficient data to compute baseline comparsion"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            "basline_days": baseline_days,
            "activity_level": baseline_activity,
            **result
        }, status=status.HTTP_200_OK)


class SleepDurationViewSet(BaseHealthMetricsViewSet):
    """ViewSet for SleepDuration metric"""
    queryset = SleepDuration.objects.all()
    serializer_class = SleepDurationSerializer
    filterset_class = SleepDurationFilterSet
    search_fields = ['source']

    @action(detail=False, methods=['get'])
    def sufficiency_check(self, request):
        """ Endpoint for is_sufficient function in SleepDuration class"""
        if 'age' not in request.query_params:
            return Response(
                {'error': 'Age parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            age = int(request.query_params.get('age'))
            if age <= 0 or age >= 120:
                return Response(
                    {"error": "Age must be between 1 and 120"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Age parameter must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No sleep sessions found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latest_session = queryset.latest('timestamp')

        duration = latest_session.duration
        is_sufficient = latest_session.is_sufficient(age)

        # Calculate recommended ranges for response
        weekly_min, weekly_max = 7, 9
        if age:
            if 1 <= age < 3:
                weekly_min, weekly_max = 11, 14
            elif age < 6:
                weekly_min, weekly_max = 10, 13
            elif age < 13:
                weekly_min, weekly_max = 9, 11
            elif age < 18:
                weekly_min, weekly_max = 8, 10
            elif age > 65:
                weekly_min, weekly_max = 7, 8

        if is_sufficient:
            message = f"Your sleep duration of {duration:.1f} hours meets the recommended duration for your age"
        else:
            if duration < weekly_min:
                message = f"Your sleep duration of {duration:.1f} hours is below the recommended minimum of {weekly_min} hours for your age"
            else:
                message = f"Your sleep duration of {duration:1f} hours exceeds the recommended maximum of {weekly_max} hours for your age"

        response_data = {
            "is_sufficient":is_sufficient,
            "duration": duration,
            "recommended_range":{
                "min_hours": weekly_min,
                "max_hours": weekly_max
            },
            "age": age,
            "recommendation": message,
            "latest_session":{
                "start_time": latest_session.start_time.isoformat(),
                "end_time": latest_session.end_time.isoformat()
            }
        }

        # Add quality assessment if available
        if latest_session.quality is not None:
            response_data["quality"] = {
                "score": latest_session.quality,
                "scale": "1-10"
            }

        if latest_session.interruptions is not None:
            response_data['interruptions'] = latest_session.interruptions

        return Response(response_data)

    @action(detail=False, methods=['get'])
    def weekly_average(self, request):
        """Endpoint for weekly_average method in SleepDuration class"""
        try:
            days = int(request.query_params.get('days', 7))
            if days <= 0 or days >= 90:
                return Response(
                    {'error': "Days parameter must be between 1 and 90"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {'error': 'Days parameter must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No sleep sessions found for analysis"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        latest_session = queryset.latest('timestamp')

        weekly_avg = latest_session.get_weekly_average(days=days)

        if weekly_avg is None:
            return Response(
                {"message": "Insufficient data to calculate average sleep duration"},
                status=status.HTTP_200_OK
            )
        
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=days-1)

        # Count how many nights have data
        nights_with_data = queryset.filter(
            start_time__date__range=(start_date, end_date)
        ).dates('start_time', 'day').count()

        age = request.query_params.get('age')
        weekly_min, weekly_max = 49, 63
        
        if age:
            try:
                age = int(age)
                if 1 <= age < 3:
                    weekly_min, weekly_max = 77, 98
                elif age < 6:
                    weekly_min, weekly_max = 70, 91
                elif age < 13:
                    weekly_min, weekly_max = 63, 77
                elif age < 18:
                    weekly_min, weekly_max = 56, 70
                elif age > 65:
                    weekly_min, weekly_max = 49, 56
            except ValueError:
                pass

        if weekly_min <= weekly_avg <= weekly_max:
            assessment = "Your average sleep duration is within the recommended range."
        elif weekly_avg < weekly_min:
            assessment = f"Your average sleep duration is below the recommended minimum of {weekly_min} hours."
        else:
            assessment = f"Your average sleep duration exceeds the recommended maximum of {weekly_max} hours."

        response_data = {
            "weekly_average": weekly_avg,
            "date_range":{
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "nights_with_data": nights_with_data,
            "data_completeness": round((nights_with_data / days) * 100, 2),
            "recommended_range":{
                "min_hours": weekly_min,
                "max_hours": weekly_max
            },
            "assessment": assessment,
        }

        return Response(response_data)

        
class SpO2ViewSet(BaseHealthMetricsViewSet):
    """ViewSet for SpO2 metrics"""
    queryset = SpO2.objects.all()
    serializer_class = SpO2Serializer
    filterset_class = SpO2FilterSet
    search_fields = ['source', 'measurement_method']

    @action(detail=False, methods=['get'])
    def lowest_reading(self, request):
        """Endpoint for get_lowest_reading in SpO2 class"""
        try:
            days = int(request.query_params.get('days', 7))
            if days <= 0 or days > 7:
                return Response(
                    {"error": "Days parameter must be between 1 and 7"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Days parameter must be a valid integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset()

        start_date = timezone.now() - timedelta(days=days+1)

        filtered_queryset = queryset.filter(timestamp__gte=start_date)

        if not filtered_queryset.exists():
            return Response(
                {"error": "No oxygen level measurements found for analysis"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        min_value = filtered_queryset.aggregate(min_value=models.Min('value'))['min_value']
        print(f"Minimum value: {min_value}")
        
        return Response({
            "lowest_oxygen_level": f"{min_value}%"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def alert_check(self):
        """Endpoint for alert_required function in SpO2 class"""
        queryset = self.get_queryset()

        if not queryset.exists():
            return Response(
                {"error": "No oxygen level data found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        latests_spo2 = queryset.latest('timestamp')

        if latests_spo2:
            if latests_spo2 < 90:
                return Response(
                    {"message": "Immediate attention required"},
                    status=status.HTTP_200_OK
                )