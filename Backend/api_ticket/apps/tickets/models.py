from decimal import ROUND_HALF_UP, Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta
from apps.autenticacion.models import Usuario # Importa el modelo de usuario personalizado
from django.core.exceptions import ValidationError
from django.db.models import Q, F, Sum
from django.db.models.constraints import UniqueConstraint
from api.logger import logger

class Categoria(models.Model):
    nom_categoria = models.CharField(max_length=255)
    sla_horas = models.IntegerField(default=0 , null= True, blank= True)

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
        
    
    def save(self, *args, **kwargs):
        # Call clean method to validate data before saving
        self.clean()
        
        # Recalculate the current 'presupuesto_gastado'
        recalculated_gastado = Decimal(self.costos.filter(cierre=True).aggregate(
            total=Sum('monto_final')
        )['total'] or 0)
        print(recalculated_gastado)

        # Fetch the current 'presupuesto_gastado' from the database
        if self.pk:  # Only if this is not a new instance
            current_gastado = Decimal(PresupuestoTI.objects.filter(pk=self.pk).values_list(
                'presupuesto_gastado', flat=True
            ).first() or 0)
        else:
            current_gastado = Decimal(0)  # New instances have no current value
        
        # Only update if the recalculated value differs
        try:
            if not self.pk or recalculated_gastado != current_gastado:
                self.presupuesto_gastado = recalculated_gastado
                self.presupuesto_restante = self.presupuesto_mensual - self.presupuesto_gastado
                self.over_budget = self.presupuesto_gastado > self.presupuesto_mensual
                super().save(*args, **kwargs)  # Save only if there's a change
            else:
                # Log or skip saving since there are no changes
                logger.info(f"No changes detected for 'presupuesto_gastado'. Save skipped for {self.fecha_presupuesto.strftime('%Y-%m')}.")
        except Exception as e:
            logger.error(f"unexpected error on saving presupuesto object {self.id}, {str(e)}")
            

class Ticket(models.Model):
    titulo = models.CharField(max_length=255)
    comentario = models.TextField(null=True, blank=True)
    sla_status = models.CharField(max_length=40,default="Al dia", null= True, blank= True)
    categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE)
    prioridad = models.ForeignKey('Prioridad', on_delete=models.CASCADE)
    servicio = models.ForeignKey('Servicio', on_delete=models.CASCADE)
    estado = models.ForeignKey('Estado', on_delete=models.CASCADE)
    user = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    resolucion = models.TextField(null=True, blank=True)

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
        logger.debug(f"on:FechaTicket save. Saving Ticket ID: {self.ticket.id} Tipo Fecha: {self.tipo_fecha}")
        if self.tipo_fecha == 'Creacion':
            # Fetch the creation date from FechaTicket (tipo_fecha='Creacion')
            
            creacion_ticket = FechaTicket.objects.filter(ticket=self.ticket, tipo_fecha='Creacion').first()
            
            if creacion_ticket:
                creation_date = creacion_ticket.fecha
                logger.debug(f"on:FechaTicket save. Creation Date: {creation_date}")  # Use the 'fecha' field from FechaTicket for creation date
                
                if self.ticket.categoria:
                    sla_duration_hours = self.ticket.categoria.sla_horas
                    logger.info(f"SLA for the ticket (ID: {self.ticket.id}) is {sla_duration_hours} hours.")
                else:
                    sla_duration_hours = 42 # en caso de error entonces se define como duracion de sla de 2 dias 
                    logger.info("Ticket or category not found. Defaulting SLA duration to 0 hours.")
                    return 0
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
    presupuesto_ti = models.ForeignKey('PresupuestoTI', on_delete=models.CASCADE, related_name='costos')
    ticket = models.OneToOneField('Ticket', on_delete=models.CASCADE, related_name='costos')
    monto = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    horas_atraso = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True,blank=True)
    cierre = models.BooleanField(default= False, blank= True)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True,blank=True)
    fecha = models.DateField(null=True, blank=True)
    class Meta:
        unique_together = ('ticket', 'presupuesto_ti')  # Ensures 1 Costo per Ticket + PresupuestoTI
        # Or alternatively using constraints if using Django 2.2+
        constraints = [
            models.UniqueConstraint(fields=['ticket', 'presupuesto_ti'], name='unique_costo_ticket_presupuesto')
        ]
    def __str__(self):
        return f"Ticket ID {self.ticket.id} -Starting cost: {self.monto} - Final Cost: {self.monto_final}"
    #definir save or update
    def get_ticket_cost(self):
        """
        Fetch the base cost from the related Ticket's Service.
        """
        return self.ticket.servicio.costo or Decimal("0.00")

    def calculate_monto_final(self):
        """
        Calculate the final amount based on hours of delay and the base cost.
        """
        base_cost = self.get_ticket_cost()
        delay_multiplier = max(Decimal("1.00"), Decimal("1.00") + (Decimal("0.05") * self.horas_atraso))
        return (base_cost * delay_multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def is_ticket_closed(self):
        """
        Determine whether the related Ticket has a closure date.
        """
        cierre_fecha = self.ticket.fechaticket_set.filter(tipo_fecha='Cierre').first()
        logger.debug(f"Checking ticket closure: {self.ticket.id}, closure found: {bool(cierre_fecha)}")
        return cierre_fecha is not None

        
    def save(self, *args, **kwargs):
        
        # Call clean method to validate data before saving
        self.monto = self.get_ticket_cost()
        self.monto_final = self.calculate_monto_final()
        self.cierre = self.is_ticket_closed()
        super().save(*args, **kwargs)
        # Only save if any field has changed

class EvaluacionTicket(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name="evaluacion")
    nota = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],  # Actualizado para las caritas
        help_text="Calificación del ticket (1: Muy malo, 5: Excelente)"
    )

    feedback = models.TextField(blank=True, null=True, help_text="Comentarios opcionales")

    def __str__(self):
        return f"Evaluación para Ticket {self.ticket.id}: Nota {self.nota}"