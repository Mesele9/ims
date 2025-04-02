from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from inventory.models import Category, UnitOfMeasure, Item, ItemTransaction, Supplier
from inventory.serializers import (
    CategorySerializer, UnitOfMeasureSerializer, ItemSerializer,
    ItemTransactionSerializer, SupplierSerializer
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

class UnitOfMeasureViewSet(viewsets.ModelViewSet):
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviation']
    ordering_fields = ['name', 'created_at']

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'unit_of_measure']
    search_fields = ['code', 'description']
    ordering_fields = ['code', 'description', 'current_price', 'current_balance', 'created_at']
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Return items with stock levels below minimum"""
        low_stock_items = Item.objects.filter(current_balance__lte=models.F('min_stock_level'))
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Return transaction history for an item"""
        item = self.get_object()
        transactions = ItemTransaction.objects.filter(item=item).order_by('-date', '-created_at')
        serializer = ItemTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class ItemTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ItemTransaction.objects.all().order_by('-date', '-created_at')
    serializer_class = ItemTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['item', 'transaction_type', 'date']
    search_fields = ['item__code', 'item__description']
    ordering_fields = ['date', 'created_at', 'quantity_in', 'quantity_out', 'balance_after']

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_person', 'email', 'phone']
    ordering_fields = ['name', 'created_at']
