from rest_framework import serializers
from .models import *
from apps.autenticacion.models import Cargo, Departamento
from django.utils.timezone import localtime


class DepartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model= Departamento
        fields = ['id','nom_departamento']
class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model=Cargo
        fields=['id','nom_cargo','departamento']
    
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model= Categoria
        fields = ['id','nom_categoria']

class EstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estado
        fields = ['id','nom_estado']

class PrioridadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prioridad
        fields = ['id','num_prioridad']

class ServicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ['id','titulo_servicio','costo', 'categoria_id']

class TicketSerializer(serializers.ModelSerializer):
    fecha_creacion = serializers.SerializerMethodField()
    fecha_cierre = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(
        slug_field='nom_usuario',
        queryset=Usuario.objects.all(),
        required=False
    )
    estado = serializers.PrimaryKeyRelatedField(queryset=Estado.objects.all())  # Ajuste aquí
    class Meta:
        model = Ticket
        fields = [
            'id', 'titulo', 'comentario', 'categoria',
            'prioridad', 'servicio', 'estado', 'user',
            'fecha_creacion', 'fecha_cierre'
        ]

    def get_fecha_creacion(self, obj):
        fecha_creacion = FechaTicket.objects.filter(ticket=obj, tipo_fecha='Creacion').first()
        if fecha_creacion:
            return localtime(fecha_creacion.fecha).strftime('%Y-%m-%d %H:%M:%S')  # Formato ajustado
        return None
    def get_fecha_cierre(self, obj):
        # Obtener la fecha de cierre del modelo FechaTicket
        fecha_cierre = FechaTicket.objects.filter(ticket=obj, tipo_fecha='Cierre').first()
        if fecha_cierre:
            return localtime(fecha_cierre.fecha).strftime('%Y-%m-%d %H:%M:%S')
        return None

    def get_user(self, obj):
        return obj.user.nom_usuario if obj.user else None  # Ajusta 'nom_usuario' al campo correcto en tu modelo de usuario

    def update(self, instance, validated_data):
        # Actualizar el ticket con datos validados
        instance.titulo = validated_data.get('titulo', instance.titulo)
        instance.comentario = validated_data.get('comentario', instance.comentario)
        instance.categoria = validated_data.get('categoria', instance.categoria)
        instance.prioridad = validated_data.get('prioridad', instance.prioridad)
        instance.servicio = validated_data.get('servicio', instance.servicio)
        instance.estado = validated_data.get('estado', instance.estado)
        instance.save()

        # Manejar la fecha de cierre
        fecha_cierre = validated_data.get('fecha_cierre', None)
        if fecha_cierre:
            FechaTicket.objects.update_or_create(
                ticket=instance,
                tipo_fecha='Cierre',
                defaults={'fecha': fecha_cierre}
            )

        return instance
    
class DetalleUsuarioTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleUsuarioTicket
        fields = ['ticket','usuario','relacion_ticket']

'''class DetalleServicioSerializer(serializers.ModelSerializer):
    model = DetalleServicio
    fields = ['id','ticket','servicio']''' 

class FechaTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = FechaTicket
        fields = ['id','fecha','tipo_fecha']