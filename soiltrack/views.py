# encoding=utf-8

import re
import json
import copy
from datetime import datetime, timedelta

from django.shortcuts import render
# from pybamboo import ErrorRetrievingBambooData
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from pybamboo.connection import Connection
from pybamboo.exceptions import BambooError, ErrorParsingBambooData
from dict2xml import dict2xml

from microsite.views import options as ms_options
from microsite.utils import get_option
from microsite.bamboo import raw_getset_bamboo_dataset
from microsite.views import DEFAULT_IDS
from microsite.models import Project
from microsite.barcode import b64_qrcode
from microsite.decorators import project_required
from microsite.formhub import (submit_xml_forms_formhub,
                               ErrorUploadingDataToFormhub,
                               ErrorMultipleUploadingDataToFormhub)
from microsite.bamboo import (get_bamboo_dataset_id,
                              get_bamboo_url, CachedDataset)

from soiltrack.spid_ssid import generate_ssids
from soiltrack.utils import ensure_fixtures_ready
from soiltrack.sample import ESTSSample


DEFAULT_PROJECT = Project.objects.get(slug='soiltrack')

PROCESSING_CENTERS = {
    'awassa': (u"Awassa", u"Hawassa soil testing",
               u"Hawassa soil testing laboratory",
               u"Hawassa soil lab", u"Hawassa soil testing lab."),
    'nekempte': (u"Nekempte", u"Nekemte"),
    'jimma': (u"Jimma", u"Jima"),
    'nstc_pc': (u"NSTC PC", u"nstc"),
    'bar_hadir': (u"Bar Hadir", u"Bd"),
    'dessie': (u"Dessie",),
    'mekelle': (u"Mekelle", u"Mekele"),
}

# check-for/create datasets fixtures
ensure_fixtures_ready(DEFAULT_PROJECT)


@project_required(guests=DEFAULT_PROJECT)
def dashboard(request):
    context = {'category': 'home'}

    # init bamboo datasets
    main_dataset = ESTSSample.all_datasets(request.user.project) \
                             .get(ESTSSample.STATUS_COLLECTED)

    def pc(num, denum):
        try:
            return float(num) / float(denum)
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0

    # total number of plots (EthioSIS_ET submissions)
    try:
        nb_plots = int(main_dataset.count('found_top_qr', cache=True))
    except (BambooError, ErrorParsingBambooData):
        nb_plots = 0

    # collected samples (ESTS1)
    try:
        ests1 = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_SENT_TO_PC)
        nb_collected = int(ests1.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_collected = 0

    # being processed samples (ESTS2)
    try:
        ests2 = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_ARRIVED_AT_PC)
        nb_processing = int(ests2.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_processing = 0

    # processed samples (ESTS3)
    try:
        ests3 = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_SENT_TO_NSTC)
        nb_processed = int(ests3.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_processed = 0

    # being analyzed samples (ESTS4)
    try:
        ests4 = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_ARRIVED_AT_NSTC)
        nb_analyzing = int(ests4.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_analyzing = 0

    # analyzed samples (ESTS5)
    try:
        ests5 = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_SENT_TO_ARCHIVE)
        nb_analyzed = int(ests5.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_analyzed = 0

    # archived samples (ESTS6)
    try:
        ests6 = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_ARRIVED_AT_ARCHIVE)
        nb_archived = int(ests6.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_archived = 0

    # lost/missing samples
    nb_lost = 1

    # total form submissions:
    nb_submissions = sum([nb_plots, nb_collected, nb_processing, nb_processed,
                          nb_analyzing, nb_analyzed, nb_archived])

    last_events = []
    last_events_id = []
    for ds_type, dataset in {'ests1': ests1,
                    'ests2': ests2,
                    'ests3': ests3,
                    'ests4': ests4,
                    'ests5': ests5,
                    'ests6': ests6}.items():

        last_ten = dataset.get_data(order_by='-end_time', limit=10,
                                    select=['scan_soil_id', 'end_time'],
                                    cache=True, cache_expiry=60 * 60 * 5)
        if isinstance(last_ten, list):
            last_events_id += last_ten

    last_events_id.sort(key=lambda e: e.get('end_time'), reverse=True)
    last_events_id = last_events_id[:9]
    for event in last_events_id:
        try:
            sample = ESTSSample(event.get(u'scan_soil_id'),
                                project=request.user.project)
            last_events.append(sample)
        except ValueError:
            pass

    context.update({'nb_plots': nb_plots,
                    'nb_collected': nb_collected,
                    'pc_collected': pc(nb_collected, nb_collected),
                    'nb_processed': nb_processed,
                    'pc_processed': pc(nb_processed, nb_collected),
                    'nb_analyzed': nb_analyzed,
                    'pc_analyzed': pc(nb_analyzed, nb_collected),
                    'nb_lost': nb_lost,
                    'pc_lost': pc(nb_lost, nb_collected),
                    'nb_processing': nb_processing,
                    'nb_analyzing': nb_analyzing,
                    'nb_archived': nb_archived,
                    'nb_submissions': nb_submissions,
                    'last_events': last_events,
                    'processing_centers': [(k, v[0])
                                           for k, v
                                           in PROCESSING_CENTERS.items()]})

    return render(request, 'dashboard.html', context)


def idgen(request, nb_ids=DEFAULT_IDS):

    context = {'category': 'idgen'}

    # hard-coded max number of IDs to gen.
    try:
        nb_ids = 100 if int(nb_ids) > 100 else int(nb_ids)
    except ValueError:
        nb_ids = DEFAULT_IDS

    all_ids = []

    # for i in xrange(0, nb_ids):
    for ssid in generate_ssids('NG'):
        # this is a tuple of (ID, B64_QRPNG)
        all_ids.append((ssid, b64_qrcode(ssid, scale=1.8)))

    context.update({'generated_ids': all_ids})

    return render(request, 'idgen.html', context)


def options(request):
    if not request.method == "POST":
        return ms_options(request)

    response = ms_options(request)

    # try to update bamboo datasets
    for key_prefix in ('ests1', 'ests2', 'ests3', 'ests4', 'ests5', 'ests6'):
        form = get_option(request.user.project, '%s_form' % key_prefix)
        key = '%s_dataset' % key_prefix
        if raw_getset_bamboo_dataset(request.user.project, form, key):
            messages.success(request, u"%s bamboo dataset "
                             u"retrieved successfuly." % key_prefix)
        else:
            messages.warning(request, u"Unable to retrieve %s bamboo dataset."
                             % key_prefix)

    return response


@project_required(guests=DEFAULT_PROJECT)
def processing_center(request, pc_slug):
    context = {'category': 'pc'}

    pc_slug = pc_slug.lower()
    if not pc_slug in PROCESSING_CENTERS.keys():
        raise Http404(u"Unable to find matching Processing Center")

    arrived_pc = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_ARRIVED_AT_PC)
    left_pc = ESTSSample.all_datasets(request.user.project) \
                          .get(ESTSSample.STATUS_SENT_TO_NSTC)

    namesq = [{"pc_name": name} for name in PROCESSING_CENTERS.get(pc_slug)]
    seven_day_ago = datetime.now() - timedelta(7)

    try:
        received_data = arrived_pc.get_data(select=['scan_soil_id'],
                                            query={'$or': namesq},
                                            cache=True, cache_expiry=3600)
    except:
        received_data = []

    nb_received = len(received_data)

    try:
        nb_received_7days = len(arrived_pc.get_data(select=['pc_name'],
                                                    query={"$or": namesq,
                                                           "survey_day":
                                                            {"$gte": seven_day_ago.isoformat()}}),
                                                    cache=True, cache_expiry=3600)
    except:
        nb_received_7days = 0

    try:
        processed_data = left_pc.get_data(select=['pc_name'],
                                          query={'$or': namesq},
                                          cache=True, cache_expiry=3600)
    except:
        processed_data = []
    nb_processed = len(processed_data)

    try:
        nb_processed_7days = len(left_pc.get_data(select=['pc_name'],
                                                  query={"$or": namesq,
                                                         "survey_day":
                                                            {'$gte': seven_day_ago.isoformat()}}),
                                                  cache=True, cache_expiry=3600)
    except:
        nb_processed_7days = 0

    avg_processing = 'n/a'

    remaining_samples = list(set([e.get('scan_soil_id', None)
                                  for e in received_data]))

    for sid in (e.get('scan_soil_id', None) for e in processed_data):
        while True:
            try:
                remaining_samples.remove(sid)
            except ValueError:
                break

    context.update({'pc': pc_slug,
                    'pc_name': PROCESSING_CENTERS[pc_slug][0],
                    'nb_received': nb_received,
                    'nb_received_7days': nb_received_7days,
                    'nb_processed': nb_processed,
                    'nb_processed_7days': nb_processed_7days,
                    'avg_processing': avg_processing,
                    'remaining_samples': remaining_samples})

    return render(request, 'pc.html', context)


@project_required(guests=DEFAULT_PROJECT)
def sample_detail(request):

    context = {'category': 'sample'}

    sample_id = request.GET.get('sid', None)

    if not sample_id:
        raise Http404(u"Incorect Sample ID.")

    try:
        sample = ESTSSample(sample_id, project=request.user.project)
        assert sample.is_valid
    except (BambooError, ErrorParsingBambooData, AssertionError):
        raise Http404(u"Unable to retrieve data about this ID.")

    context.update({'sample_id': sample_id,
                    'sample': sample})

    return render(request, 'sample_detail.html', context)


@require_POST
@csrf_exempt
def steps_form_splitter(request, project_slug='soiltrack'):
    ''' Unified (ESTS_Steps) Form to individual ones (submits to FH)

        1. Receives a JSON POST from formhub containing x samples barcode
        2. For each sample, prepare a step-specific submission
        3. Submits the resulting XForms to formhub. '''

    # we need a project to guess formhub URL
    try:
        project = Project.objects.get(slug=project_slug)
    except:
        project = Project.objects.all()[0]

    try:
        jsform = json.loads(request.raw_post_data)
    except:
        return HttpResponse(u"Unable to parse JSON data", status=400)

    # we have a json dict containing all fields.
    # we need to:
    #   1. explode the form into x ones from soil_id
    #   2. find out step
    #   2. rename all fields except barcode to prefix with step

    forms = []
    step = jsform['step']

    for soil_field in jsform['scan']:
        # looping on repeat field `scan` which contains `soil_id`
        barcode = soil_field['scan/soil_id']

        # duplicate whole form to grab meta data.
        form = copy.copy(jsform)

        # rename all fields but `_` starting ones
        keys = form.keys()
        for key in keys:
            # _ starting keys are internal.
            if key.startswith('_'):
                continue
            form['%s_%s' % (step, key)] = form[key]
            # delete key once duplicated
            form.pop(key)
        # remove repeat section and replace with `barcode`
        form.pop('scan')
        form['barcode'] = barcode

        forms.append(form)
    del(jsform)

    def json2xform(jsform):
        # changing the form_id to match correct Step
        dd = {'form_id': u'ESTS_%s' % jsform.get(u'step', u'').title()}
        xml_head = u"<?xml version='1.0' ?><%(form_id)s id='%(form_id)s'>" % dd
        xml_tail = u"</%(form_id)s>" % dd

        # remove the parent's instance ID and step
        try:
            jsform['meta'].pop('instanceID')
            jsform.pop('step')
        except KeyError:
            pass

        for field in jsform.keys():
            # treat field starting with underscore are internal ones.
            # and remove them
            if field.startswith('_'):
                jsform.pop(field)

        return xml_head + dict2xml(jsform) + xml_tail

    xforms = [json2xform(form) for form in forms]

    try:
        submit_xml_forms_formhub(project, xforms, as_bulk=False)
    except (ErrorUploadingDataToFormhub,
            ErrorMultipleUploadingDataToFormhub) as e:
        return HttpResponse(u"%(intro)s\n%(detail)s"
                            % {'intro': e,
                               'detail': e.details()}, status=502)
    except Exception as e:
        return HttpResponse(str(e), status=500)

    return HttpResponse('OK', status=201)


@require_POST
@csrf_exempt
def main_form_splitter(request, project_slug='soiltrack'):
    ''' Unified EthioSIS_ET Form to per-sample (ESTS_ET) ones (submits to FH)

        1. Receives a JSON POST from formhub containing qr_* barcodes
        2. For each level (qr), prepare a step-specific submission
        3. Submits the resulting XForms to formhub. '''

    # we need a project to guess formhub URL
    try:
        project = Project.objects.get(slug=project_slug)
    except:
        project = Project.objects.all()[0]

    try:
        jsform = json.loads(request.raw_post_data)
    except:
        return HttpResponse(u"Unable to parse JSON data", status=400)

    positions = {
        'top_qr': None,
        'sub_qr': None,
        'qr_0_20': None,
        'qr_20_40': None,
        'qr_40_60': None,
        'qr_60_80': None,
        'qr_80_100': None,
    }

    forms = []

    for key in positions.keys():
        positions[key] = jsform.get('found_%s' % key, None)
        if not re.match(r'[a-zA-Z0-9\_]+', positions[key]):
            positions[key] = None

    for position in positions.keys():
        if not positions[position]:
            continue

        # extract sample identifier
        barcode = jsform['found_%s' % position]

        # duplicate whole form to grab meta data.
        form = copy.copy(jsform)

        # delete all position keys
        for key in positions.keys():
            form.pop(key)

        # add `barcode` field
        form['barcode'] = barcode

        forms.append(form)
    del(jsform)

    def json2xform(jsform):
        # changing the form_id to match correct Step
        dd = {'form_id': u'ESTS_ET_sample'}
        xml_head = u"<?xml version='1.0' ?><%(form_id)s id='%(form_id)s'>" % dd
        xml_tail = u"</%(form_id)s>" % dd

        # remove the parent's instance ID and step
        try:
            jsform['meta'].pop('instanceID')
            jsform.pop('step')
        except KeyError:
            pass

        for field in jsform.keys():
            # treat field starting with underscore are internal ones.
            # and remove them
            if field.startswith('_'):
                jsform.pop(field)

        return xml_head + dict2xml(jsform) + xml_tail

    xforms = [json2xform(form) for form in forms]

    try:
        submit_xml_forms_formhub(project, xforms, as_bulk=False)
    except (ErrorUploadingDataToFormhub,
            ErrorMultipleUploadingDataToFormhub) as e:
        return HttpResponse(u"%(intro)s\n%(detail)s"
                            % {'intro': e,
                               'detail': e.details()}, status=502)
    except Exception as e:
        return HttpResponse(str(e), status=500)

    return HttpResponse('OK', status=201)
