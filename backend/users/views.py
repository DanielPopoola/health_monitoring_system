from rest_framework.views import APIView
from rest_framework import generics
from .serializers import UserSerializer, CustomTokenObtainPairSerializer, PatientListSerializer
from .models import UserProfile, Role
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsDoctorOrNurseOrAdmin


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(request.data)
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "user": serializer.data,
                    "message": "User registered successfully",
                },
                status=status.HTTP_201_CREATED
            )
        else:
            print("Serializer errors:", serializer.errors)  
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '')
        password = request.data.get('password', '')

        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = UserProfile.objects.filter(email=email).first()

        if user is None:
            return Response(
                {'error': 'Invalid credentials!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Invalid credentials!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        serializer = UserSerializer(user)
        response = Response({
            'message': 'Login successful',
            'user': serializer.data,
            'access_token': access_token,
            'refresh_token': refresh_token
        }, status=status.HTTP_200_OK)

        return response


class UserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)


class PatientListView(generics.ListAPIView):
    """
    API view to list patients (users who are not staff/professionals).
    Accessible only by Doctors, Nurses, or Admins.
    """
    serializer_class = PatientListSerializer
    permission_classes = [IsAuthenticated, IsDoctorOrNurseOrAdmin]

    def get_queryset(self):
        """
        Return a list of all non-staff users (patients).
        """
        return UserProfile.objects.filter(role=Role.USER).order_by('last_name', 'first_name')

class Logout(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.data = {
            'message': "Logout successful"
        }
        return response
