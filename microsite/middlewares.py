# encoding=utf-8

from microsite.utils import ProjectUnconfigured


class AuthenticationMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'user'), \
               (u"The microsite.AuthenticationMiddleware requires " 
                u"Django authentication middleware to be installed. "
                u"Edit your MIDDLEWARE_CLASSES setting to insert "
                u"'django.contrib.auth.middleware.AuthenticationMiddleware'.")

        try:
            request.user = request.user.get_profile()
        except AttributeError:
            pass


from django.template import RequestContext, loader
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def project_unconfigured(request, message=None, \
                         template_name='500_unconfigured.html',
                         project=None, *args, **kwargs):
    ''' renders template with project in context '''
    t = loader.get_template(template_name)
    context = {'request_path': request.path,
               'message': message,
               'project': project}
    return HttpResponseForbidden(t.render(RequestContext(request, context)))


class Http500UnconfiguredMiddleware(object):
    ''' catches ProjectUnconfigured and returns project_unconfigured view '''
    def process_exception(self, request, exception):
        if isinstance(exception, ProjectUnconfigured):
            return project_unconfigured(request,
                                        message=exception.message,
                                        project=exception.project)
