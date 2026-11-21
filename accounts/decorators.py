from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def login_required_custom(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('username') or not request.session.get('role'):
            messages.warning(request, 'Please log in to access this portal.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('username') or not request.session.get('role'):
            messages.warning(request, 'Please log in to access the Administrator portal.')
            return redirect('accounts:login')
        if request.session.get('role') != 'Admin':
            messages.error(request, 'Unauthorized access: Administrator privileges required.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def tech_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('username') or not request.session.get('role'):
            messages.warning(request, 'Please log in to access the Technician portal.')
            return redirect('accounts:login')
        if request.session.get('role') != 'Technician':
            messages.error(request, 'Unauthorized access: Technician privileges required.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def consumer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('username') or not request.session.get('role'):
            messages.warning(request, 'Please log in to access the Consumer portal.')
            return redirect('accounts:login')
        if request.session.get('role') != 'Consumer':
            messages.error(request, 'Unauthorized access: Consumer account required.')
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
