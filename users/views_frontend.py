from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from users.models import CustomUser, Department
from users.forms import UserRegistrationForm, UserUpdateForm, DepartmentForm

@login_required
def user_list(request):
    # Check if user has admin permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get filter parameters
    role = request.GET.get('role')
    department_id = request.GET.get('department')
    is_active = request.GET.get('is_active')
    search = request.GET.get('search')
    
    # Base queryset
    users = CustomUser.objects.all()
    
    # Apply filters
    if role:
        users = users.filter(role=role)
    
    if department_id:
        users = users.filter(department_id=department_id)
    
    if is_active is not None:
        is_active_bool = is_active.lower() == 'true'
        users = users.filter(is_active=is_active_bool)
    
    if search:
        users = users.filter(
            Q(username__icontains=search) | 
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # Order by username
    users = users.order_by('username')
    
    # Pagination
    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get departments for filter dropdown
    departments = Department.objects.all().order_by('name')
    
    context = {
        'users': page_obj,
        'departments': departments,
        'role_choices': CustomUser.ROLE_CHOICES,
    }
    
    return render(request, 'users/user_list.html', context)

@login_required
def user_detail(request, pk):
    # Check if user has admin permissions or is viewing their own profile
    if not request.user.is_staff and request.user.id != pk:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    context = {
        'user_obj': user,
    }
    
    return render(request, 'users/user_detail.html', context)

@login_required
def user_create(request):
    # Check if user has admin permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'User {user.username} created successfully.')
            return redirect('user_list')
    else:
        form = UserRegistrationForm()
    
    context = {
        'form': form,
        'title': 'Create User',
    }
    
    return render(request, 'users/user_form.html', context)

@login_required
def user_edit(request, pk):
    # Check if user has admin permissions or is editing their own profile
    if not request.user.is_staff and request.user.id != pk:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully.')
            if request.user.id == pk:
                return redirect('profile')
            else:
                return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)
    
    context = {
        'form': form,
        'user_obj': user,
        'title': 'Edit User',
    }
    
    return render(request, 'users/user_form.html', context)

@login_required
def user_change_password(request, pk):
    # Check if user has admin permissions or is changing their own password
    if not request.user.is_staff and request.user.id != pk:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    if request.method == 'POST':
        # If user is changing their own password, use PasswordChangeForm
        if request.user.id == pk:
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password was successfully updated!')
                return redirect('profile')
        # If admin is changing someone else's password
        else:
            password = request.POST.get('password')
            if password:
                user.set_password(password)
                user.save()
                messages.success(request, f'Password for {user.username} updated successfully.')
                return redirect('user_list')
            else:
                messages.error(request, 'Password cannot be empty.')
    else:
        # If user is changing their own password, use PasswordChangeForm
        if request.user.id == pk:
            form = PasswordChangeForm(user=request.user)
            context = {
                'form': form,
                'user_obj': user,
                'title': 'Change Password',
            }
            return render(request, 'users/password_change.html', context)
    
    # Simple form for admin changing someone else's password
    context = {
        'user_obj': user,
        'title': 'Change Password',
    }
    
    return render(request, 'users/password_change_admin.html', context)

@login_required
def user_toggle_active(request, pk):
    # Check if user has admin permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    user = get_object_or_404(CustomUser, pk=pk)
    
    # Don't allow deactivating yourself
    if user == request.user:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('user_list')
    
    user.is_active = not user.is_active
    user.save()
    
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} {status} successfully.')
    
    return redirect('user_list')

@login_required
def department_list(request):
    # Check if user has admin permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # Get filter parameters
    search = request.GET.get('search')
    
    # Base queryset
    departments = Department.objects.all()
    
    # Apply filters
    if search:
        departments = departments.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Order by name
    departments = departments.order_by('name')
    
    # Pagination
    paginator = Paginator(departments, 10)  # Show 10 departments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'departments': page_obj,
    }
    
    return render(request, 'users/department_list.html', context)

@login_required
def department_create(request):
    # Check if user has admin permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department {department.name} created successfully.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'title': 'Create Department',
    }
    
    return render(request, 'users/department_form.html', context)

@login_required
def department_edit(request, pk):
    # Check if user has admin permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f'Department {department.name} updated successfully.')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
        'title': 'Edit Department',
    }
    
    return render(request, 'users/department_form.html', context)

@login_required
def profile(request):
    """View for user to see their own profile"""
    return redirect('user_detail', pk=request.user.id)

def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/login.html', context)

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def audit_log(request):
    """View for audit log"""
    # Check if user has admin permissions
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
    # This would be implemented with a proper audit log model
    # For now, we'll just render a template
    
    context = {
        'title': 'Audit Log',
    }
    
    return render(request, 'users/audit_log.html', context)
