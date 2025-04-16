from django.urls import path
from .views import Register, Login, UserView

urlpatterns = [
    path('user', UserView.as_view()),
    path('login', Login.as_view()),
    path('register', Register.as_view())
]