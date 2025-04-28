from django.urls import path, include
from .views import Register, Login, UserView, Logout, CustomTokenObtainPairView, PatientListView


urlpatterns = [
    path('patients/', PatientListView.as_view(), name='patient-list'),
    path('logout', Logout.as_view()),
    path('user', UserView.as_view()),
    path('login', Login.as_view()),
    path('register', Register.as_view()),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair')
]