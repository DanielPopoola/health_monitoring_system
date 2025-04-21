from rest_framework.routers import DefaultRouter
from .views import (
    BloodPressureViewSet,
    DailyStepsViewSet,
    HeartRateViewSet,
    SleepDurationViewSet,
    SpO2ViewSet
)

router = DefaultRouter()
router.register(r'blood-pressure', BloodPressureViewSet)
router.register(r'daily-steps', DailyStepsViewSet)
router.register(r'heart-rate', HeartRateViewSet)
router.register(r'sleep-duration', SleepDurationViewSet)
router.register(r'spo2', SpO2ViewSet)

urlpatterns = router.urls