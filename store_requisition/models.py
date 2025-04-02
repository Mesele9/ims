from django.db import models
from django.utils import timezone
from users.models import CustomUser, Department
from inventory.models import Item

class StoreRequisition(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('checked', 'Checked'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('issued', 'Issued'),
        ('partially_issued', 'Partially Issued'),
    )
    
    requisition_no = models.CharField(max_length=20, unique=True, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sr_requested')
    requested_date = models.DateField()
    checked_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sr_checked')
    checked_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sr_approved')
    approved_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.requisition_no
    
    def save(self, *args, **kwargs):
        if not self.requisition_no:
            today = timezone.now().date()
            prefix = f"SR-{today.strftime('%Y%m')}-"
            last_sr = StoreRequisition.objects.filter(
                requisition_no__startswith=prefix
            ).order_by('-requisition_no').first()
            
            if last_sr:
                last_number = int(last_sr.requisition_no.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.requisition_no = f"{prefix}{new_number:04d}"
            
        super().save(*args, **kwargs)

class SRItem(models.Model):
    sr = models.ForeignKey(StoreRequisition, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    requested_qty = models.PositiveIntegerField()
    checked_qty = models.PositiveIntegerField(null=True, blank=True)
    approved_qty = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('sr', 'item')
    
    def __str__(self):
        return f"{self.sr.requisition_no} - {self.item.code}"

class StoreIssue(models.Model):
    siv_no = models.CharField(max_length=20, unique=True, editable=False)
    sr = models.ForeignKey(StoreRequisition, on_delete=models.CASCADE)
    date = models.DateField()
    prepared_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='siv_prepared')
    checked_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='siv_checked')
    issued_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='siv_issued')
    received_by = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.siv_no
    
    def save(self, *args, **kwargs):
        if not self.siv_no:
            today = timezone.now().date()
            prefix = f"SIV-{today.strftime('%Y%m')}-"
            last_siv = StoreIssue.objects.filter(
                siv_no__startswith=prefix
            ).order_by('-siv_no').first()
            
            if last_siv:
                last_number = int(last_siv.siv_no.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.siv_no = f"{prefix}{new_number:04d}"
            
        super().save(*args, **kwargs)

class SIVItem(models.Model):
    siv = models.ForeignKey(StoreIssue, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('siv', 'item')
    
    def __str__(self):
        return f"{self.siv.siv_no} - {self.item.code}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
