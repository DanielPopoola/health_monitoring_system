from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile

# Register your models here.
@admin.register(UserProfile)
class CustomUserAdmin(UserAdmin):
    model = UserProfile
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name', 'name')
    ordering = ('email', )

    fieldsets = (
        (None, {'fields':('email', 'password')}),
        ('Personal info', {'fields': ('name', 'first_name', 'last_name', 'age', 'gender')}),
        ('Role', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password', 'password2',
                'first_name', 'last_name', 'name', 'age', 'gender',
                'role',
                'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
                ),
        }),
    )


    filter_horizontal = ('groups', 'user_permissions')