from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from purchase_requisition.models import PurchaseRequisition, PRItem
from inventory.models import Item, Supplier
from users.models import CustomUser

@login_required
def pr_list(request):
    # Get filter parameters
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Base queryset
    requisitions = PurchaseRequisition.objects.all()
    
    # Apply filters
    if status:
        requisitions = requisitions.filter(status=status)
    
    if date_from:
        requisitions = requisitions.filter(date__gte=date_from)
    
    if date_to:
        requisitions = requisitions.filter(date__lte=date_to)
    
    if search:
        requisitions = requisitions.filter(
            Q(pr_no__icontains=search) | 
            Q(notes__icontains=search)
        )
    
    # Order by most recent first
    requisitions = requisitions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requisitions, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requisitions': page_obj,
        'status_choices': PurchaseRequisition.STATUS_CHOICES,
    }
    
    return render(request, 'purchase_requisition/pr_list.html', context)

@login_required
def pr_detail(request, pk):
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'purchase_requisition/pr_detail.html', context)

@login_required
def pr_create(request, item_id=None):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create purchase requisition
                requisition = PurchaseRequisition(
                    date=request.POST.get('date'),
                    requested_by=request.user,
                    notes=request.POST.get('notes'),
                    status='pending_approval'
                )
                requisition.save()
                
                # Process items
                items_data = []
                for key, value in request.POST.items():
                    if key.startswith('items[') and key.endswith('][item]'):
                        index = key.split('[')[1].split(']')[0]
                        item_id = value
                        quantity = request.POST.get(f'items[{index}][quantity]')
                        unit_price = request.POST.get(f'items[{index}][unit_price]')
                        
                        if item_id and quantity:
                            items_data.append({
                                'item_id': item_id,
                                'quantity': quantity,
                                'unit_price': unit_price or 0
                            })
                
                # Create PR items
                for item_data in items_data:
                    total_price = float(item_data['quantity']) * float(item_data['unit_price']) if item_data['unit_price'] else None
                    PRItem.objects.create(
                        pr=requisition,
                        item_id=item_data['item_id'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'] or None,
                        total_price=total_price
                    )
                
                messages.success(request, f'Purchase Requisition {requisition.pr_no} created successfully.')
                return redirect('pr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error creating purchase requisition: {str(e)}')
    
    # Get items for dropdowns
    items = Item.objects.all().order_by('code')
    
    # If item_id is provided (from low stock alert), get the item
    selected_item = None
    if item_id:
        selected_item = get_object_or_404(Item, pk=item_id)
    
    context = {
        'items': items,
        'selected_item': selected_item,
        'today': timezone.now().date(),
    }
    
    return render(request, 'purchase_requisition/pr_create.html', context)

@login_required
def pr_approve(request, pk):
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    
    # Check if user has permission to approve requisitions
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to approve requisitions.')
        return redirect('pr_detail', pk=requisition.id)
    
    # Check if requisition is in pending status
    if requisition.status != 'pending_approval':
        messages.error(request, 'Only pending requisitions can be approved.')
        return redirect('pr_detail', pk=requisition.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update requisition
                requisition.approved_by = request.user
                requisition.approved_date = timezone.now().date()
                requisition.status = 'approved'
                requisition.save()
                
                # Process items
                for item in requisition.items.all():
                    quantity = request.POST.get(f'item_{item.id}_quantity')
                    unit_price = request.POST.get(f'item_{item.id}_unit_price')
                    
                    if quantity and unit_price:
                        item.quantity = quantity
                        item.unit_price = unit_price
                        item.total_price = float(quantity) * float(unit_price)
                        item.save()
                
                messages.success(request, f'Purchase Requisition {requisition.pr_no} approved successfully.')
                return redirect('pr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error approving purchase requisition: {str(e)}')
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'purchase_requisition/pr_approve.html', context)

@login_required
def pr_reject(request, pk):
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    
    # Check if user has permission to reject requisitions
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to reject requisitions.')
        return redirect('pr_detail', pk=requisition.id)
    
    # Check if requisition is in pending status
    if requisition.status != 'pending_approval':
        messages.error(request, 'Only pending requisitions can be rejected.')
        return redirect('pr_detail', pk=requisition.id)
    
    if request.method == 'POST':
        try:
            # Update requisition
            requisition.rejected_by = request.user
            requisition.rejected_date = timezone.now().date()
            requisition.rejection_reason = request.POST.get('rejection_reason')
            requisition.status = 'rejected'
            requisition.save()
            
            messages.success(request, f'Purchase Requisition {requisition.pr_no} rejected successfully.')
            return redirect('pr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error rejecting purchase requisition: {str(e)}')
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'purchase_requisition/pr_reject.html', context)

@login_required
def pr_order(request, pk):
    requisition = get_object_or_404(PurchaseRequisition, pk=pk)
    
    # Check if user has permission to mark as ordered
    if request.user.role not in ['admin', 'manager', 'procurement']:
        messages.error(request, 'You do not have permission to mark requisitions as ordered.')
        return redirect('pr_detail', pk=requisition.id)
    
    # Check if requisition is in approved status
    if requisition.status != 'approved':
        messages.error(request, 'Only approved requisitions can be marked as ordered.')
        return redirect('pr_detail', pk=requisition.id)
    
    if request.method == 'POST':
        try:
            # Update requisition
            requisition.status = 'ordered'
            requisition.order_date = timezone.now().date()
            requisition.save()
            
            messages.success(request, f'Purchase Requisition {requisition.pr_no} marked as ordered successfully.')
            return redirect('pr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error marking purchase requisition as ordered: {str(e)}')
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'purchase_requisition/pr_order.html', context)

@login_required
def pr_pending(request):
    # Get requisitions that need action based on user role
    user_role = request.user.role
    
    if user_role in ['admin', 'manager']:
        # Managers see pending approval requisitions
        requisitions = PurchaseRequisition.objects.filter(status='pending_approval')
    elif user_role == 'procurement':
        # Procurement sees approved requisitions
        requisitions = PurchaseRequisition.objects.filter(status='approved')
    else:
        # Staff see their own pending requisitions
        requisitions = PurchaseRequisition.objects.filter(
            requested_by=request.user
        ).exclude(status__in=['received', 'rejected'])
    
    # Order by most recent first
    requisitions = requisitions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requisitions, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requisitions': page_obj,
        'title': 'Pending Purchase Requisitions',
    }
    
    return render(request, 'purchase_requisition/pr_pending.html', context)

@login_required
def pr_create_for_item(request, item_id):
    # Redirect to PR create with item_id
    return redirect('pr_create', item_id=item_id)
