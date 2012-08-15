# encoding=utf-8

from microsite.utils import get_option


def get_formhub_url(project):
    return get_option(project, 'formhub_uri')


def get_formhub_user(project):
    return get_option(project, 'formhub_user')


def get_formhub_form(project):
    return get_option(project, 'formhub_form')


def get_formhub_ids_user(project):
    return get_option(project, 'formhub_ids_user')


def get_formhub_ids_form(project):
    return get_option(project, 'formhub_ids_form')


def get_formhub_form_url(project, is_registration=False):
  
    data = {'base': get_formhub_url(project),
            'user': get_formhub_user(project),
            'form': get_formhub_form(project)}

    return u'%(base)s/%(user)s/forms/%(form)s' % data

def get_formhub_form_api_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/api' % data


def get_formhub_form_public_api_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/public_api' % data


def get_formhub_form_datacsv_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/data.csv' % data


def get_formhub_form_dataxls_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/data.xls' % data


def get_formhub_form_datakml_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/data.kml' % data


def get_formhub_form_datazip_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/data.zip' % data


def get_formhub_form_gdocs_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/gdocs' % data


def get_formhub_form_map_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/map' % data


def get_formhub_form_instance_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/instance' % data


def get_formhub_form_dataentry_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/enter-data' % data


def get_formhub_form_dataview_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/view-data' % data


def get_formhub_form_formxml_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/form.xml' % data


def get_formhub_form_formxls_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/form.xls' % data


def get_formhub_form_formjson_url(project, is_registration=False):
    data = {'form_url': get_formhub_form_url(project, is_registration)}
    return u'%(form_url)s/form.json' % data