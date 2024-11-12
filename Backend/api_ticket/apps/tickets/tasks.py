from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from datetime import timedelta
from django.utils import timezone
from apps.tickets.models import Ticket
from .models import Costo, PresupuestoTI
from django.db.models import Sum
import math
from django.db import transaction
from api.logger import logger
from decimal import ROUND_HALF_UP, Decimal

def update_sla_status(ticket_id=None):
    """
    Updates the SLA status for a specific ticket or all tickets.
    It will call the appropriate function for open and closed tickets.
    """
    try:
        # Fetch the tickets to update (filter by ticket_id if provided)
        if ticket_id:
            tickets = Ticket.objects.filter(id=ticket_id).prefetch_related('fechaticket_set')
        else:
            tickets = Ticket.objects.all().prefetch_related('fechaticket_set')

        for ticket in tickets:
            # Check if the ticket has a cierre_real date (closed ticket)
            cierre_real = ticket.fechaticket_set.filter(tipo_fecha='Cierre').first()

            if cierre_real:
                # Closed ticket, update SLA status and cost (calculo_monto)
                update_sla_status_for_closed_ticket(ticket, cierre_real)
            else:
                # Open ticket, just update the SLA status without calculating monto
                update_sla_status_for_open_ticket(ticket)

    except Exception as e:
        logger.error(f"Error updating SLA status: {str(e)}")

def update_sla_status_for_open_ticket(ticket):
    """
    Updates SLA status for open tickets only (no cost calculations).
    """
    now = timezone.now()
    fecha_esperada = ticket.fechaticket_set.filter(tipo_fecha='cierre_esperado').first()
    
    if not fecha_esperada:
        logger.warning(f"Expected closure date not found for open Ticket ID {ticket.id}. Skipping update.")
        return

    cierre_esperado = fecha_esperada.fecha
    if now > cierre_esperado:
        logger.info(f"ticket {ticket.id} has breached sla")
        new_sla_status = 'Breached'
        breach_duration = math.floor((now -cierre_esperado).total_seconds() / 3600)
        logger.info(f"breach duration of {breach_duration} hours")
        calc_monto = max(1.00, 1.00 + 0.05 * breach_duration)
        logger.info(f"calculo monto = {calc_monto}")
    elif now + timedelta(days=1) > cierre_esperado:
        logger.info(f"ticket {ticket.id} is at risk")
        new_sla_status = 'At Risk'
        calc_monto =1.00
        logger.info(f"calculo monto = {calc_monto}")
    elif now > cierre_esperado:
        logger.info(f"tikcet {ticket.id} is on track")
        new_sla_status = 'On Track'
        calc_monto = 1.00
        logger.info(f"calculo monto = {calc_monto}")
    calc_monto_D = Decimal(str(calc_monto)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    costo = Costo.objects.filter(ticket_id=ticket.id).first()
    if costo:
        if costo.calculo_monto != calc_monto_D:
            costo.calculo_monto = calc_monto_D
            costo.monto_final = 0   # Set monto to 0 for open tickets
            costo.save()
            logger.info(f"SLA status updated for open Ticket ID {ticket.id}, calculo_monto set to {calc_monto}, monto set to 0")
        else:
            logger.info(f"skiped update of costo from open ticket id {ticket.id} because there was no change in calculo_monto{calc_monto_D}, and {costo.calculo_monto}")
    # Update SLA status if it has changed
    if ticket.sla_status != new_sla_status:
        ticket.sla_status = new_sla_status
        ticket.save()
        logger.info(f"SLA status updated for open Ticket ID {ticket.id} to {new_sla_status}")

def update_sla_status_for_closed_ticket(ticket, cierre_real):
    """
    Updates SLA status and calculo_monto for closed tickets.
    """
    fecha_esperada = ticket.fechaticket_set.filter(tipo_fecha='cierre_esperado').first()
    
    if not fecha_esperada:
        logger.warning(f"Expected closure date not found for closed Ticket ID {ticket.id}. Skipping update.")
        return

    cierre_esperado = fecha_esperada.fecha
    if cierre_real.fecha <= cierre_esperado:
        new_sla_status = 'On Track'
        calc_monto = 1.00
    else:
        new_sla_status = 'Breached'
        breach_duration = math.floor((cierre_real.fecha - cierre_esperado).total_seconds() / 3600)
        calc_monto = max(1.00, 1.00 + 0.05 * breach_duration)
    calc_monto_D = Decimal(str(calc_monto))
    
    # Update Costo model with new calc_monto if needed
    costo = Costo.objects.filter(ticket_id=ticket.id).first()
    if costo and (costo.calculo_monto != calc_monto_D):
        costo.calculo_monto = calc_monto_D
        costo.monto_final = costo.monto * calc_monto_D
        costo.save()
        logger.info(f"Updated calc_monto for closed Ticket ID {ticket.id} to {calc_monto_D}")
    
    # Update SLA status if it has changed
    if ticket.sla_status != new_sla_status:
        ticket.sla_status = new_sla_status
        ticket.save()
        logger.info(f"SLA status updated for closed Ticket ID {ticket.id} to {new_sla_status}")

@transaction.atomic
def definir_costo(ticket_id=None):
    try:
        logger.info(f"on: definir_costo. Starting cost definition process.")
        if ticket_id:
            # Retrieve the specific ticket if ticket_id is provided
            tickets = [Ticket.objects.get(id=ticket_id)]
        else:
            # Retrieve all tickets if no ticket_id is provided
            tickets = Ticket.objects.all()

        for ticket in tickets:
            try:
                # Access the 'servicio' related to the ticket
                servicio = ticket.servicio  # This accesses the Servicio instance associated with the ticket
                if not servicio:
                    raise ValueError(f"on: definir_costo. Servicio not found for ticket ID {ticket.id}")
                logger.info(f"on: definir_costo. Servicio associated with ticket {ticket.id}: {servicio}")

                # Access base_cost from the servicio if it exists, otherwise use a default of 0
                monto = servicio.costo if servicio and servicio.costo else 0
                logger.info(f"on: definir_costo. Calculated monto based on servicio costo: {monto}")

                # Get the current month for PresupuestoTI creation
                fecha_actual = timezone.now().replace(day=1)
                logger.info(f"on: definir_costo. Current year and month: {timezone.now().strftime('%Y/%m')}")

                # Get or create the current month's PresupuestoTI
                presupuesto_ti, created = PresupuestoTI.objects.get_or_create(
                    fecha_presupuesto=fecha_actual
                )

                if created:
                    # If the object was created, log that the record was created
                    logger.info(f"on: definir_costo. Created new presupuesto record for {fecha_actual.strftime('%Y/%m')}")
                else:
                    # If the object already exists, log that the record was found
                    logger.info(f"on: definir_costo. Presupuesto record already exists for {fecha_actual.strftime('%Y/%m')}")


                # Check if a Costo instance already exists for this ticket and presupuesto_ti
                costo_instance = Costo.objects.filter(ticket=ticket, presupuesto_ti=presupuesto_ti).first()

                if costo_instance:
                    # If it exists, update the monto
                    logger.info(f"on: definir_costo. Updating existing Costo instance: {costo_instance}")
                    costo_instance.monto = monto
                    costo_instance.save()
                    logger.info(f"on: definir_costo. Updated Costo instance with new monto: {costo_instance.monto}")
                else:
                    # If no existing instance, create a new one
                    costo_instance = Costo.objects.create(
                        ticket=ticket,
                        presupuesto_ti=presupuesto_ti,
                        monto=monto,
                        fecha=timezone.now()
                    )
                    logger.info(f"on: definir_costo. New Costo instance created: {costo_instance}")
            except ObjectDoesNotExist as e:
                logger.error(f"on: definir_costo. Error: {str(e)}. Ticket ID: {ticket.id} or related service not found.")
            except ValueError as e:
                logger.error(f"on: definir_costo. Error: {str(e)}. Ticket ID: {ticket.id}.")
            except IntegrityError as e:
                logger.error(f"on: definir_costo. Database IntegrityError: {str(e)}. Ticket ID: {ticket.id}.")
            except Exception as e:
                logger.error(f"on: definir_costo. Unexpected error for Ticket ID {ticket.id}: {str(e)}")
    except Exception as e:
        logger.error(f"on: definir_costo. Error processing tickets: {str(e)}")
        
def calcular_presupuesto_gastado(date):
    """
    Calculates and updates the 'presupuesto_gastado' field for a given month and year.
    This function can be called from anywhere without requiring an instance.
    """
    try:
        logger.info(f"on: calcular_presupuesto_gastado. Starting presupuesto_gastado calculation for {date.strftime('%Y-%m-%d')}.")
        fecha_update=date.replace(day=1)
        logger.info(f"on: calcular_presupuesto_gastado. month calculated to {fecha_update.strftime('%Y-%m')}.")
        # Calculate the total amount spent for the given month and year
        total_gastado = Costo.objects.filter(
            fecha__year=date.year,
            fecha__month=date.month
        ).aggregate(Sum('monto_final'))['monto_final__sum'] or 0

        # Get or create the corresponding 'PresupuestoTI' for the given month and year
        presupuesto_ti, created = PresupuestoTI.objects.get_or_create(
            fecha_presupuesto=fecha_update
        )

        if created:
            # If the object was created, log that the record was created
            logger.info(f"on: calcular_presupuesto_gastado. Created new presupuesto record for {fecha_update.strftime('%Y/%m')}")
        else:
            # If the object already exists, log that the record was found
            logger.info(f"on: calcular_presupuesto_gastado. Presupuesto record already exists for {fecha_update.strftime('%Y/%m')}")

        # Only update and save if the calculated value differs from the current one
        if presupuesto_ti.presupuesto_gastado != total_gastado:
            presupuesto_ti.presupuesto_gastado = total_gastado
            presupuesto_ti.save()
            logger.info(f"on: calcular_presupuesto_gastado. Updated 'presupuesto_gastado' for {date.strftime('%Y-%m')}: {presupuesto_ti.presupuesto_gastado}")
        else:
            logger.info(f"on: calcular_presupuesto_gastado. No changes in 'presupuesto_gastado' for {date.strftime('%Y-%m')}; no update needed.")
    except ObjectDoesNotExist as e:
        logger.error(f"on: calcular_presupuesto_gastado. PresupuestoTI object not found for the date {date.strftime('%Y-%m')}: {str(e)}")
    except IntegrityError as e:
        logger.error(f"on: calcular_presupuesto_gastado. Database IntegrityError while updating 'presupuesto_gastado' for {date.strftime('%Y-%m')}: {str(e)}")
    except Exception as e:
        logger.error(f"on: calcular_presupuesto_gastado. Unexpected error while calculating 'presupuesto_gastado' for {date.strftime('%Y-%m')}: {str(e)}")

