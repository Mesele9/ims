from django.db import models
from django.utils import timezone
from users.models import CustomUser
from inventory.models import Item, Supplier
from purchase_requisition.models import PurchaseRequisition

class GoodsReceivingNote(models.Model):
    grn_no = models.CharField(max_length=20, unique=True, editable=False)
    pr = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    invoice_no = models.CharField(max_length=50, blank=True, null=True)
    date = models.DateField()
    received_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='grn_received')
    checked_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='grn_checked')
    receipt_file = models.FileField(upload_to='receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.grn_no
    
    def save(self, *args, **kwargs):
        if not self.grn_no:
            today = timezone.now().date()
            prefix = f"GRN-{today.strftime('%Y%m')}-"
            last_grn = GoodsReceivingNote.objects.filter(
                grn_no__startswith=prefix
            ).order_by('-grn_no').first()
            
            if last_grn:
                last_number = int(last_grn.grn_no.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.grn_no = f"{prefix}{new_number:04d}"
            
        # Update PR status to 'received' if PR is provided
        if self.pr and self.pr.status == 'ordered':
            self.pr.status = 'received'
            self.pr.save()
            
        super().save(*args, **kwargs)

class GRNItem(models.Model):
    grn = models.ForeignKey(GoodsReceivingNote, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('grn', 'item')
    
    def __str__(self):
        return f"{self.grn.grn_no} - {self.item.code}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
