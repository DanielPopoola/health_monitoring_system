from rest_framework import serializers
from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'name', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}  # Ensures password is never sent in responses
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
