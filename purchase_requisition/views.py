from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from purchase_requisition.models import PurchaseRequisition, PRItem
from purchase_requisition.serializers import PurchaseRequisitionSerializer, PRItemSerializer
from django.shortcuts import get_object_or_404
from django.db import transaction

class PurchaseRequisitionViewSet(viewsets.ModelViewSet):
    queryset = PurchaseRequisition.objects.all().order_by('-created_at')
    serializer_class = PurchaseRequisitionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'requested_by', 'date']
    search_fields = ['pr_no']
    ordering_fields = ['pr_no', 'date', 'created_at']
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a purchase requisition"""
        requisition = self.get_object()
        
        # Validate status
        if requisition.status != 'pending_approval':
            return Response(
                {'detail': 'Only pending requisitions can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update requisition
        requisition.approved_by = request.user
        requisition.approved_date = request.data.get('approved_date')
        requisition.status = 'approved'
        requisition.save()
        
        # Update items
        items_data = request.data.get('items', [])
        for item_data in items_data:
            pr_item = get_object_or_404(PRItem, id=item_data.get('id'), pr=requisition)
            pr_item.quantity = item_data.get('quantity', pr_item.quantity)
            pr_item.unit_price = item_data.get('unit_price', pr_item.unit_price)
            pr_item.save()
        
        serializer = self.get_serializer(requisition)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a purchase requisition"""
        requisition = self.get_object()
        
        # Validate status
        if requisition.status != 'pending_approval':
            return Response(
                {'detail': 'Only pending requisitions can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update requisition
        requisition.rejected_by = request.user
        requisition.rejected_date = request.data.get('rejected_date')
        requisition.rejection_reason = request.data.get('rejection_reason')
        requisition.status = 'rejected'
        requisition.save()
        
        serializer = self.get_serializer(requisition)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def order(self, request, pk=None):
        """Mark a purchase requisition as ordered"""
        requisition = self.get_object()
        
        # Validate status
        if requisition.status != 'approved':
            return Response(
                {'detail': 'Only approved requisitions can be ordered.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update requisition
        requisition.status = 'ordered'
        requisition.save()
        
        serializer = self.get_serializer(requisition)
        return Response(serializer.data)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a purchase requisition with items"""
        # Extract nested items data
        items_data = request.data.pop('items', [])
        
        # Create purchase requisition
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        purchase_requisition = serializer.save()
        
        # Create items
        for item_data in items_data:
            item_data['pr'] = purchase_requisition.id
            item_serializer = PRItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()
        
        # Refresh and return the complete object
        purchase_requisition = self.get_queryset().get(id=purchase_requisition.id)
        serializer = self.get_serializer(purchase_requisition)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class PRItemViewSet(viewsets.ModelViewSet):
    queryset = PRItem.objects.all()
    serializer_class = PRItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pr', 'item']
