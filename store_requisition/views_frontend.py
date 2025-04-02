from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from store_requisition.models import StoreRequisition, SRItem, StoreIssue, SIVItem
from inventory.models import Item, Department
from users.models import CustomUser

@login_required
def sr_list(request):
    # Get filter parameters
    status = request.GET.get('status')
    department_id = request.GET.get('department')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Base queryset
    requisitions = StoreRequisition.objects.all()
    
    # Apply filters
    if status:
        requisitions = requisitions.filter(status=status)
    
    if department_id:
        requisitions = requisitions.filter(department_id=department_id)
    
    if date_from:
        requisitions = requisitions.filter(requested_date__gte=date_from)
    
    if date_to:
        requisitions = requisitions.filter(requested_date__lte=date_to)
    
    if search:
        requisitions = requisitions.filter(
            Q(requisition_no__icontains=search) | 
            Q(department__name__icontains=search)
        )
    
    # Order by most recent first
    requisitions = requisitions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requisitions, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get departments for filter dropdown
    departments = Department.objects.all().order_by('name')
    
    context = {
        'requisitions': page_obj,
        'departments': departments,
        'status_choices': StoreRequisition.STATUS_CHOICES,
    }
    
    return render(request, 'store_requisition/sr_list.html', context)

@login_required
def sr_detail(request, pk):
    requisition = get_object_or_404(StoreRequisition, pk=pk)
    
    # Get related store issues
    issues = StoreIssue.objects.filter(sr=requisition)
    
    context = {
        'requisition': requisition,
        'issues': issues,
    }
    
    return render(request, 'store_requisition/sr_detail.html', context)

@login_required
def sr_create(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create store requisition
                requisition = StoreRequisition(
                    department_id=request.POST.get('department'),
                    requested_by=request.user,
                    requested_date=timezone.now().date(),
                    delivery_date=request.POST.get('delivery_date'),
                    status='pending'
                )
                requisition.save()
                
                # Process items
                items_data = []
                for key, value in request.POST.items():
                    if key.startswith('items[') and key.endswith('][item]'):
                        index = key.split('[')[1].split(']')[0]
                        item_id = value
                        quantity = request.POST.get(f'items[{index}][quantity]')
                        
                        if item_id and quantity:
                            items_data.append({
                                'item_id': item_id,
                                'quantity': quantity
                            })
                
                # Create SR items
                for item_data in items_data:
                    SRItem.objects.create(
                        sr=requisition,
                        item_id=item_data['item_id'],
                        requested_qty=item_data['quantity']
                    )
                
                messages.success(request, f'Store Requisition {requisition.requisition_no} created successfully.')
                return redirect('sr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error creating store requisition: {str(e)}')
    
    # Get departments and items for dropdowns
    departments = Department.objects.all().order_by('name')
    items = Item.objects.filter(current_balance__gt=0).order_by('code')
    
    context = {
        'departments': departments,
        'items': items,
        'today': timezone.now().date(),
    }
    
    return render(request, 'store_requisition/sr_create.html', context)

@login_required
def sr_check(request, pk):
    requisition = get_object_or_404(StoreRequisition, pk=pk)
    
    # Check if user has permission to check requisitions
    if request.user.role not in ['admin', 'controller', 'manager']:
        messages.error(request, 'You do not have permission to check requisitions.')
        return redirect('sr_detail', pk=requisition.id)
    
    # Check if requisition is in pending status
    if requisition.status != 'pending':
        messages.error(request, 'Only pending requisitions can be checked.')
        return redirect('sr_detail', pk=requisition.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update requisition
                requisition.checked_by = request.user
                requisition.checked_date = timezone.now().date()
                requisition.status = 'checked'
                requisition.save()
                
                # Process items
                for item in requisition.items.all():
                    checked_qty = request.POST.get(f'item_{item.id}_checked_qty')
                    if checked_qty:
                        item.checked_qty = checked_qty
                        item.save()
                
                messages.success(request, f'Store Requisition {requisition.requisition_no} checked successfully.')
                return redirect('sr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error checking store requisition: {str(e)}')
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'store_requisition/sr_check.html', context)

@login_required
def sr_approve(request, pk):
    requisition = get_object_or_404(StoreRequisition, pk=pk)
    
    # Check if user has permission to approve requisitions
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to approve requisitions.')
        return redirect('sr_detail', pk=requisition.id)
    
    # Check if requisition is in pending or checked status
    if requisition.status not in ['pending', 'checked']:
        messages.error(request, 'Only pending or checked requisitions can be approved.')
        return redirect('sr_detail', pk=requisition.id)
    
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
                    approved_qty = request.POST.get(f'item_{item.id}_approved_qty')
                    if approved_qty:
                        item.approved_qty = approved_qty
                        item.save()
                
                messages.success(request, f'Store Requisition {requisition.requisition_no} approved successfully.')
                return redirect('sr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error approving store requisition: {str(e)}')
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'store_requisition/sr_approve.html', context)

@login_required
def sr_reject(request, pk):
    requisition = get_object_or_404(StoreRequisition, pk=pk)
    
    # Check if user has permission to reject requisitions
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'You do not have permission to reject requisitions.')
        return redirect('sr_detail', pk=requisition.id)
    
    # Check if requisition is in pending or checked status
    if requisition.status not in ['pending', 'checked']:
        messages.error(request, 'Only pending or checked requisitions can be rejected.')
        return redirect('sr_detail', pk=requisition.id)
    
    if request.method == 'POST':
        try:
            # Update requisition
            requisition.status = 'rejected'
            requisition.save()
            
            messages.success(request, f'Store Requisition {requisition.requisition_no} rejected successfully.')
            return redirect('sr_detail', pk=requisition.id)
                
        except Exception as e:
            messages.error(request, f'Error rejecting store requisition: {str(e)}')
    
    context = {
        'requisition': requisition,
    }
    
    return render(request, 'store_requisition/sr_reject.html', context)

@login_required
def siv_create(request, sr_id=None):
    # If sr_id is provided, get the store requisition
    sr = None
    if sr_id:
        sr = get_object_or_404(StoreRequisition, pk=sr_id)
        
        # Check if requisition is approved
        if sr.status != 'approved':
            messages.error(request, 'Only approved requisitions can be issued.')
            return redirect('sr_detail', pk=sr_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Create store issue
                store_issue = StoreIssue(
                    sr_id=request.POST.get('sr'),
                    date=timezone.now().date(),
                    prepared_by=request.user,
                    checked_by=request.user,  # Simplified for now
                    issued_by=request.user,   # Simplified for now
                    received_by=request.POST.get('received_by')
                )
                store_issue.save()
                
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
                
                # Create SIV items
                for item_data in items_data:
                    SIVItem.objects.create(
                        siv=store_issue,
                        item_id=item_data['item_id'],
                        quantity=item_data['quantity'],
                        unit_price=item_data['unit_price'],
                        total_price=float(item_data['quantity']) * float(item_data['unit_price'])
                    )
                
                messages.success(request, f'Store Issue Voucher {store_issue.siv_no} created successfully.')
                return redirect('siv_detail', pk=store_issue.id)
                
        except Exception as e:
            messages.error(request, f'Error creating store issue voucher: {str(e)}')
    
    # Get approved requisitions for dropdown
    approved_requisitions = StoreRequisition.objects.filter(status='approved').order_by('-created_at')
    
    # Get items with stock for dropdowns
    items = Item.objects.filter(current_balance__gt=0).order_by('code')
    
    context = {
        'sr': sr,
        'approved_requisitions': approved_requisitions,
        'items': items,
    }
    
    return render(request, 'store_requisition/siv_create.html', context)

@login_required
def siv_list(request):
    # Get filter parameters
    sr_id = request.GET.get('sr')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    # Base queryset
    issues = StoreIssue.objects.all()
    
    # Apply filters
    if sr_id:
        issues = issues.filter(sr_id=sr_id)
    
    if date_from:
        issues = issues.filter(date__gte=date_from)
    
    if date_to:
        issues = issues.filter(date__lte=date_to)
    
    if search:
        issues = issues.filter(
            Q(siv_no__icontains=search) | 
            Q(sr__requisition_no__icontains=search) |
            Q(sr__department__name__icontains=search)
        )
    
    # Order by most recent first
    issues = issues.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(issues, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'issues': page_obj,
    }
    
    return render(request, 'store_requisition/siv_list.html', context)

@login_required
def siv_detail(request, pk):
    issue = get_object_or_404(StoreIssue, pk=pk)
    
    context = {
        'issue': issue,
    }
    
    return render(request, 'store_requisition/siv_detail.html', context)

@login_required
def sr_pending(request):
    # Get requisitions that need action based on user role
    user_role = request.user.role
    
    if user_role == 'controller':
        # Controllers see pending requisitions
        requisitions = StoreRequisition.objects.filter(status='pending')
    elif user_role in ['admin', 'manager']:
        # Managers see checked requisitions and pending requisitions
        requisitions = StoreRequisition.objects.filter(
            Q(status='checked') | Q(status='pending')
        )
    elif user_role == 'store_keeper':
        # Store keepers see approved requisitions
        requisitions = StoreRequisition.objects.filter(status='approved')
    else:
        # Staff see their own pending requisitions
        requisitions = StoreRequisition.objects.filter(
            requested_by=request.user
        ).exclude(status__in=['issued', 'rejected'])
    
    # Order by most recent first
    requisitions = requisitions.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(requisitions, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requisitions': page_obj,
        'title': 'Pending Requisitions',
    }
    
    return render(request, 'store_requisition/sr_pending.html', context)

@login_required
def sr_approved(request):
    # Get approved requisitions
    requisitions = StoreRequisition.objects.filter(status='approved')
    
    # Order by most recent first
    requisitions = requisitions.order_by('-approved_date')
    
    # Pagination
    paginator = Paginator(requisitions, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requisitions': page_obj,
        'title': 'Approved Requisitions',
    }
    
    return render(request, 'store_requisition/sr_approved.html', context)
