from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from inventory.models import Item, ItemTransaction
from store_requisition.models import SIVItem, StoreIssue
from goods_receiving.models import GRNItem

@receiver(post_save, sender=GRNItem)
def update_inventory_on_grn_save(sender, instance, created, **kwargs):
    """
    Signal to update inventory when a GRN item is saved
    """
    if created:  # Only run this for new items
        # Create an item transaction record
        transaction = ItemTransaction(
            item=instance.item,
            transaction_type='purchase',
            reference_id=instance.grn.id,
            reference_type='GRN',
            quantity_in=instance.quantity,
            quantity_out=0,
            balance_after=instance.item.current_balance + instance.quantity,
            unit_price=instance.unit_price,
            total_price=instance.total_price,
            date=instance.grn.date,
            created_by=instance.grn.received_by
        )
        transaction.save()
        
        # Update item balance and price (weighted average)
        item = instance.item
        if item.current_balance == 0:
            # If current balance is 0, just use the new price
            item.current_price = instance.unit_price
        else:
            # Calculate weighted average price
            total_value = (item.current_balance * item.current_price) + (instance.quantity * instance.unit_price)
            total_quantity = item.current_balance + instance.quantity
            item.current_price = total_value / total_quantity
        
        item.current_balance += instance.quantity
        item.save()

@receiver(post_save, sender=SIVItem)
def update_inventory_on_siv_save(sender, instance, created, **kwargs):
    """
    Signal to update inventory when a SIV item is saved
    """
    if created:  # Only run this for new items
        # Create an item transaction record
        transaction = ItemTransaction(
            item=instance.item,
            transaction_type='issue',
            reference_id=instance.siv.id,
            reference_type='SIV',
            quantity_in=0,
            quantity_out=instance.quantity,
            balance_after=instance.item.current_balance - instance.quantity,
            unit_price=instance.unit_price,
            total_price=instance.total_price,
            date=instance.siv.date,
            created_by=instance.siv.prepared_by
        )
        transaction.save()
        
        # Update item balance
        item = instance.item
        item.current_balance -= instance.quantity
        item.save()

@receiver(post_save, sender=StoreIssue)
def update_store_requisition_status(sender, instance, created, **kwargs):
    """
    Signal to update store requisition status when a store issue is created
    """
    if created:
        # Get the store requisition
        sr = instance.sr
        
        # Check if all items in the SR have been issued
        sr_items = sr.items.all()
        siv_items = instance.items.all()
        
        # If all items have been issued with the full quantity, mark as 'issued'
        # Otherwise, mark as 'partially_issued'
        all_issued = True
        
        for sr_item in sr_items:
            approved_qty = sr_item.approved_qty or sr_item.checked_qty or sr_item.requested_qty
            issued_qty = 0
            
            # Sum up all issued quantities for this item
            for siv_item in siv_items:
                if siv_item.item == sr_item.item:
                    issued_qty += siv_item.quantity
            
            if issued_qty < approved_qty:
                all_issued = False
                break
        
        sr.status = 'issued' if all_issued else 'partially_issued'
        sr.save()
