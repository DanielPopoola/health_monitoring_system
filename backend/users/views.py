from rest_framework.views import APIView
from .serializers import UserSerializer, CustomTokenObtainPairSerializer
from .models import UserProfile
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import AllowAny


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
            'user': serializer.data
        }, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=False,
            samesite='Lax',
            max_age=3600
        )

        return response


class UserView(APIView):
    def get(self, request):
        token = request.COOKIES.get('access_token')

        if not token:
            return Response(
                {'error': 'Token not found!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            jwt_authenticator = JWTAuthentication()
            validated_token = jwt_authenticator.get_validated_token(token)
            user = jwt_authenticator.get_user(validated_token=validated_token)
        except(InvalidToken, AuthenticationFailed):
            return Response(
                {'error': 'Invalid or expired token!'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = UserSerializer(user)
        return Response({'user': serializer.data}, status=status.HTTP_200_OK)


class Logout(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.data = {
            'message': "Logout successful"
        }
        return response
