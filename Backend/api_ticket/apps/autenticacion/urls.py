from django.urls import path
from knox import views as knox_views
from .views import LoginView, RegistroView
from .views import CargoListAPIView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer  # Importar el serializador personalizado
urlpatterns = [
    path('registrar/', RegistroView.as_view(), name='registrar'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', knox_views.LogoutView.as_view(), name='logout'),
    path('logout-all/', knox_views.LogoutAllView.as_view(), name='logout_all'),
    path('api/cargos/', CargoListAPIView.as_view(), name='cargo-list'),
    path('api/token/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]