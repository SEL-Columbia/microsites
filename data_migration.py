#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

import shutil
import uuid
import csv
import codecs
import cStringIO
from dict2xml import dict2xml
import copy
import json
import time

import requests
from path import path
from pybamboo.connection import Connection
from pybamboo.dataset import Dataset

from microsite.utils import download_formhub
from microsite.formhub import (submit_xml_forms_formhub_raw,
                           ErrorUploadingDataToFormhub,
                           ErrorMultipleUploadingDataToFormhub)
from microsite.utils import nest_flat_dict

SUBMISSION_URL = u'http://formhub.org/atasoils/submission'
BULK_SUBMISSION_URL = u'http://formhub.org/atasoils/bulk-submission'
PUBLIC_API_URL = u'https://www.formhub.org/atasoils/forms/%(form)s/public_api'
FH_TIMEOUT = 60

FH_LOGIN = u'atasoils'
FH_PASSWORD = u''
BAMBOO_URL = u'http://bamboo.io/'

FORMS = [
    u'EthioSIS_ET',
    u'ESTS_1_send_field_to_PC',
    u'ESTS_2_arrive_at_PC_from_field',
    u'ESTS_3_send_PC_to_NSTC',
    u'ESTS_4_arrive_at_NSTC_from_PC',
    u'ESTS_5_send_NSTC_to_Archive',
    u'ESTS_6_arrive_at_Archive_from_NSTC'
]

NEW_FORMS = [
    u'ESTS_ET_sample',
    u'ESTS_Step1',
    u'ESTS_Step2',
    u'ESTS_Step3',
    u'ESTS_Step4',
    u'ESTS_Step5',
    u'ESTS_Step6',
]

STEPS_FORMS = u'ESTS_Steps'
NA_START = u"n/a__"
NA = None

TOP_QR = 'top_qr'
SUB_QR = 'sub_qr'
QR_0_20 = 'qr_0_20'
QR_20_40 = 'qr_20_40'
QR_40_60 = 'qr_40_60'
QR_60_80 = 'qr_60_80'
QR_80_100 = 'qr_80_100'

EXISTING = {
    TOP_QR: [],
    SUB_QR: [],
    QR_0_20: [],
    QR_20_40: [],
    QR_40_60: [],
    QR_60_80: [],
    QR_80_100: []
}

DUPLICATES = {
    TOP_QR: {},
    SUB_QR: {},
    QR_0_20: {},
    QR_20_40: {},
    QR_40_60: {},
    QR_60_80: {},
    QR_80_100: {}
}

INDEXES = {
    TOP_QR: -13,
    SUB_QR: -12,
    QR_0_20: -11,
    QR_20_40: -10,
    QR_40_60: -9,
    QR_60_80: -8,
    QR_80_100: -7
}

AVAILABLES = []

USED = {
    'step1': [],
    'step2': [],
    'step3': [],
    'step4': [],
    'step5': [],
    'step6': [],
}

LABS = {
    u'awassa': [
        'Hawassa',
        'Awassa',
        'Awasa',
        'Awwasa',
        'Awassa soil laboratory',
        'Awass soil laboratory',
        'Hawasa',
        'Awasss',
        'Hawasw',
        'Hawassa soil testing laboratory',
        'Hawassa soil testing',
        'Hawassa soil testing lab.',
        'Hawassa soil testig lab.',
        'Hawassa soil testing lab ',
        'Hawassa soil lab.',
        'Hawassa ',
        'Awasa soil lab',
        'Hawassa soil labratory',
        'Awasa lab',
        'Hawassa soil lab',
        'Hawssa',
    ],
    u'nekempte': [
        'Nekemte',
        'Nekrmte',
        ' Nekemte',
        'Nekemtr',
        '"Nekemte',
        'Mekelle',
        '"Mekelle',
        'Nrkemte',
        'Nekemt',
    ],
    u'jimma': [
        'Jimma',
        'Jima '
        'Jima',
        'Jims',
        'Jimma research',
        'Jimma soil lab',
        'Jima research center',
        'Jima reserch center',
    ],
    u'nstc_pc': [
        'Addis ababa',
        'Addis Ababa',
        'NSTC',
        'Nstl',
        'NSTL',
        ' NSTL',
        'N\tSTL',
        'National soil testing center',
        'Addis abeba',
        '"Addis \na"',
        'Addis ababa soil lab',
        'Addis ababa national soil labrator',
        'Addis ababa national lab',
        'A.A',
        'A. A',
        'Nstc lab',
        'Add is Ababa',
        'Addiss Ababa',
        'nstc',
    ],
    u'bar_hadir': [
        'Bahardar',
        'Bahsrdar',
        'Bahrdar',
        'Bahrdar soil testing lab.',
        'Bahir Dar',
        'Bahirdar ',
        'Bd ',
        'Bd',
        'Bday',
        'BahrDar',
        'Bahirdar',
        'Bahir dar',
        'Bahrdar s.t.l',
        'Baher dar',
    ],
    u'dessie': [
        'Dessie',
        'Dessie ',
        'Desie',
        'Dessi',
        'Desie soil testing laboratory',
        'Dessiesoiltestinglaboratory',
        'Desire soil testing laboratory',
        'Desire soil testing lanoratory',
        'Dessie soil testing lab.',
        'Dessie soil t.l',
        'Dessie soil lab',
        'Desse',
        'Dessie soil testing lab',
        'Desiesoiltestinglaboratpratory',
    ],
    u'mekelle': [
        'Mekelle soil laboratory',
        'Mekele soil laboratory ',
        'Mekelle soil labratory',
        'Mekele',
        'Mekele\n',
    ],
}


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def cleanup_ethiosis(csv_in, csv_out):

        csv_in_fh = open(csv_in)
        # lines = open(csv_in).read().split("$\n")
        csv_out_fh = open(csv_out, 'w')
        csv_out_writer = UnicodeWriter(csv_out_fh)

        first = True

        uniques = 0
        goods = 0
        dups = 0
        nb_lines = 0

        for line in UnicodeReader(csv_in_fh):
            if first:
                csv_out_writer.writerow(line)

                first = False
                continue

            nb_lines += 1

            try:
                d = {}
                for k, i in INDEXES.items():
                    d[k] = line[i].upper()
            except:
                continue

            start = line[1]
            end = line[-1]

            if not '+' in start or not '+' in end:
                continue

            dup = False
            for k, v in d.items():

                if v.strip().lower() == "n/a":
                    line[INDEXES[k]] = u"n/a___%s" % uuid.uuid4().hex
                elif v in EXISTING[k]:
                    if not v in DUPLICATES[k].keys():
                        DUPLICATES[k].update({v: 1})
                    DUPLICATES[k][v] += 1

                    dup = True
                    dups += 1
                else:
                    EXISTING[k].append(v)
                    goods += 1
            if not dup:
                uniques += 1
                csv_out_writer.writerow(line)

        csv_in_fh.close()
        csv_out_fh.close()


def json2xform(jsform, form_id):
        # changing the form_id to match correct Step
        dd = {'form_id': form_id}
        xml_head = u"<?xml version='1.0' ?><%(form_id)s id='%(form_id)s'>" % dd
        xml_tail = u"</%(form_id)s>" % dd

        for field in jsform.keys():
            # treat field starting with underscore are internal ones.
            # and remove them
            if field.startswith('_'):
                jsform.pop(field)

        return xml_head + dict2xml(jsform) + xml_tail


def generate_fh_submission(csv_in, form):


    headers = []
    errors = []
    first = True
    count = 0
    success = 0

    for line in UnicodeReader(open(csv_in)):
        xforms = []
        if first:
            headers = line
            first = False
            continue

        sub_dict = dict(zip(headers, line))
        nest_flat_dict(sub_dict)
        for key in INDEXES.keys():
            bc = sub_dict.get(u'found', {}).get(key, NA_START)
            if bc.startswith(NA_START):
                continue
            count += 1
            submission_dict = copy.deepcopy(sub_dict)
            submission_dict.update({u'barcode': bc,
                                    u'position': key})
            print(u"%d Adding %s:%s" % (count, key, bc))
            xforms.append(json2xform(submission_dict, NEW_FORMS[0]))

        try:
            print(u"Submitting %d xforms" % len(xforms))
            submit_xml_forms_formhub_raw(submission_url=SUBMISSION_URL,
                                         xforms=xforms, as_bulk=True,
                                         attachments=None,
                                         bulk_submission_url=BULK_SUBMISSION_URL,
                                         timeout=FH_TIMEOUT)
            success += 1
        except (ErrorUploadingDataToFormhub,
                ErrorMultipleUploadingDataToFormhub) as e:
            print(e)
            print(e.details())
            errors.extend(xforms)

    print(u"Submitted %d forms successfuly." % success)
    print(u"Re-submitting %d forms." % len(errors))
    for error in errors:
        try:
            submit_xml_forms_formhub_raw(submission_url=SUBMISSION_URL,
                                         xforms=[error], as_bulk=False,
                                         attachments=None,
                                         bulk_submission_url=BULK_SUBMISSION_URL,
                                         timeout=FH_TIMEOUT)
            success += 1
        except (ErrorUploadingDataToFormhub,
                ErrorMultipleUploadingDataToFormhub) as e:
            print(e)
            print(e.details())
            errors.extend(xforms)


def clean_pc_slug(bad_slug):

    for pc_slug, values in LABS.items():
        if bad_slug in values:
            return pc_slug
    return NA


def generate_fh_steps(csv_in, form, step):

    steps = {
             'imei': NA,
             'start_time': NA,
             'end_time': NA,
             'survey_day': NA,
             'deviceid': NA,
             'sim_serial_number': NA,
             'phone_number': NA,
             'step': step,
             'name': NA,
             'cp_num': NA,
             'pc_destination': NA,
             'processing_center': NA,
             'scan': [],
             }
    headers = []
    first = True
    count = 0
    errors = []
    success = 0
    indivs = 0

    for line in UnicodeReader(open(csv_in)):
        xforms = []
        if first:
            headers = line
            first = False
            continue

        submission = copy.deepcopy(steps)

        parsed_line = dict(zip(headers, line))

        # fill up with common values
        for key in submission.keys():
            value = parsed_line.get(key, None)
            if value is not None:
                submission[key] = value

        # per form logic
        for key in ('pc_destination', 'processing_center'):
            if submission.get(key, NA) != NA:
                submission[key] = clean_pc_slug(submission[key])

        # cp_num used to be a float
        if submission.get('cp_num') != NA:
            try:
                submission['cp_num'] = int(submission['cp_num'])
            except:
                pass

        # form-specific rematch
        if parsed_line.get('pc_name'):
            submission['processing_center'] = \
                                      clean_pc_slug(parsed_line.get('pc_name'))

        # loop on soil_id
        for key in parsed_line.keys():
            if not key.startswith('scan['):
                continue

            soil_id = parsed_line.get(key)
            if not soil_id in AVAILABLES:
                continue

            if soil_id in USED[step]:
                continue

            USED[step].append(soil_id)

            submission['scan'].append({'soil_id': soil_id})

        if not len(submission['scan']):
            continue
        else:
            indivs += len(submission['scan'])

        print(u"%d Adding a form with %d scans" % (count,
                                                   len(submission['scan'])))
        xforms.append(json2xform(submission, STEPS_FORMS))
        count += 1

        try:
            print(u"Submitting %d xforms" % len(xforms))
            submit_xml_forms_formhub_raw(submission_url=SUBMISSION_URL,
                                         xforms=xforms, as_bulk=False,
                                         attachments=None,
                                         bulk_submission_url=BULK_SUBMISSION_URL,
                                         timeout=FH_TIMEOUT)
            success += 1
        except (ErrorUploadingDataToFormhub,
                ErrorMultipleUploadingDataToFormhub) as e:
            print(e)
            print(e.details())
            errors.extend(xforms)

    print(u"Submitted %d forms successfuly (%d indivs)." % (success, indivs))
    print(u"Re-submitting %d forms." % len(errors))
    for error in errors:
        try:
            submit_xml_forms_formhub_raw(submission_url=SUBMISSION_URL,
                                         xforms=[error], as_bulk=False,
                                         attachments=None,
                                         bulk_submission_url=BULK_SUBMISSION_URL,
                                         timeout=FH_TIMEOUT)
            success += 1
        except (ErrorUploadingDataToFormhub,
                ErrorMultipleUploadingDataToFormhub) as e:
            print(e)
            print(e.details())
            errors.extend(xforms)


def main():
    # Download CSV for all forms.
    for form in FORMS:
        form_csv = path(u'%s.csv' % form)
        if not form_csv.isfile():
            print(u"Downloading CSV for %s" % form)
            url = u"https://www.formhub.org/atasoils/forms/%s/data.csv" % form
            form_csv_tmp = path(download_formhub(url, login=FH_LOGIN, password=FH_PASSWORD))
            shutil.copy(form_csv_tmp, u'%s.csv' % form)
        print(form_csv, form_csv.isfile())

    # Parse EthioSIS and build a cleaned-up version
    cleanup_ethiosis(csv_in=u'%s.csv' % FORMS[0],
                     csv_out=u'%s_clean.csv' % FORMS[0])
    print(u"Cleanup done.")
    print(u"\n")
    # Generate FH submissions for each cleaned sample.
    submissions_done = path('submissions_done')
    if not submissions_done.isfile():
        print(u"Generating FH submissions")
        generate_fh_submission(csv_in=u'%s_clean.csv' % FORMS[0],
                               form=NEW_FORMS[0])
        submissions_done.touch()

    # flat list of available IDs to pop out
    for id_list in EXISTING.values():
        for soil_id in id_list:
            if not soil_id in AVAILABLES:
                AVAILABLES.append(soil_id)

    # Parse Steps 1-6, cleanup (duplicates), clean PC names
    for findex, form in enumerate(FORMS):
        if findex == 0:
            continue
        step = u'step%d' % findex
        step_done = path(u'%s_done' % step)
        if not step_done.isfile():
            print(u"Generating STEP %d submissions" % findex)
            generate_fh_steps(csv_in=u'%s.csv' % form,
                              form=form,
                              step=step)
            step_done.touch()

    # join the datasets
    print(u"Joining datasets")
    joined_dataset = None
    bamboo_conn = Connection(BAMBOO_URL)
    for form in NEW_FORMS:
        try:
            form_dataset = json.loads(requests.get(PUBLIC_API_URL
                                      % {'form': form}).text)['bamboo_dataset']
        except:
            form_dataset = u''

        if not form_dataset:
            continue

        print(u"%s: %s" % (form, form_dataset))

        if not joined_dataset:
            joined_dataset = form_dataset
            continue

        print(u"Joined dataset: %s" % joined_dataset)

        ds_joined = Dataset(connection=bamboo_conn, dataset_id=joined_dataset)
        ds_form = Dataset(connection=bamboo_conn, dataset_id=form_dataset)
        dataset = Dataset.join(left_dataset=ds_joined,
                               right_dataset=ds_form,
                               on=u'barcode',
                               connection=bamboo_conn)
        time.sleep(10)
        joined_dataset = dataset.id

        print(u"Merged dataset: %s" % dataset.id)
    print(u"Ultimate dataset: %s" % dataset.id)


if __name__ == '__main__':
    main()
