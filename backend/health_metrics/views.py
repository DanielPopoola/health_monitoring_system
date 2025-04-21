from rest_framework import viewsets, filters, permissions
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from .models import BloodPressure, DailySteps, HeartRate, SleepDuration, SpO2
from .serializers  import (
    BloodPressureSerializer,
    DailyStepsSerializer,
    HeartRateSerializer,
    SleepDurationSerializer,
    SpO2Serializer
)
# Create your views here.
class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for all viewsets"""
    page_size = 20
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
    filterset_fields = ['source', 'timestamp']
    search_fields = ['source']

class DailyStepsViewSet(BaseHealthMetricsViewSet):
    """ViewSet for DailySteps metrics"""
    queryset = DailySteps.objects.all()
    serializer_class = DailyStepsSerializer
    filterset_fields = ['source', 'timestamp', 'device']
    search_fields = ['source', 'device']

class HeartRateViewSet(BaseHealthMetricsViewSet):
    """ViewSet for HeartRate metrics"""
    queryset = HeartRate.objects.all()
    serializer_class = HeartRateSerializer
    filterset_fields = ['source', 'timestamp', 'activity_level']
    search_fields = ['source', 'activity_level']

class SleepDurationViewSet(BaseHealthMetricsViewSet):
    """ViewSet for SleepDuration metric"""
    queryset = SleepDuration.objects.all()
    serializer_class = SleepDurationSerializer
    filterset_fields = ['source', 'timestamp', 'start_time', 'end_time']
    search_fields = ['source']

class SpO2ViewSet(BaseHealthMetricsViewSet):
    """ViewSet for SpO2 metrics"""
    queryset = SpO2.objects.all()
    serializer_class = SpO2Serializer
    filterset_fields = ['source', 'timestamp', 'measurement_method']
    search_fields = ['source', 'measurement_method']
    