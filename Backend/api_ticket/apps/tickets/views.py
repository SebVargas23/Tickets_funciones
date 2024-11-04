from rest_framework import generics,status
from .models import Categoria, Estado, Prioridad, Servicio, Ticket, DetalleUsuarioTicket, FechaTicket,Usuario
from apps.autenticacion.models import Departamento, Cargo
from apps.autenticacion.serializers import UsuarioSerializer
from .serializers import (
    DepartamentoSerializer, CargoSerializer, CategoriaSerializer, 
    EstadoSerializer, PrioridadSerializer, ServicioSerializer, 
    TicketSerializer, DetalleUsuarioTicketSerializer, FechaTicketSerializer,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from .models import Usuario, Ticket
from django.db.models import Count


# Departamento Views
class DepartamentoListCreateView(generics.ListCreateAPIView):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer

class DepartamentoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Departamento.objects.all()
    serializer_class = DepartamentoSerializer

# Cargo Views
class CargoListCreateView(generics.ListCreateAPIView):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer

class CargoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer

# Categoria Views
class CategoriaListCreateView(generics.ListCreateAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

# Estado Views
class EstadoListCreateView(generics.ListCreateAPIView):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer

class EstadoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer

# Prioridad Views
class PrioridadListCreateView(generics.ListCreateAPIView):
    queryset = Prioridad.objects.all()
    serializer_class = PrioridadSerializer

class PrioridadDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Prioridad.objects.all()
    serializer_class = PrioridadSerializer

# Servicio Views
class ServicioListCreateView(generics.ListCreateAPIView):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer

class ServicioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Servicio.objects.all()
    serializer_class = ServicioSerializer

# Ticket Views
class TicketListCreateView(generics.ListCreateAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Si el usuario es admin, retorna todos los tickets; si no, solo los tickets creados por él X Usuario
        if user.role == 'admin':
            return Ticket.objects.all()
        return Ticket.objects.filter(user=user)

    def perform_create(self, serializer):
        # Obtener el usuario autenticado
        usuario_autenticado = self.request.user

        # Verificar si es una instancia válida del modelo de usuario personalizado
        if isinstance(usuario_autenticado, Usuario):
            serializer.save(user=usuario_autenticado)
        else:
            raise ValueError("El usuario autenticado no es una instancia de Usuario.")

        # Crear la fecha de creación en FechaTicket
        FechaTicket.objects.create(ticket=serializer.instance, tipo_fecha='Creacion')



# Vista para manejar GET, PUT, PATCH y DELETE en un ticket específico
class TicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def retrieve(self, request, *args, **kwargs):
        ticket = self.get_object()
        ticket_data = self.get_serializer(ticket).data
        # Obtener la fecha de creación más reciente de FechaTicket para este ticket
        fecha_creacion = FechaTicket.objects.filter(ticket=ticket, tipo_fecha='Creacion').order_by('-fecha').first()
        ticket_data['fecha_creacion'] = fecha_creacion.fecha if fecha_creacion else None
        return Response(ticket_data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Manejar la actualización del estado
        estado_id = request.data.get('estado')
        if estado_id:
            estado_obj = get_object_or_404(Estado, id=estado_id)
            request.data['estado'] = estado_obj.id

        # Manejar la actualización del usuario
        user_id = request.data.get('user')
        if user_id:
            try:
                user = Usuario.objects.get(nom_usuario=nom_usuario)
                request.data['user'] = user.id  # Asegurarse de usar el ID interno para la actualización
            except Usuario.DoesNotExist:
                raise ValidationError({"user": "Usuario no encontrado"})

        # Serializar y actualizar el ticket
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Si el estado cambia a "Cerrado", crea o actualiza la fecha de cierre
        if estado_obj.nom_estado == "Cerrado":
            fecha_cierre, created = FechaTicket.objects.get_or_create(
                ticket=instance, tipo_fecha='Cierre',
                defaults={'fecha': timezone.now()}
            )
            if not created:
                fecha_cierre.fecha = timezone.now()
                fecha_cierre.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
    
# DetalleUsuarioTicket Views
class DetalleUsuarioTicketListCreateView(generics.ListCreateAPIView):
    queryset = DetalleUsuarioTicket.objects.all()
    serializer_class = DetalleUsuarioTicketSerializer

class DetalleUsuarioTicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DetalleUsuarioTicket.objects.all()
    serializer_class = DetalleUsuarioTicketSerializer

# FechaTicket Views
class FechaTicketListCreateView(generics.ListCreateAPIView):
    queryset = FechaTicket.objects.all()
    serializer_class = FechaTicketSerializer

class FechaTicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FechaTicket.objects.all()
    serializer_class = FechaTicketSerializer

class ClosedTicketListView(generics.ListAPIView):
    queryset = Ticket.objects.filter(estado__nom_estado='Cerrado')
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
def dashboard_stats(request):
    usuarios_totales = Usuario.objects.count()
    tickets_totales = Ticket.objects.count()
    tickets_abiertos = Ticket.objects.filter(estado__nom_estado="Abierto").count()
    tickets_cerrados = Ticket.objects.filter(estado__nom_estado="Cerrado").count()
    tickets_pendientes = Ticket.objects.filter(estado__nom_estado="Pendiente").count()
    # Agrega más estadísticas según necesites

    data = {
        "usuarios_totales": usuarios_totales,
        "tickets_totales": tickets_totales,
        "tickets_abiertos": tickets_abiertos,
        "tickets_cerrados": tickets_cerrados,
        "tickets_pendientes": tickets_pendientes,
        # Agrega otros datos aquí
    }
    return Response(data)

@api_view(['GET'])
def list_usuarios(request):
    usuarios = Usuario.objects.all()
    serializer = UsuarioSerializer(usuarios, many=True)
    return Response(serializer.data)