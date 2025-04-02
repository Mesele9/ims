from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from goods_receiving.models import GoodsReceivingNote, GRNItem
from inventory.models import Item, Supplier
from purchase_requisition.models import PurchaseRequisition
from users.models import CustomUser

@login_required
def grn_list(request):
    # Get filter parameters
    supplier_id = request.GET.get('supplier')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Base queryset
    grns = GoodsReceivingNote.objects.all()
    
    # Apply filters
    if supplier_id:
        grns = grns.filter(supplier_id=supplier_id)
    
    if date_from:
        grns = grns.filter(date__gte=date_from)
    
    if date_to:
        grns = grns.filter(date__lte=date_to)
    
    if search:
        grns = grns.filter(
            Q(grn_no__icontains=search) | 
            Q(invoice_no__icontains=search) |
            Q(supplier__name__icontains=search)
        )
    
    # Order by most recent first
    grns = grns.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(grns, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get suppliers for filter dropdown
    suppliers = Supplier.objects.all().order_by('name')
    
    context = {
        'grns': page_obj,
        'suppliers': suppliers,
    }
    
    return render(request, 'goods_receiving/grn_list.html', context)

@login_required
def grn_detail(request, pk):
    grn = get_object_or_404(GoodsReceivingNote, pk=pk)
    
    context = {
        'grn': grn,
    }
    
    return render(request, 'goods_receiving/grn_detail.html', context)

@login_required
def grn_create(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create goods receiving note
                grn = GoodsReceivingNote(
                    date=request.POST.get('date'),
                    supplier_id=request.POST.get('supplier'),
                    invoice_no=request.POST.get('invoice_no'),
                    pr_id=request.POST.get('pr') or None,
                    received_by=request.user,
                    checked_by=request.user  # Simplified for now
                )
                
                # Handle file upload if provided
                if 'receipt_file' in request.FILES:
                    grn.receipt_file = request.FILES['receipt_file']
                
                grn.save()
                
                # Process items
                items_data = []
                for key, value in request.POST.items():
                    if key.startswith('items[') and key.endswith('][item]'):
                        index = key.split('[')[1].split(']')[0]
                        item_id = value
                        quantity = request.POST.get(f'items[{index}][quantity]')
                        unit_price = request.POST.get(f'items[{index}][unit_price]')
                        
                        if item_id and quantity and unit_price:
                            items_data.append({
                                'item_id': item_id,
                                'quantity': quantity,
                                'unit_price': unit_price
                            })
                
                # Create GRN items
                for item_data in items_data:
                    total_price = float(item_data['quantity']) * float(item_data['unit_price'])
                    GRNItem.objects.create(
                        grn=grn,
                        item_id=item_data['item_id'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=total_price
                    )
                
                # If this is linked to a PR, update its status
                if grn.pr:
                    grn.pr.status = 'received'
                    grn.pr.save()
                
                messages.success(request, f'Goods Receiving Note {grn.grn_no} created successfully.')
                return redirect('grn_detail', pk=grn.id)
                
        except Exception as e:
            messages.error(request, f'Error creating goods receiving note: {str(e)}')
    
    # Get suppliers for dropdown
    suppliers = Supplier.objects.all().order_by('name')
    
    # Get ordered purchase requisitions for dropdown
    purchase_requisitions = PurchaseRequisition.objects.filter(status='ordered').order_by('-date')
    
    # Get items for dropdowns
    items = Item.objects.all().order_by('code')
    
    context = {
        'suppliers': suppliers,
        'purchase_requisitions': purchase_requisitions,
        'items': items,
        'today': timezone.now().date(),
    }
    
    return render(request, 'goods_receiving/grn_create.html', context)

@login_required
def grn_from_pr(request, pr_id):
    # Get the purchase requisition
    pr = get_object_or_404(PurchaseRequisition, pk=pr_id)
    
    # Check if PR is in ordered status
    if pr.status != 'ordered':
        messages.error(request, 'Only ordered purchase requisitions can be received.')
        return redirect('pr_detail', pk=pr_id)
    
    # Redirect to GRN create with PR pre-selected
    return redirect(f'/goods_receiving/create/?pr_id={pr_id}')

@login_required
def get_pr_items(request):
    """API endpoint to get PR items for GRN creation"""
    pr_id = request.GET.get('pr_id')
    
    if not pr_id:
        return JsonResponse({'error': 'PR ID is required'}, status=400)
    
    try:
        pr = PurchaseRequisition.objects.get(id=pr_id)
        items = []
        
        for item in pr.items.all():
            items.append({
                'id': item.id,
                'item_id': item.item_id,
                'item_code': item.item.code,
                'item_description': item.item.description,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'unit_of_measure': item.item.unit_of_measure.abbreviation
            })
        
        return JsonResponse({
            'pr_no': pr.pr_no,
            'date': pr.date.strftime('%Y-%m-%d'),
            'items': items
        })
    
    except PurchaseRequisition.DoesNotExist:
        return JsonResponse({'error': 'Purchase Requisition not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
