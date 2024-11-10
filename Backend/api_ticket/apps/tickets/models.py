from django.db import models
from datetime import timedelta
from apps.autenticacion.models import Usuario  # Importa el modelo de usuario personalizado

class Categoria(models.Model):
    nom_categoria = models.CharField(max_length=255)

    def __str__(self):
        return self.nom_categoria

class Prioridad(models.Model):
    num_prioridad = models.CharField(max_length=10)

    def __str__(self):
        return self.num_prioridad

class Estado(models.Model):
    nom_estado = models.CharField(max_length=255)

    def __str__(self):
        return self.nom_estado



class Servicio(models.Model):
    titulo_servicio = models.CharField(max_length=20)
    costo = models.DecimalField(max_digits=12, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)  # Relación con Categoria

    def __str__(self):
        return self.titulo_servicio
    
class Ticket(models.Model):
    titulo = models.CharField(max_length=255)
    comentario = models.TextField(null=True, blank=True)
    sla_status = models.CharField(max_length=40, null= True, blank= True)
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE)
    prioridad = models.ForeignKey('Prioridad', on_delete=models.CASCADE)
    servicio = models.ForeignKey('Servicio', on_delete=models.CASCADE)
    estado = models.ForeignKey('Estado', on_delete=models.CASCADE)
    user = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.titulo

    
class FechaTicket(models.Model):
    fecha = models.DateTimeField()
    tipo_fecha = models.CharField(max_length=40, choices=[
        ('Creacion', 'Creación'), 
        ('cierre_esperado', 'cierre_esperado'),
        ('Cierre', 'Cierre'),
    ])
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='fechaticket_set')

    def __str__(self):
        return f"Fecha {self.fecha} ({self.tipo_fecha}) para Ticket {self.ticket}"
    class Meta:
        unique_together = ('fecha', 'ticket')
        
    def save(self, *args, **kwargs):
        print(self.fecha, self.tipo_fecha)
        super().save(*args, **kwargs)

        # Debugging prints
        print(f"Saving Ticket ID: {self.ticket.id}")
        print(f"Tipo Fecha: {self.tipo_fecha} for Ticket ID: {self.ticket.id}")
        
        if self.tipo_fecha == 'Creacion':
            # Fetch the creation date from FechaTicket (tipo_fecha='Creacion')
            creation_date_obj = FechaTicket.objects.filter(ticket=self.ticket, tipo_fecha='Creacion').first()
            
            if creation_date_obj:
                creation_date = creation_date_obj.fecha
                print(f"Creation Date: {creation_date}")  # Use the 'fecha' field from FechaTicket for creation date
                
                sla_duration_hours = 48  # You can use a dynamic SLA based on priority or other factors
                
                # Ensure that we're adding SLA duration to the ticket's creation date
                expected_closure_date = creation_date + timedelta(hours=sla_duration_hours)
                
                print(f"Calculated expected closure date: {expected_closure_date} for Ticket ID: {self.ticket.id}")
                
                # Check if 'Cierre Esperado' entry already exists
                existing_expected_closure = FechaTicket.objects.filter(
                    ticket=self.ticket, tipo_fecha='Cierre Esperado'
                ).first()

                if not existing_expected_closure:
                    # Create a new 'Cierre Esperado' FechaTicket entry with the correct expected closure date
                    print(f"Creating 'Cierre Esperado' FechaTicket for Ticket ID: {self.ticket.id} with date {expected_closure_date}")
                    FechaTicket.objects.create(
                        ticket=self.ticket,
                        tipo_fecha='cierre_esperado',
                        fecha=expected_closure_date
                    )
            else:
                print(f"No creation date found for Ticket ID: {self.ticket.id}. Cannot calculate expected closure date.")
                
        else:
            print(f"Skipping SLA logic for Tipo Fecha: {self.tipo_fecha}")
class DetalleUsuarioTicket(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    usuario = models.ForeignKey('autenticacion.Usuario', on_delete=models.CASCADE)
    relacion_ticket = models.CharField(max_length=20, choices=[
        ('creador', 'Creador'),
        ('asignado', 'Asignado'),
        ('resuelto', 'Resuelto')
    ])

    def __str__(self):
        return f"Usuario {self.usuario.nom_usuario} - {self.relacion_ticket} en Ticket {self.ticket}"

    class Meta:
        unique_together = ('ticket', 'usuario', 'relacion_ticket')
