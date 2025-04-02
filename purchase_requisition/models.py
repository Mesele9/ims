from django.db import models
from django.utils import timezone
from users.models import CustomUser
from inventory.models import Item, Supplier

class PurchaseRequisition(models.Model):
    STATUS_CHOICES = (
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
    )
    
    pr_no = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_approval')
    requested_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='pr_requested')
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='pr_approved')
    approved_date = models.DateField(null=True, blank=True)
    rejected_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='pr_rejected')
    rejected_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.pr_no
    
    def save(self, *args, **kwargs):
        if not self.pr_no:
            today = timezone.now().date()
            prefix = f"PR-{today.strftime('%Y%m')}-"
            last_pr = PurchaseRequisition.objects.filter(
                pr_no__startswith=prefix
            ).order_by('-pr_no').first()
            
            if last_pr:
                last_number = int(last_pr.pr_no.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.pr_no = f"{prefix}{new_number:04d}"
            
        super().save(*args, **kwargs)

class PRItem(models.Model):
    pr = models.ForeignKey(PurchaseRequisition, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('pr', 'item')
    
    def __str__(self):
        return f"{self.pr.pr_no} - {self.item.code}"
    
    def save(self, *args, **kwargs):
        if self.unit_price and self.quantity:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
