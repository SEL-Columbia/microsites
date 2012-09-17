
from functools import wraps

from django.utils.decorators import available_attrs
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import HttpResponseRedirect

from microsite.models import Option
from microsite.utils import ProjectUnconfigured


def project_required(also_registration=False, guests=None):
    ''' requests login; fwd to admin if no project; raise if project unconfig'''

    def inner_decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):

            if not hasattr(request, 'user') or (request.user.is_anonymous() 
                                                and guests is None):
                path = request.build_absolute_uri()
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(path, 
                                         None, REDIRECT_FIELD_NAME)

            if not getattr(request.user, 'project', None):
                try:
                    setattr(request.user, 'project', guests)
                except:
                    return HttpResponseRedirect('/admin')

            if not Option.objects.get(key='bamboo_dataset',
                                      project=request.user.project).value:
                raise ProjectUnconfigured(request.user.project)

            if (also_registration 
                and Option.objects.get(key='bamboo_ids_dataset',
                                       project=request.user.project).value):
                raise ProjectUnconfigured(request.user.project)

            return view_func(request, *args, **kwargs)
        return wraps(view_func)(_wrapped_view)
    return inner_decorator


def unconfigured_project_required(view_func):
    ''' requests login; fwd to admin if no project; raise if project unconfig'''

    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view(request, *args, **kwargs):

        if not hasattr(request, 'user') or request.user.is_anonymous():
            path = request.build_absolute_uri()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path, 
                                     None, REDIRECT_FIELD_NAME)

        if not getattr(request.user, 'project', None):
            return HttpResponseRedirect('/admin')

        return view_func(request, *args, **kwargs)

    return _wrapped_view