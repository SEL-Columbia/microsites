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

from path import path

from microsite.utils import download_formhub

FH_LOGIN = u'atasoils'
FH_PASSWORD = u'soilmap'

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
    from microsite.formhub import (submit_xml_forms_formhub_raw,
                               ErrorUploadingDataToFormhub,
                               ErrorMultipleUploadingDataToFormhub)
    from microsite.utils import nest_flat_dict

    submission_url = u'http://formhub.org/atasoils/submission'
    bulk_submission_url = u'http://formhub.org/atasoils/bulk-submission'

    xforms = []
    headers = []
    first = True
    count = 0

    for line in UnicodeReader(open(csv_in)):
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
        submit_xml_forms_formhub_raw(submission_url=submission_url,
                                     xforms=xforms, as_bulk=True,
                                     attachments=None,
                                     bulk_submission_url=bulk_submission_url)
    except (ErrorUploadingDataToFormhub,
            ErrorMultipleUploadingDataToFormhub) as e:
        print(e)
        print(e.details())
    return


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
    print(u"Generating FH submissions")
    generate_fh_submission(csv_in=u'%s_clean.csv' % FORMS[0],
                           form=NEW_FORMS[0])

    # Generate FH submissions for each cleaned sample.


if __name__ == '__main__':
    main()
