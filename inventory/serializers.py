from rest_framework import serializers
from inventory.models import Category, UnitOfMeasure, Item, ItemTransaction, Supplier

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    unit_of_measure_name = serializers.ReadOnlyField(source='unit_of_measure.abbreviation')
    is_low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Item
        fields = '__all__'

class ItemTransactionSerializer(serializers.ModelSerializer):
    item_code = serializers.ReadOnlyField(source='item.code')
    item_description = serializers.ReadOnlyField(source='item.description')
    created_by_name = serializers.ReadOnlyField(source='created_by.get_full_name')
    
    class Meta:
        model = ItemTransaction
        fields = '__all__'

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
