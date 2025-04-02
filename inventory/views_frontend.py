from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.core.paginator import Paginator

from inventory.models import Item, Category, ItemTransaction
from store_requisition.models import StoreRequisition
from goods_receiving.models import GoodsReceivingNote

@login_required
def dashboard(request):
    # Get counts and summary data
    total_items = Item.objects.count()
    low_stock_items = Item.objects.filter(current_balance__lte=F('min_stock_level'))
    low_stock_count = low_stock_items.count()
    
    # Calculate inventory value
    inventory_value = Item.objects.aggregate(
        total_value=Sum(F('current_balance') * F('current_price'))
    )['total_value'] or 0
    
    # Get pending requisitions
    pending_requisitions = StoreRequisition.objects.filter(
        Q(status='pending') | Q(status='checked')
    ).count()
    
    # Get recent requisitions
    recent_requisitions = StoreRequisition.objects.order_by('-created_at')[:5]
    
    # Get recent goods receiving notes
    recent_grns = GoodsReceivingNote.objects.order_by('-created_at')[:5]
    
    # Get top 5 low stock items for display
    low_stock_display = low_stock_items.order_by('current_balance')[:5]
    
    context = {
        'total_items': total_items,
        'low_stock_count': low_stock_count,
        'pending_requisitions': pending_requisitions,
        'inventory_value': inventory_value,
        'recent_requisitions': recent_requisitions,
        'recent_grns': recent_grns,
        'low_stock_items': low_stock_display,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def item_list(request):
    # Get filter parameters
    category_id = request.GET.get('category')
    low_stock = request.GET.get('low_stock')
    search = request.GET.get('search')
    
    # Base queryset
    items = Item.objects.all()
    
    # Apply filters
    if category_id:
        items = items.filter(category_id=category_id)
    
    if low_stock == 'true':
        items = items.filter(current_balance__lte=F('min_stock_level'))
    
    if search:
        items = items.filter(
            Q(code__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Order by code
    items = items.order_by('code')
    
    # Pagination
    paginator = Paginator(items, 10)  # Show 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = Category.objects.all().order_by('name')
    
    context = {
        'items': page_obj,
        'categories': categories,
    }
    
    return render(request, 'inventory/item_list.html', context)

@login_required
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    # Get transaction history
    transactions = ItemTransaction.objects.filter(item=item).order_by('-date', '-created_at')
    
    context = {
        'item': item,
        'transactions': transactions,
    }
    
    return render(request, 'inventory/item_detail.html', context)

@login_required
def item_create(request):
    if request.method == 'POST':
        # Process form data
        # This would be implemented with proper form validation
        pass
    
    # Get categories and units of measure for dropdowns
    categories = Category.objects.all().order_by('name')
    units = UnitOfMeasure.objects.all().order_by('name')
    
    context = {
        'categories': categories,
        'units': units,
    }
    
    return render(request, 'inventory/item_form.html', context)

@login_required
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    if request.method == 'POST':
        # Process form data
        # This would be implemented with proper form validation
        pass
    
    # Get categories and units of measure for dropdowns
    categories = Category.objects.all().order_by('name')
    units = UnitOfMeasure.objects.all().order_by('name')
    
    context = {
        'item': item,
        'categories': categories,
        'units': units,
    }
    
    return render(request, 'inventory/item_form.html', context)
