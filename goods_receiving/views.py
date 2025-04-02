from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from goods_receiving.models import GoodsReceivingNote, GRNItem
from goods_receiving.serializers import GoodsReceivingNoteSerializer, GRNItemSerializer
from purchase_requisition.models import PurchaseRequisition
from django.shortcuts import get_object_or_404
from django.db import transaction

class GoodsReceivingNoteViewSet(viewsets.ModelViewSet):
    queryset = GoodsReceivingNote.objects.all().order_by('-created_at')
    serializer_class = GoodsReceivingNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'date', 'received_by', 'pr']
    search_fields = ['grn_no', 'invoice_no', 'supplier__name']
    ordering_fields = ['grn_no', 'date', 'created_at']
    
    @action(detail=False, methods=['get'])
    def from_pr(self, request):
        """Get purchase requisition details for creating a GRN"""
        pr_id = request.query_params.get('pr_id')
        if not pr_id:
            return Response(
                {'detail': 'PR ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pr = get_object_or_404(PurchaseRequisition, id=pr_id)
        
        # Validate PR status
        if pr.status != 'ordered':
            return Response(
                {'detail': 'Only ordered purchase requisitions can be received.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return PR details for GRN creation
        from purchase_requisition.serializers import PurchaseRequisitionSerializer
        serializer = PurchaseRequisitionSerializer(pr)
        return Response(serializer.data)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a goods receiving note with items"""
        # Extract nested items data
        items_data = request.data.pop('items', [])
        
        # Create goods receiving note
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grn = serializer.save()
        
        # Create items
        for item_data in items_data:
            item_data['grn'] = grn.id
            item_serializer = GRNItemSerializer(data=item_data)
            item_serializer.is_valid(raise_exception=True)
            item_serializer.save()
        
        # Refresh and return the complete object
        grn = self.get_queryset().get(id=grn.id)
        serializer = self.get_serializer(grn)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GRNItemViewSet(viewsets.ModelViewSet):
    queryset = GRNItem.objects.all()
    serializer_class = GRNItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['grn', 'item']
