from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
import csv
import io
from datetime import datetime, timedelta
import json

from inventory.models import Item, ItemTransaction, Category, UnitOfMeasure
from store_requisition.models import StoreRequisition, StoreIssue
from purchase_requisition.models import PurchaseRequisition
from goods_receiving.models import GoodsReceivingNote
from users.models import Department

@login_required
def report_inventory(request):
    """Inventory Status Report"""
    # Get filter parameters
    category_id = request.GET.get('category')
    low_stock = request.GET.get('low_stock')
    search = request.GET.get('search')
    export = request.GET.get('export')
    
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
    
    # Export to CSV if requested
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Code', 'Description', 'Category', 'UoM', 'Current Stock', 'Min Stock', 'Current Price', 'Value', 'Status'])
        
        for item in items:
            status = 'Low Stock' if item.is_low_stock else 'Normal'
            if item.current_balance == 0:
                status = 'Out of Stock'
                
            writer.writerow([
                item.code,
                item.description,
                item.category.name,
                item.unit_of_measure.abbreviation,
                item.current_balance,
                item.min_stock_level,
                item.current_price,
                item.current_balance * item.current_price,
                status
            ])
        
        return response
    
    # Get all categories for filter dropdown
    categories = Category.objects.all().order_by('name')
    
    # Calculate summary statistics
    total_items = items.count()
    total_value = sum(item.current_balance * item.current_price for item in items)
    low_stock_count = sum(1 for item in items if item.is_low_stock)
    out_of_stock_count = sum(1 for item in items if item.current_balance == 0)
    
    # Pagination
    paginator = Paginator(items, 20)  # Show 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'items': page_obj,
        'categories': categories,
        'total_items': total_items,
        'total_value': total_value,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'title': 'Inventory Status Report',
    }
    
    return render(request, 'reports/report_inventory.html', context)

@login_required
def report_transactions(request):
    """Inventory Transactions Report"""
    # Get filter parameters
    item_id = request.GET.get('item')
    transaction_type = request.GET.get('transaction_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    export = request.GET.get('export')
    
    # Base queryset
    transactions = ItemTransaction.objects.all()
    
    # Apply filters
    if item_id:
        transactions = transactions.filter(item_id=item_id)
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    # Order by date and time
    transactions = transactions.order_by('-date', '-created_at')
    
    # Export to CSV if requested
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Item Code', 'Description', 'Transaction Type', 'Reference', 'Quantity In', 'Quantity Out', 'Balance After', 'Unit Price', 'Created By'])
        
        for transaction in transactions:
            writer.writerow([
                transaction.date,
                transaction.item.code,
                transaction.item.description,
                transaction.get_transaction_type_display(),
                transaction.reference,
                transaction.quantity_in or 0,
                transaction.quantity_out or 0,
                transaction.balance_after,
                transaction.unit_price,
                transaction.created_by.get_full_name() if transaction.created_by else ''
            ])
        
        return response
    
    # Get all items for filter dropdown
    items = Item.objects.all().order_by('code')
    
    # Calculate summary statistics
    total_transactions = transactions.count()
    total_in = transactions.aggregate(Sum('quantity_in'))['quantity_in__sum'] or 0
    total_out = transactions.aggregate(Sum('quantity_out'))['quantity_out__sum'] or 0
    
    # Pagination
    paginator = Paginator(transactions, 20)  # Show 20 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'transactions': page_obj,
        'items': items,
        'transaction_types': ItemTransaction.TRANSACTION_TYPES,
        'total_transactions': total_transactions,
        'total_in': total_in,
        'total_out': total_out,
        'title': 'Inventory Transactions Report',
    }
    
    return render(request, 'reports/report_transactions.html', context)

@login_required
def report_requisitions(request):
    """Store Requisitions Report"""
    # Get filter parameters
    department_id = request.GET.get('department')
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    export = request.GET.get('export')
    
    # Base queryset
    requisitions = StoreRequisition.objects.all()
    
    # Apply filters
    if department_id:
        requisitions = requisitions.filter(department_id=department_id)
    
    if status:
        requisitions = requisitions.filter(status=status)
    
    if date_from:
        requisitions = requisitions.filter(requested_date__gte=date_from)
    
    if date_to:
        requisitions = requisitions.filter(requested_date__lte=date_to)
    
    # Order by date
    requisitions = requisitions.order_by('-requested_date')
    
    # Export to CSV if requested
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="requisitions_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Requisition No', 'Department', 'Requested Date', 'Delivery Date', 'Status', 'Requested By', 'Checked By', 'Approved By', 'Items Count'])
        
        for req in requisitions:
            writer.writerow([
                req.requisition_no,
                req.department.name,
                req.requested_date,
                req.delivery_date,
                req.get_status_display(),
                req.requested_by.get_full_name() if req.requested_by else '',
                req.checked_by.get_full_name() if req.checked_by else '',
                req.approved_by.get_full_name() if req.approved_by else '',
                req.items.count()
            ])
        
        return response
    
    # Get all departments for filter dropdown
    departments = Department.objects.all().order_by('name')
    
    # Calculate summary statistics
    total_requisitions = requisitions.count()
    pending_count = requisitions.filter(status='pending').count()
    approved_count = requisitions.filter(status='approved').count()
    issued_count = requisitions.filter(status='issued').count()
    
    # Pagination
    paginator = Paginator(requisitions, 20)  # Show 20 requisitions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requisitions': page_obj,
        'departments': departments,
        'status_choices': StoreRequisition.STATUS_CHOICES,
        'total_requisitions': total_requisitions,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'issued_count': issued_count,
        'title': 'Store Requisitions Report',
    }
    
    return render(request, 'reports/report_requisitions.html', context)

@login_required
def report_purchases(request):
    """Purchases Report"""
    # Get filter parameters
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    export = request.GET.get('export')
    
    # Base queryset
    purchases = PurchaseRequisition.objects.all()
    
    # Apply filters
    if status:
        purchases = purchases.filter(status=status)
    
    if date_from:
        purchases = purchases.filter(date__gte=date_from)
    
    if date_to:
        purchases = purchases.filter(date__lte=date_to)
    
    # Order by date
    purchases = purchases.order_by('-date')
    
    # Export to CSV if requested
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="purchases_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['PR No', 'Date', 'Status', 'Requested By', 'Approved By', 'Total Amount', 'Items Count'])
        
        for pr in purchases:
            total_amount = sum(item.total_price or 0 for item in pr.items.all())
            writer.writerow([
                pr.pr_no,
                pr.date,
                pr.get_status_display(),
                pr.requested_by.get_full_name() if pr.requested_by else '',
                pr.approved_by.get_full_name() if pr.approved_by else '',
                total_amount,
                pr.items.count()
            ])
        
        return response
    
    # Calculate summary statistics
    total_purchases = purchases.count()
    pending_count = purchases.filter(status='pending_approval').count()
    approved_count = purchases.filter(status='approved').count()
    ordered_count = purchases.filter(status='ordered').count()
    received_count = purchases.filter(status='received').count()
    
    # Calculate total amount
    total_amount = 0
    for pr in purchases:
        total_amount += sum(item.total_price or 0 for item in pr.items.all())
    
    # Pagination
    paginator = Paginator(purchases, 20)  # Show 20 purchases per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'purchases': page_obj,
        'status_choices': PurchaseRequisition.STATUS_CHOICES,
        'total_purchases': total_purchases,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'ordered_count': ordered_count,
        'received_count': received_count,
        'total_amount': total_amount,
        'title': 'Purchases Report',
    }
    
    return render(request, 'reports/report_purchases.html', context)

@login_required
def report_dashboard(request):
    """Dashboard Report with charts and statistics"""
    # Date range for trend data
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get inventory statistics
    total_items = Item.objects.count()
    low_stock_items = Item.objects.filter(current_balance__lte=F('min_stock_level')).count()
    out_of_stock_items = Item.objects.filter(current_balance=0).count()
    inventory_value = Item.objects.aggregate(
        total_value=Sum(F('current_balance') * F('current_price'))
    )['total_value'] or 0
    
    # Get requisition statistics
    total_requisitions = StoreRequisition.objects.filter(
        requested_date__gte=start_date,
        requested_date__lte=end_date
    ).count()
    
    # Get purchase statistics
    total_purchases = PurchaseRequisition.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).count()
    
    # Get goods receiving statistics
    total_grns = GoodsReceivingNote.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).count()
    
    # Get top categories by value
    top_categories = Category.objects.annotate(
        total_value=Sum(F('items__current_balance') * F('items__current_price'))
    ).order_by('-total_value')[:5]
    
    # Get top departments by requisitions
    top_departments = Department.objects.annotate(
        req_count=Count('store_requisitions')
    ).order_by('-req_count')[:5]
    
    # Prepare data for charts
    # Daily transactions for the past 30 days
    daily_transactions = []
    for i in range(30):
        date = end_date - timedelta(days=i)
        in_qty = ItemTransaction.objects.filter(
            date=date,
            quantity_in__isnull=False
        ).aggregate(Sum('quantity_in'))['quantity_in__sum'] or 0
        
        out_qty = ItemTransaction.objects.filter(
            date=date,
            quantity_out__isnull=False
        ).aggregate(Sum('quantity_out'))['quantity_out__sum'] or 0
        
        daily_transactions.append({
            'date': date.strftime('%Y-%m-%d'),
            'in': in_qty,
            'out': out_qty
        })
    
    # Reverse to get chronological order
    daily_transactions.reverse()
    
    # Category distribution data
    category_data = []
    for category in Category.objects.all():
        value = Item.objects.filter(
            category=category
        ).aggregate(
            total_value=Sum(F('current_balance') * F('current_price'))
        )['total_value'] or 0
        
        if value > 0:
            category_data.append({
                'name': category.name,
                'value': value
            })
    
    context = {
        'total_items': total_items,
        'low_stock_items': low_stock_items,
        'out_of_stock_items': out_of_stock_items,
        'inventory_value': inventory_value,
        'total_requisitions': total_requisitions,
        'total_purchases': total_purchases,
        'total_grns': total_grns,
        'top_categories': top_categories,
        'top_departments': top_departments,
        'daily_transactions': json.dumps(daily_transactions),
        'category_data': json.dumps(category_data),
        'title': 'Dashboard Report',
    }
    
    return render(request, 'reports/report_dashboard.html', context)
