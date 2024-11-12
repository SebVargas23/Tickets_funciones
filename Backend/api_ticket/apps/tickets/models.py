from django.db import models, IntegrityError
from datetime import timedelta
from apps.autenticacion.models import Usuario # Importa el modelo de usuario personalizado
from django.core.exceptions import ValidationError
from django.db.models import Q, F
from django.db.models.constraints import UniqueConstraint
from api.logger import logger

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

class PresupuestoTI(models.Model):
    presupuesto_mensual = models.DecimalField(max_digits=12, decimal_places=2, default=1000000 ,  help_text="Monthly budget for the department")
    presupuesto_gastado = models.DecimalField(max_digits=12, decimal_places=2, default=0 , help_text="Amount spent for the month")
    presupuesto_restante = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # Adjust size if needed
    over_budget = models.BooleanField(default=False, null=True, blank=True)
    fecha_presupuesto = models.DateField(help_text="Month for this budget record")
    class Meta:
            constraints = [
                UniqueConstraint(
                    name="unique_monthly_presupuesto",
                    fields=["fecha_presupuesto"],
                    condition=Q(
                        fecha_presupuesto__month=F("fecha_presupuesto__month"),
                          fecha_presupuesto__year=F("fecha_presupuesto__year")
                          )
                )
            ]

    def __str__(self):
        return f"{self.fecha_presupuesto.strftime('%Y-%m')} - Spent: {self.presupuesto_gastado} / Monthly Budget: {self.presupuesto_mensual}"
    
    def clean(self):
        # Ensure no duplicate presupuesto for the same month
        if self.fecha_presupuesto.day != 1:
            self.fecha_presupuesto = self.fecha_presupuesto.replace(day=1)

        duplicate = PresupuestoTI.objects.filter(
            fecha_presupuesto__month=self.fecha_presupuesto.month,
            fecha_presupuesto__year=self.fecha_presupuesto.year
        ).exclude(pk=self.pk)  # Exclude self to allow updates on the current record

        if duplicate.exists():
            raise ValidationError(f"Ya existe un presupuesto para el mes: {self.fecha_presupuesto.strftime('%Y-%m')}. Solo se permite 1 presupuesto por mes.")

        # Calculate remaining budget and set the over_budget flag
        if self.presupuesto_mensual and self.presupuesto_gastado is not None:
            self.presupuesto_restante = self.presupuesto_mensual - self.presupuesto_gastado
            self.over_budget = self.presupuesto_gastado > self.presupuesto_mensual
    
    def save(self, *args, **kwargs):
        # Call clean method to validate data before saving
        self.clean()
        super().save(*args, **kwargs)

class Ticket(models.Model):
    titulo = models.CharField(max_length=255)
    comentario = models.TextField(null=True, blank=True)
    sla_status = models.CharField(max_length=40,default="On Track", null= True, blank= True)
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
        logger.debug("on:FechaTicket save - Fecha: %s, Tipo de fecha: %s", self.fecha, self.tipo_fecha)
        super().save(*args, **kwargs)

        # Debugging prints
        logger.debug(f"on:FechaTicket save. Saving Ticket ID: {self.ticket.id}")
        logger.debug(f"on:FechaTicket save. Tipo Fecha: {self.tipo_fecha} for Ticket ID: {self.ticket.id}")
        
        if self.tipo_fecha == 'Creacion':
            # Fetch the creation date from FechaTicket (tipo_fecha='Creacion')
            creation_date_obj = FechaTicket.objects.filter(ticket=self.ticket, tipo_fecha='Creacion').first()
            
            if creation_date_obj:
                creation_date = creation_date_obj.fecha
                logger.debug(f"on:FechaTicket save. Creation Date: {creation_date}")  # Use the 'fecha' field from FechaTicket for creation date
                
                sla_duration_hours = 48  # You can use a dynamic SLA based on priority or other factors
                
                # Ensure that we're adding SLA duration to the ticket's creation date
                expected_closure_date = creation_date + timedelta(hours=sla_duration_hours)
                
                logger.debug(f"on:FechaTicket save. Calculated expected closure date: {expected_closure_date} for Ticket ID: {self.ticket.id}")
                
                # Check if 'Cierre Esperado' entry already exists
                existing_expected_closure = FechaTicket.objects.filter(
                    ticket=self.ticket, tipo_fecha='cierre_esperado'
                ).first()

                if not existing_expected_closure:
                    # Create a new 'Cierre Esperado' FechaTicket entry with the correct expected closure date
                    logger.info(f"on:FechaTicket save. Creating 'Cierre Esperado' FechaTicket for Ticket ID: {self.ticket.id} with date {expected_closure_date}")
                    FechaTicket.objects.create(
                        ticket=self.ticket,
                        tipo_fecha='cierre_esperado',
                        fecha=expected_closure_date
                    )
            else:
                logger.warning(f"on:FechaTicket save. No creation date found for Ticket ID: {self.ticket.id}. Cannot calculate expected closure date.")
                
        else:
            logger.warning(f"on:FechaTicket save. skipped because Tipo Fecha is not 'Creacion' but '{self.tipo_fecha}'")

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

class Costo(models.Model):
    ticket = models.ForeignKey('Ticket', on_delete=models.CASCADE, related_name='costos')
    presupuesto_ti = models.ForeignKey('PresupuestoTI', on_delete=models.CASCADE, related_name='costos')
    monto = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    calculo_monto = models.DecimalField(max_digits=10, decimal_places=2, default=1, null=True,blank=True)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True,blank=True)
    fecha = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Ticket ID {self.ticket.id} -Starting cost: {self.monto} - Final Cost: {self.monto_final}"
    #definir save or update
