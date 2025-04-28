from rest_framework import permissions


class IsDoctorOrNurseOrAdmin(permissions.BasePermission):
    """
    Allows access only to users with Doctor, Nurse, or Admin roles.
    """
    message = "You do not have permission to access patient data."
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ["DOCTOR", "NURSE", "ADMIN"]