from rest_framework import serializers
from .models import UserProfile, Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'name', 'age', 'gender',
                   'email', 'password', 'role', 'role_display']
        extra_kwargs = {
            'password': {'write_only': True}, # Ensures password is never sent in responses
            'role': {'read_only': True} # Prevent self-modification of role
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)

        instance = self.Meta.model(**validated_data)

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance

class PatientListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing patients, exposing only necessary fields.
    """
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'email', 'age', 'gender']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'
