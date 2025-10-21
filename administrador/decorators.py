# administrador/decorators.py
from functools import wraps

from django.shortcuts import redirect


def staff_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_staff:
                return redirect("/")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
