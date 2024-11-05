from rest_framework import permissions
from knox.views import LoginView as KnoxLoginView
from django.contrib.auth import authenticate, login
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserCreateSerializer
from rest_framework import generics
from .models import Cargo
from .serializers import CargoSerializer, CustomTokenObtainPairSerializer, UsuarioSerializer
from rest_framework_simplejwt.views import TokenObtainPairView # type: ignore
from django.contrib.auth import get_user_model

class LoginView(KnoxLoginView):
    permission_classes = (permissions.AllowAny,)
    def post(self, request, format=None):
        # Autenticación del usuario con correo y contraseña
        correo = request.data.get('correo')
        password = request.data.get('password')
        
        # Autenticación
        user = authenticate(request, correo=correo, password=password)
        if user is None:
            return Response({"error": "Credenciales no válidas"}, status=400)
        login(request,user)
        return super(LoginView, self).post(request, format=None)
    


class RegistroView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = (permissions.AllowAny,)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({"message": "Usuario creado exitosamente"}, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        user = self.request.user  # Usuario autenticado
        if not user.is_authenticated or user.role != 'admin':
            # Si el usuario no es admin, forzamos el rol a 'usuario'
            serializer.save(role='usuario')
        else:
            serializer.save()

class CargoListAPIView(generics.ListAPIView):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = (permissions.AllowAny,)

class UsuarioListAPIView(generics.ListAPIView):
    User = get_user_model()
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    #permission_classes = (permissions.IsAuthenticated)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer