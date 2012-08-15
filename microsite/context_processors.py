# encoding=utf-8


def add_user(request):
    ''' Add the MicrositeUser object of logged-in user or django's User '''
    try:
        user = request.user.get_profile()
    except:
        user = request.user

    return {'user': user}