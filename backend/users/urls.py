from django.urls import path
from .views import Register, Login

urlpatterns = [
    path('login', Login.as_view()),
    path('register', Register.as_view())
]