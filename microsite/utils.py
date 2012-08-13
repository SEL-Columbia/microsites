# encoding=utf-8

import os
import StringIO
import tempfile
import datetime
import json

import twill
from twill import commands as tw, get_browser
from twill.errors import TwillAssertionError


class DownloadFailed(StandardError):
    pass


def download_with_djangologin(url, login_url, login=None, 
                              password=None, ext=''):
    ''' Download a URI from a website using Django by loging-in first

        1. Logs in using supplied login & password (if provided)
        2. Create a temp file on disk using extension if provided
        3. Write content of URI into file '''

    # log-in to Django site
    if login and password:
        tw.go(login_url)
        tw.formvalue('1', 'username', login)
        tw.formvalue('1', 'password', password)
        tw.submit()

    # retrieve URI
    try:
        tw.go(url)
        tw.code('200')
    except TwillAssertionError:
        code = get_browser().get_code()
        # ensure we don't keep credentials
        tw.reset_browser()
        raise DownloadFailed(u"Unable to download %(url)s. "
                             u"Received HTTP #%(code)s."
                             % {'url': url, 'code': code})
    buff = StringIO.StringIO()
    twill.set_output(buff)
    try:
        tw.show()
    finally:
        twill.set_output(None)
        tw.reset_browser()

    # write file on disk
    suffix = '.%s' % ext if ext else ''
    fileh, filename = tempfile.mkstemp(suffix=suffix)
    os.write(fileh, buff.getvalue())
    os.close(fileh)
    buff.close()

    return filename


def download_formhub(url, login=None, password=None, ext=''):
    ''' shortcut to download_with_djangologin using formhub URL '''
    return download_with_djangologin(url, 'https://formhub.org/accounts/login/',
                                     login, password, ext)


def dump_json(obj, default=None):
    ''' shortcut to json dump with datetime hack '''
    def date_default(obj):
        return obj.isoformat() if isinstance(obj, datetime.datetime) else obj
    if not default:
        default = date_default
    return json.dumps(obj, default=default)


def load_json(json_str, object_hook=None):
    return json.loads(json_str, object_hook=object_hook)