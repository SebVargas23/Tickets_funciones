from datetime import timedelta
from django.utils import timezone
from apps.tickets.models import Ticket

def update_sla_status(ticket_id=None):
    """
    Updates the SLA status for a specific ticket or all tickets if no ticket_id is provided.

    Args:
        ticket_id (int, optional): The ID of the specific ticket to update. Defaults to None.

    Returns:
        str: A message indicating the update status.
    """
    now = timezone.now()

    # Fetch tickets to update (prefetch related FechaTicket entries to optimize database queries)
    if ticket_id:
        tickets = Ticket.objects.filter(id=ticket_id).prefetch_related('fechaticket_set')
    else:
        tickets = Ticket.objects.all().prefetch_related('fechaticket_set')

    # Process each ticket to update SLA status
    for ticket in tickets:
        try:
            # Get the expected closure date (cierre_esperado)
            fecha_esperada = ticket.fechaticket_set.filter(tipo_fecha='cierre_esperado').first()
            if not fecha_esperada:
                print(f"Expected closure date not found for Ticket ID {ticket.id}. Skipping SLA update.")
                continue
            
            cierre_esperado = fecha_esperada.fecha
            cierre_real = ticket.fechaticket_set.filter(tipo_fecha='Cierre').first()
            
            # Determine SLA status based on closure dates
            if cierre_real:
                print(f"ticket cerrado {ticket.id}")
                # Ticket is closed
                if cierre_real.fecha <= cierre_esperado:
                    new_sla_status = 'On Track'
                else:
                    new_sla_status = 'Breached'
            else:
                # Ticket is still open
                if now > cierre_esperado:
                    new_sla_status = 'Breached'
                elif now + timedelta(days=1) > cierre_esperado:
                    new_sla_status = 'At Risk'
                else:
                    new_sla_status = 'On Track'

            # Save updated SLA status if changed
            if ticket.sla_status != new_sla_status:
                ticket.sla_status = new_sla_status
                ticket.save()
                print(f"SLA status updated for Ticket ID {ticket.id}: {new_sla_status}")
            else:
                print(f"SLA status presents no changes for Ticket ID {ticket.id}: {ticket.sla_status}")

        except Exception as e:
            print(f"Error processing Ticket ID {ticket.id}: {str(e)}")

    if ticket_id:
        return f"SLA status checked and updated (if needed) for Ticket ID {ticket_id}"
    return f"SLA status checked and updated (if needed) for {tickets.count()} tickets"
