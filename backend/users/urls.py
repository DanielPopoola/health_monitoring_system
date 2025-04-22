from django.urls import path
from .views import Register, Login, UserView, Logout, CustomTokenObtainPairView

urlpatterns = [
    path('logout', Logout.as_view()),
    path('user', UserView.as_view()),
    path('login', Login.as_view()),
    path('register', Register.as_view()),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair')
]