
DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# ROOT_DIR contains path to this file's parent dir.
import os
abs_path = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(abs_path))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'microsite.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
# TIME_ZONE = 'America/New_York'
TIME_ZONE = 'Africa/Bamako'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(ROOT_DIR, 'collected_static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'lkq3-5$z9wq&amp;44&amp;p1aaey5-p@3egm6fk)$_toh8jf)6g(w9yj#'

# overload apps list
INSTALLED_APPS_EXTRA = ['reportcard']

# app receiving root URI request
DEFAULT_APP = 'reportcard'

# User Profile
# AUTH_PROFILE_MODULE = 'accounts.UserProfile'