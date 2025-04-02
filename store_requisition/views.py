from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from store_requisition.models import StoreRequisition, SRItem, StoreIssue, SIVItem
from store_requisition.serializers import (
    StoreRequisitionSerializer, SRItemSerializer, 
    StoreIssueSerializer, SIVItemSerializer
)
from django.shortcuts import get_object_or_404
from django.db import transaction

class StoreRequisitionViewSet(viewsets.ModelViewSet):
    queryset = StoreRequisition.objects.all().order_by('-created_at')
    serializer_class = StoreRequisitionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'status', 'requested_by', 'requested_date']
    search_fields = ['requisition_no', 'department__name']
    ordering_fields = ['requisition_no', 'requested_date', 'created_at']
    
    @action(detail=True, methods=['post'])
    def check(self, request, pk=None):
        """Check a store requisition"""
        requisition = self.get_object()
        
        # Validate status
        if requisition.status != 'pending':
            return Response(
                {'detail': 'Only pending requisitions can be checked.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update requisition
        requisition.checked_by = request.user
        requisition.checked_date = request.data.get('checked_date')
        requisition.status = 'checked'
        requisition.save()
        
        # Update items
        items_data = request.data.get('items', [])
        for item_data in items_data:
            sr_item = get_object_or_404(SRItem, id=item_data.get('id'), sr=requisition)
            sr_item.checked_qty = item_data.get('checked_qty', sr_item.requested_qty)
            sr_item.save()
        
        serializer = self.get_serializer(requisition)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a store requisition"""
        requisition = self.get_object()
        
        # Validate status
        if requisition.status not in ['pending', 'checked']:
            return Response(
                {'detail': 'Only pending or checked requisitions can be approved.'},
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
            sr_item = get_object_or_404(SRItem, id=item_data.get('id'), sr=requisition)
            sr_item.approved_qty = item_data.get('approved_qty', sr_item.checked_qty or sr_item.requested_qty)
            sr_item.save()
        
        serializer = self.get_serializer(requisition)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a store requisition"""
        requisition = self.get_object()
        
        # Validate status
        if requisition.status not in ['pending', 'checked']:
            return Response(
                {'detail': 'Only pending or checked requisitions can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update requisition
        requisition.status = 'rejected'
        requisition.save()
        
        serializer = self.get_serializer(requisition)
        return Response(serializer.data)

class SRItemViewSet(viewsets.ModelViewSet):
    queryset = SRItem.objects.all()
    serializer_class = SRItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sr', 'item']

class StoreIssueViewSet(viewsets.ModelViewSet):
    queryset = StoreIssue.objects.all().order_by('-created_at')
    serializer_class = StoreIssueSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['sr', 'date', 'prepared_by']
    search_fields = ['siv_no', 'sr__requisition_no']
    ordering_fields = ['siv_no', 'date', 'created_at']
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a store issue with items"""
        # Extract nested items data
        items_data = request.data.pop('items', [])
        
        # Create store issue
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store_issue = serializer.save()
        
        # Create items
        for item_data in items_data:
            item_data['siv'] = store_issue.id
            item_serializer = SIVItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()
        
        # Refresh and return the complete object
        store_issue = self.get_object()
        serializer = self.get_serializer(store_issue)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SIVItemViewSet(viewsets.ModelViewSet):
    queryset = SIVItem.objects.all()
    serializer_class = SIVItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['siv', 'item']
