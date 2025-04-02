from rest_framework import serializers
from goods_receiving.models import GoodsReceivingNote, GRNItem
from inventory.serializers import ItemSerializer, SupplierSerializer

class GRNItemSerializer(serializers.ModelSerializer):
    item_details = ItemSerializer(source='item', read_only=True)
    item_code = serializers.ReadOnlyField(source='item.code')
    item_description = serializers.ReadOnlyField(source='item.description')
    unit_of_measure = serializers.ReadOnlyField(source='item.unit_of_measure.abbreviation')
    
    class Meta:
        model = GRNItem
        fields = '__all__'

class GoodsReceivingNoteSerializer(serializers.ModelSerializer):
    items = GRNItemSerializer(many=True, read_only=True)
    supplier_details = SupplierSerializer(source='supplier', read_only=True)
    pr_no = serializers.ReadOnlyField(source='pr.pr_no')
    received_by_name = serializers.ReadOnlyField(source='received_by.get_full_name')
    checked_by_name = serializers.ReadOnlyField(source='checked_by.get_full_name')
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = GoodsReceivingNote
        fields = '__all__'
        read_only_fields = ['grn_no']
    
    def get_total_amount(self, obj):
        total = sum(item.total_price for item in obj.items.all())
        return total
