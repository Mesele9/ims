from rest_framework import serializers
from store_requisition.models import StoreRequisition, SRItem, StoreIssue, SIVItem
from inventory.serializers import ItemSerializer

class SRItemSerializer(serializers.ModelSerializer):
    item_details = ItemSerializer(source='item', read_only=True)
    item_code = serializers.ReadOnlyField(source='item.code')
    item_description = serializers.ReadOnlyField(source='item.description')
    unit_of_measure = serializers.ReadOnlyField(source='item.unit_of_measure.abbreviation')
    current_balance = serializers.ReadOnlyField(source='item.current_balance')
    
    class Meta:
        model = SRItem
        fields = '__all__'

class StoreRequisitionSerializer(serializers.ModelSerializer):
    items = SRItemSerializer(many=True, read_only=True)
    department_name = serializers.ReadOnlyField(source='department.name')
    requested_by_name = serializers.ReadOnlyField(source='requested_by.get_full_name')
    checked_by_name = serializers.ReadOnlyField(source='checked_by.get_full_name')
    approved_by_name = serializers.ReadOnlyField(source='approved_by.get_full_name')
    
    class Meta:
        model = StoreRequisition
        fields = '__all__'
        read_only_fields = ['requisition_no']

class SIVItemSerializer(serializers.ModelSerializer):
    item_details = ItemSerializer(source='item', read_only=True)
    item_code = serializers.ReadOnlyField(source='item.code')
    item_description = serializers.ReadOnlyField(source='item.description')
    unit_of_measure = serializers.ReadOnlyField(source='item.unit_of_measure.abbreviation')
    
    class Meta:
        model = SIVItem
        fields = '__all__'

class StoreIssueSerializer(serializers.ModelSerializer):
    items = SIVItemSerializer(many=True, read_only=True)
    sr_no = serializers.ReadOnlyField(source='sr.requisition_no')
    department_name = serializers.ReadOnlyField(source='sr.department.name')
    prepared_by_name = serializers.ReadOnlyField(source='prepared_by.get_full_name')
    checked_by_name = serializers.ReadOnlyField(source='checked_by.get_full_name')
    issued_by_name = serializers.ReadOnlyField(source='issued_by.get_full_name')
    
    class Meta:
        model = StoreIssue
        fields = '__all__'
        read_only_fields = ['siv_no']
