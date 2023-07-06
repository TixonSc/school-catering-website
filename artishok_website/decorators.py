from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from .models import Cart, Child


def admin_only(function):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            profile = request.user.profile
            if profile.role == 4:
                return function(request, *args, **kwargs)
        return HttpResponseForbidden()
    return wrapper


def profile_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
            return redirect('create_profile')  # redirect to profile edit
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    def decorator(function):
        @wraps(function)
        @profile_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                profile = request.user.profile
                if profile.role in roles:
                    return function(request, *args, **kwargs)
            return HttpResponseForbidden()
        return wrapper
    return decorator

def can_access_cart():
    def decorator(view_func):
        @wraps(view_func)
        @profile_required
        def wrapped_view(request, cart_id, *args, **kwargs):
            try:
                cart = Cart.objects.get(id=cart_id)
                # Find the Child object with matching pupil_id and parent_id
                Child.objects.get(pupil_id=cart.pupil_id, parent_id=request.user.profile)
            except (Cart.DoesNotExist, Child.DoesNotExist):
                return 404 # or any other appropriate response 
            return view_func(request, cart_id, *args, **kwargs)
        return wrapped_view
    return decorator
