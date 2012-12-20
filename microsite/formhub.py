# encoding=utf-8

import os
import requests
import zipfile
import tempfile

from microsite.utils import get_option

FORMHUB_UPLOAD_TIMEOUT = 60


class ErrorUploadingDataToFormhub(IOError):

    def details(self, kind=None):
        return ''


class ErrorMultipleUploadingDataToFormhub(IOError):

    def __init__(self, *args, **kwargs):
        super(ErrorMultipleUploadingDataToFormhub, self).__init__(*args,
                                                                  **kwargs)
        self.timeouts = []
        self.failures = []
        self.denies = []

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message

    def is_filled(self):
        return bool(self.count())

    def count(self):
        return len(self.timeouts) + len(self.failures) + len(self.denies)

    @property
    def message(self):
        return (u"Error while submitting multiple forms. "
                u"%(total)d submissions failed:\n%(nb_timeouts)d time outs.\n"
                u"%(nb_failures)d general failures.\n"
                u"%(nb_denies)d submissions rejected."
                % {'total': self.count(),
                   'nb_timeouts': len(self.timeouts),
                   'nb_failures': len(self.failures),
                   'nb_denies': len(self.denies)})

    def details(self, kind=None):
        if not kind is None and kind in ('timeouts', 'failures', 'denies'):
            exceptions = self.get(kind)
        else:
            exceptions = self.timeouts + self.failures + self.denies
        return '\n'.join(['%r' % e for e in exceptions])


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


def get_formhub_user_url(project, is_registration=False):
    user = (get_formhub_ids_user(project) if is_registration
                                         else get_formhub_user(project))
    data = {'base': get_formhub_url(project),
            'user': user}
    return u'%(base)s/%(user)s' % data


def get_formhub_form_url(project, is_registration=False):
    form = (get_formhub_ids_form(project) if is_registration
                                         else get_formhub_form(project))
    data = {'user_url': get_formhub_user_url(project, is_registration),
            'form': form}
    return u'%(user_url)s/forms/%(form)s' % data


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


def get_formhub_submission_url(project, is_registration=False):
    data = {'user_url': get_formhub_user_url(project, is_registration)}
    return u'%(user_url)s/submission' % data


def get_formhub_bulk_submission_url(project, is_registration=False):
    data = {'user_url': get_formhub_user_url(project, is_registration)}
    return u'%(user_url)s/bulk-submission' % data


def submit_xml_forms_formhub(project, xforms=[], as_bulk=False, attachments=[]):
    formhub_submission_url = get_formhub_submission_url(project)
    bulk_submission_url = get_formhub_bulk_submission_url(project)
    return submit_xml_forms_formhub_raw(formhub_submission_url, xforms=xforms,
                                        as_bulk=as_bulk,
                                        attachments=attachments,
                                        bulk_submission_url=bulk_submission_url)


def submit_xml_forms_formhub_raw(submission_url, xforms=[], as_bulk=False,
                                 attachments=[], bulk_submission_url=u''):

    # allow single form parameter
    if not isinstance(xforms, list):
        xforms = [xforms]

    # bulk allows to send multiple forms at once in a ZIP archive
    if as_bulk:

        # filename for the zip file
        ziph, zip_file = tempfile.mkstemp(suffix='.zip')

        # create the ZIP file containing the forms
        with zipfile.ZipFile(zip_file, 'w') as zfile:
            for form_xml in xforms:
                if not form_xml:
                    continue

                # create a temporary file for each form
                fileh, form_file = tempfile.mkstemp(suffix='.xml')
                os.write(fileh, form_xml)
                os.close(fileh)
                # add the temp xml file to the zip file
                zfile.write(form_file)
                try:
                    os.remove(form_file)
                except:
                    pass

        # upload the zip file
        try:
            req = requests.post(bulk_submission_url,
                                    files={'zip_submission_file':
                                           (zip_file,
                                            open(zip_file))},
                                           timeout=FORMHUB_UPLOAD_TIMEOUT)
        except requests.exceptions.Timeout:
            raise ErrorUploadingDataToFormhub(u"Upload timed out after "
                                              u"%ds." % FORMHUB_UPLOAD_TIMEOUT)
        except Exception as e:
            raise ErrorUploadingDataToFormhub(u"Unable to send: %r" % e.message)

        if not req.status_code in (200, 201, 202):
            raise ErrorUploadingDataToFormhub(u'Unable to submit ZIP: %s'
                                              % req.text)
        print(req.text)
        return True

    # not bulk, submissions one by one
    exception = ErrorMultipleUploadingDataToFormhub()

    for index, form_xml in enumerate(xforms):
        if not form_xml:
            continue
        try:
            # add pictures & other attachments
            try:
                attached = attachments[index]
            except:
                attached = []

            req_files = {'xml_submission_file': ('form.xml', form_xml)}
            for num, attachment in enumerate(attached):
                req_files.update({'form_attachment_%d' % num: attachment})
            req = requests.post(submission_url,
                                files=req_files,
                                timeout=FORMHUB_UPLOAD_TIMEOUT)
        except requests.exceptions.Timeout as e:
            exception.timeouts.append(e)
            continue
        except Exception as e:
            exception.failures.append(e)
            continue

        try:
            assert req.status_code in (200, 201, 202), (u"Received unexpected "
                                                        u"HTTP return code %d."
                                                        % req.status_code)
        except AssertionError as e:
            print(req.text)
            exception.denies.append(e)

    if exception.is_filled():
        raise exception

    return True
