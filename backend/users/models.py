from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# Create your models here.
class UserProfileManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class Role(models.TextChoices):
    USER = 'USER', 'User'
    DOCTOR = 'DOCTOR', 'Doctor'
    NURSE = 'NURSE', 'Nurse'
    ADMIN = 'ADMIN', 'Admin'

class UserProfile(AbstractUser):
    name = models.CharField(max_length=55)
    email = models.EmailField(unique=True)
    username = None
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, 
                            default=Role.USER, help_text="User role in the system")


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserProfileManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def is_healthcare_professional(self):
        return self.role in [Role.DOCTOR, Role.NURSE]
    
    @property
    def is_regular_user(self):
        return self.role == Role.USER




