from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from core.contracts.models import ElectricityContract, ContractStatus
from .models import SwitchRequest, SwitchStatus

@receiver(post_save, sender=ElectricityContract)
def on_contract_status_change(sender, instance, created, **kwargs):
    """
    Trigger the creation of a SwitchRequest when a contract is ready.
    """
    if instance.status == ContractStatus.READY and not hasattr(instance, 'switch_request'):
        # To prevent recursion, we check if the status was already READY
        # A more robust solution would be to use django-dirtyfields
        try:
            old_instance = ElectricityContract.objects.get(pk=instance.pk)
            if old_instance.status == ContractStatus.READY:
                return
        except ElectricityContract.DoesNotExist:
            pass # This is a new contract, so the status wasn't READY before

        instance.ready_at = timezone.now()
        
        # This is a placeholder for getting the traders.
        # In a real implementation, this would involve a more complex lookup.
        gaining_trader = instance.tenant
        losing_trader = instance.tenant 

        SwitchRequest.objects.create(
            contract=instance,
            gaining_trader=gaining_trader,
            losing_trader=losing_trader,
            status=SwitchStatus.INITIATED
        )
        instance.status = ContractStatus.SWITCH_GAIN
        instance.save(update_fields=['status', 'ready_at'])

        # TODO: Trigger Airflow DAG
        # from .tasks import trigger_gain_customer_switch_dag
        # trigger_gain_customer_switch_dag.delay(switch_request_id=switch_request.id) 