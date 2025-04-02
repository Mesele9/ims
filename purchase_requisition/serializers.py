from rest_framework import serializers
from purchase_requisition.models import PurchaseRequisition, PRItem
from inventory.serializers import ItemSerializer

class PRItemSerializer(serializers.ModelSerializer):
    item_details = ItemSerializer(source='item', read_only=True)
    item_code = serializers.ReadOnlyField(source='item.code')
    item_description = serializers.ReadOnlyField(source='item.description')
    unit_of_measure = serializers.ReadOnlyField(source='item.unit_of_measure.abbreviation')
    
    class Meta:
        model = PRItem
        fields = '__all__'

class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    items = PRItemSerializer(many=True, read_only=True)
    requested_by_name = serializers.ReadOnlyField(source='requested_by.get_full_name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name')
    rejected_by_name = serializers.ReadOnlyField(source='rejected_by.get_full_name')
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseRequisition
        fields = '__all__'
        read_only_fields = ['pr_no']
    
    def get_total_amount(self, obj):
        total = sum(item.total_price or 0 for item in obj.items.all())
        return total
