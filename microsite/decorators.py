
from django.contrib.auth.decorators import login_required

from microsite.models import Option


def login_maybe_required(func):
    ''' forwards to login_required is website is not public (Option) '''

    try:
        is_public = Option.objects.get(key='microsite_is_public').value
    except:
        is_public = False

    if not is_public:
        return login_required(func)
    else:
        return func