# encoding=utf-8

import re
import json
import copy
import uuid
import time
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
from microsite.utils import get_option, nest_flat_dict
from microsite.bamboo import raw_getset_bamboo_dataset
from microsite.views import DEFAULT_IDS
from microsite.models import Project
from microsite.barcode import b64_qrcode
from microsite.decorators import project_required
from microsite.formhub import (submit_xml_forms_formhub,
                               ErrorUploadingDataToFormhub,
                               ErrorMultipleUploadingDataToFormhub)
from microsite.bamboo import (get_bamboo_url, CachedDataset)

from soiltrack.spid_ssid import generate_ssids
from soiltrack.utils import ensure_fixtures_ready
from soiltrack.sample import ESTSSample


DEFAULT_PROJECT = Project.objects.get(slug='soiltrack')

# check-for/create datasets fixtures
ensure_fixtures_ready(DEFAULT_PROJECT)


def get_ests_dataset(project):
    connection = Connection(get_bamboo_url(project))
    return CachedDataset(get_option(project, 'ests_dataset'),
                                    connection=connection)


def get_processing_centers(dataset):
    return [center for center in
            dataset.get_data(select=['step1_pc_destination'],
                             distinct='step1_pc_destination',
                             cache=True)
            if isinstance(center, basestring)]


def get_missing_trigger(request=None, ident=''):
    default = 30
    if ident.startswith('pc_') or ident.startswith('lab_'):
        default = 7
    if not request:
        return default

    try:
        return int(request.COOKIES.get(u'ests_missing_trigger_%s' % ident,
                                       default))
    except:
        return default


def set_missing_trigger(response, ident, value):
    response.set_cookie('ests_missing_trigger_%s' % ident, value)


@project_required(guests=DEFAULT_PROJECT)
def dashboard(request):
    context = {'category': 'home'}

    # init bamboo datasets
    dataset = get_ests_dataset(request.user.project)

    def pc(num, denum):
        try:
            return float(num) / float(denum)
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0

    # total number of plots (EthioSIS_ET submissions)
    try:
        nb_plots = dataset.get_data(select=['plot'],
                                    distinct='plot',
                                    count=True,
                                    cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_plots = 0

    def count_submission_in_step(step):
        try:
            field = "step%d_survey_day" % step
            if step == 0:
                field = "end"
            query = {field: {"$gt": 0}}
            return dataset.get_data(query=query,
                                    select=['barcode'],
                                    count=True,
                                    cache=True)
        except (BambooError, ErrorParsingBambooData):
            return 0

    # missing trigger from cookie
    ests_missing_trigger = get_missing_trigger(request, 'dashboard')
    new_missing_trigger = request.GET.get('trigger', None)
    if new_missing_trigger:
        try:
            ests_missing_trigger = int(new_missing_trigger)
        except:
            new_missing_trigger = False

    # nb sent from fields
    nb_sent_from_field = dataset.get_data(query={"barcode": {"$exists": True}},
                                          select=['barcode'],
                                          count=True,
                                          cache=True)

    # collected samples
    nb_collected = count_submission_in_step(0)

    # received samples (ESTS1)
    nb_received = count_submission_in_step(1)

    # being processed samples (ESTS2)
    # nb_processing = count_submission_in_step(2)
    nb_processing = dataset.get_data(query={"step2_survey_day": {"$gt": 0},
                                            "position": {"$in": ["top_qr",
                                                                 "sub_qr"]}},
                                     select=['barcode'],
                                     count=True,
                                     cache=True)

    # processed samples (ESTS3)
    nb_processed = count_submission_in_step(3)

    # being analyzed samples (ESTS4)
    nb_analyzing = count_submission_in_step(4)

    # analyzed samples (ESTS5)
    nb_analyzed = count_submission_in_step(5)

    # archived samples (ESTS6)
    nb_archived = count_submission_in_step(6)

    # total form submissions:
    nb_submissions = sum([nb_plots, nb_collected, nb_processing, nb_processed,
                          nb_analyzing, nb_analyzed, nb_archived])

    processing_centers = get_processing_centers(dataset)

    # confluence points
    confluence_points = []
    for cp in dataset.get_data(query={"block": {"$exists": True}},
                                         distinct='block',
                                         select=['block'],
                                         cache=True):
        try:
            i = int(cp)
            if not i in confluence_points:
                confluence_points.append(i)
        except:
            continue

    # last events
    last_events = []
    last_events_id = []
    for field in ('end', 'step1_end_time', 'step2_end_time',
                    'step3_end_time', 'step4_end_time', 'step5_end_time',
                    'step6_end_time'):

        last_ten = dataset.get_data(order_by='-%s' % field, limit=10,
                                    select=['barcode', field],
                                    cache=True, cache_expiry=60 * 60 * 5)
        if isinstance(last_ten, list):
            last_events_id += last_ten

    last_events_id.sort(key=lambda e: e.get('end_time'), reverse=True)
    last_events_id = last_events_id[:9]

    for event in last_events_id:
        try:
            sample = ESTSSample(event.get(u'barcode'),
                                project=request.user.project)
            last_events.append(sample)
        except ValueError:
            pass

    # missing samples by PC
    # TODO: use bamboo calculation when it'll be working.
    # add_calclation(name='proc_delay', formula='step3_end_time - step2_end_time')
    missings = {pc: 0 for pc in processing_centers}
    trigger_day_ago = time.mktime((datetime.now()
                                  - timedelta(ests_missing_trigger)).timetuple())
    for center in missings.keys():
        try:
            query = {"step2_end_time": {"$lte": trigger_day_ago},
                     "step2_processing_center": center}
            nb_missing = dataset.get_data(query=query,
                                          select=['barcode'],
                                          count=True,
                                          cache=True)
        except (BambooError, ErrorParsingBambooData):
            nb_missing = 0
        missings[center] = nb_missing

    # lost/missing samples
    nb_lost = sum(missings.values())

    context.update({'nb_plots': nb_plots,
                    'nb_sent_from_field': nb_sent_from_field,
                    'nb_collected': nb_collected,
                    'pc_collected': pc(nb_collected, nb_sent_from_field),
                    'nb_received': nb_received,
                    'pc_received': pc(nb_received, nb_collected),
                    'nb_processed': nb_processed,
                    'pc_processed': pc(nb_processed, nb_processing),
                    'nb_analyzed': nb_analyzed,
                    'pc_analyzed': pc(nb_analyzed, nb_collected),
                    'nb_lost': nb_lost,
                    'pc_lost': pc(nb_lost, nb_collected),
                    'nb_processing': nb_processing,
                    'nb_analyzing': nb_analyzing,
                    'nb_archived': nb_archived,
                    'nb_submissions': nb_submissions,
                    'last_events': last_events,
                    'processing_centers': processing_centers,
                    'ests_missing_trigger': ests_missing_trigger,
                    'missings': missings,
                    'confluence_points': confluence_points})

    response = render(request, 'dashboard.html', context)
    if new_missing_trigger:
        set_missing_trigger(response, 'dashboard', new_missing_trigger)
    return response


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

    dataset = get_ests_dataset(request.user.project)
    processing_centers = get_processing_centers(dataset)

    if not pc_slug in processing_centers:
        raise Http404(u"Unable to find matching Processing Center")

    # missing trigger from cookie
    ests_missing_trigger = get_missing_trigger(request, 'pc_%s' % pc_slug)
    new_missing_trigger = request.GET.get('trigger', None)
    if new_missing_trigger:
        try:
            ests_missing_trigger = int(new_missing_trigger)
        except:
            new_missing_trigger = False

    # seven_day_ago = time.mktime((datetime.now() - timedelta(7)).timetuple())
    trigger_day_ago = time.mktime((datetime.now()
                                  - timedelta(ests_missing_trigger)).timetuple())

    try:
        query = {"step2_end_time": {"$gt": 0},
                 "step2_processing_center": pc_slug}
        nb_received = dataset.get_data(query=query,
                                       select=['barcode'],
                                       count=True,
                                       cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_received = 0

    try:
        query = {"step2_end_time": {"$gte": trigger_day_ago},
                 "step2_processing_center": pc_slug}
        nb_received_7days = dataset.get_data(query=query,
                                             select=['barcode'],
                                             count=True,
                                             cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_received_7days = 0

    try:
        query = {"step3_end_time": {"$gt": 0},
                 "step2_processing_center": pc_slug}
        nb_processed = dataset.get_data(query=query,
                                        select=['barcode'],
                                        count=True,
                                        cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_processed = 0

    try:
        query = {"step3_end_time": {"$gte": trigger_day_ago},
                 "step2_processing_center": pc_slug}
        nb_processed_7days = dataset.get_data(query=query,
                                              select=['barcode'],
                                              count=True,
                                              cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_processed_7days = 0

    # TODO: retry with pybamboo.
    # at this time, I can't make mean(step3_surey_day - step2_survey_day)
    # to work as expected
    def duration_step(data):
        try:
            return (data['step3_end_time'] - data['step2_end_time']).days
        except TypeError:
            return None
    durations = [duration_step(data)
                 for data in
                 dataset.get_data(query={"step2_processing_center": pc_slug},
                                  select=['step3_end_time',
                                         'step2_end_time', ],
                                  cache=True)
                 if duration_step(data) is not None]

    try:
        avg_processing = reduce(lambda x, y: x + y, durations) / len(durations)
    except TypeError:
        avg_processing = u"n/a"

    query = {"$or": [{"step2_processing_center": pc_slug},
                     {"step1_pc_destination": pc_slug}]}
    sites = [d['block'] for d in
             dataset.get_data(query=query, select=['block'])]
    sites = [int(b) for b in list(set(sites))]
    try:
        sites.remove(0)
    except:
        pass

    dest_and_arrived = dataset.get_data(query={"$or": [{"step1_pc_destination": pc_slug},
                                                       {"step2_processing_center": pc_slug}]},
                                         select=['barcode',
                                                 'step1_pc_destination',
                                                 'step2_processing_center',
                                                 'step1_survey_day'],
                                         cache=True)
    remaining_samples = []
    for sample in dest_and_arrived:
        if (sample['step1_pc_destination'] != sample['step2_processing_center']
            and sample['step1_pc_destination'] != "null"):
            if not sample['barcode'] in remaining_samples:
                remaining_samples.append(sample['barcode'])

    context.update({'pc': pc_slug,
                    'nb_received': nb_received,
                    'nb_received_7days': nb_received_7days,
                    'nb_processed': nb_processed,
                    'nb_processed_7days': nb_processed_7days,
                    'avg_processing': avg_processing,
                    'remaining_samples': remaining_samples,
                    'sites': sites,
                    'ests_missing_trigger': ests_missing_trigger,
                    })

    response = render(request, 'pc.html', context)
    if new_missing_trigger:
        set_missing_trigger(response, str(u'pc_%s' % pc_slug),
                            new_missing_trigger)
    return response


@project_required(guests=DEFAULT_PROJECT)
def nstc_lab(request):
    context = {'category': 'pc'}

    dataset = get_ests_dataset(request.user.project)

    # missing trigger from cookie
    ests_missing_trigger = get_missing_trigger(request, 'lab_nstc')
    new_missing_trigger = request.GET.get('trigger', None)
    if new_missing_trigger:
        try:
            ests_missing_trigger = int(new_missing_trigger)
        except:
            new_missing_trigger = False

    # seven_day_ago = time.mktime((datetime.now() - timedelta(7)).timetuple())
    trigger_day_ago = time.mktime((datetime.now()
                                  - timedelta(ests_missing_trigger)).timetuple())

    try:
        query = {"step4_end_time": {"$gt": 0}}
        nb_received = dataset.get_data(query=query,
                                       select=['barcode'],
                                       count=True,
                                       cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_received = 0

    try:
        query = {"step4_end_time": {"$gte": trigger_day_ago}}
        nb_received_7days = dataset.get_data(query=query,
                                             select=['barcode'],
                                             count=True,
                                             cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_received_7days = 0

    try:
        query = {"step5_end_time": {"$gt": 0}}
        nb_processed = dataset.get_data(query=query,
                                        select=['barcode'],
                                        count=True,
                                        cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_processed = 0

    try:
        query = {"step5_end_time": {"$gte": trigger_day_ago}}
        nb_processed_7days = dataset.get_data(query=query,
                                              select=['barcode'],
                                              count=True,
                                              cache=True)
    except (BambooError, ErrorParsingBambooData):
        nb_processed_7days = 0

    # TODO: retry with pybamboo.
    # at this time, I can't make mean(step3_surey_day - step2_survey_day)
    # to work as expected
    def duration_step(data):
        try:
            return (data['step5_end_time'] - data['step4_end_time']).days
        except TypeError:
            return None
    durations = [duration_step(data)
                 for data in
                 dataset.get_data(select=['step5_end_time',
                                          'step4_end_time', ],
                                  cache=True)
                 if duration_step(data) is not None]

    try:
        avg_processing = reduce(lambda x, y: x + y, durations) / len(durations)
    except TypeError:
        avg_processing = u"n/a"

    remaining_samples = [elem.get('barcode') for elem in
                         dataset.get_data(query={"$and": [
                                                    {"position": {"$in": ["top_qr", "sub_qr"]},
                                                     "step4_end_time": {"$not": {"$gt": 0}}}]},
                                         select=['barcode'],
                                         cache=True)]

    context.update({'pc': None,
                    'nb_received': nb_received,
                    'nb_received_7days': nb_received_7days,
                    'nb_processed': nb_processed,
                    'nb_processed_7days': nb_processed_7days,
                    'avg_processing': avg_processing,
                    'remaining_samples': remaining_samples,
                    'ests_missing_trigger': ests_missing_trigger,
                    })

    response = render(request, 'pc.html', context)
    if new_missing_trigger:
        set_missing_trigger(response, 'lab_nstc', new_missing_trigger)
    return response


@project_required(guests=DEFAULT_PROJECT)
def location(request, cp):
    context = {'category': 'cp'}

    dataset = get_ests_dataset(request.user.project)

    today = datetime.today()
    nb_collected_total = dataset.get_data(query={"block": float(cp)},
                                          count=True, cache=True)
    nb_collected_today = dataset.get_data(query={"$and": [{"block": cp},
                                                          {"end": today.isoformat()}]},
                                          count=True, cache=True)
    last_collection = dataset.get_data(query={"block": float(cp)},
                                       order_by='end',
                                       select=['end', 'barcode'], limit=1)[0]
    average_collected = 1
    nb_collected_day_1 = 1
    nb_collected_day_2 = 1
    nb_collected_day_3 = 1

    context.update({'cp': cp,
                    'nb_collected_total': nb_collected_total,
                    'nb_collected_today': nb_collected_today,
                    'average_collected': average_collected,
                    'nb_collected_day_1': nb_collected_day_1,
                    'nb_collected_day_2': nb_collected_day_2,
                    'nb_collected_day_3': nb_collected_day_3,
                    'last_collection': last_collection,
                    'today': today})

    response = render(request, 'cp.html', context)
    return response


@project_required(guests=DEFAULT_PROJECT)
def sample_detail(request):

    context = {'category': 'sample'}

    sample_id = request.GET.get('sid', None)
    plot_id = request.GET.get('plot_id', None)

    # Search by Plot request
    if plot_id and not sample_id:
        dataset = get_ests_dataset(request.user.project)
        try:
            block, quadrant, cluster, plot = plot_id.split('.')
            block = float(block)
            quadrant = float(quadrant)
            cluster = float(cluster)
            plot = float(plot)
        except:
            raise Http404(u"Incorect Plot ID.")

        results = dataset.get_data(query={'block': block,
                                          'quadrant': quadrant,
                                          'cluster': cluster,
                                          'plot': plot},
                                   select=['barcode', 'position'])

        try:
            sample_id = results[0].get('barcode')
        except:
            raise Http404(u"Unable to find samples matching this Plot.")

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
        # re-organize JSON to match semantic
        nest_flat_dict(jsform)
    except:
        return HttpResponse(u"Unable to parse JSON data", status=400)

    # we have a json dict containing all fields.
    # we need to:
    #   1. explode the form into x ones from soil_id
    #   2. find out step
    #   2. rename all fields except barcode to prefix with step

    forms = []
    step = jsform[u'step']

    for soil_field in jsform[u'scan']:
        # looping on repeat field `scan` which contains `soil_id`
        barcode = soil_field[u'scan/soil_id']

        # duplicate whole form to grab meta data.
        form = copy.deepcopy(jsform)

        # rename all fields but `_` starting ones
        keys = form.keys()
        for key in keys:
            # _ starting keys are internal.
            if key.startswith('_'):
                continue
            form.update({'%s_%s' % (step, key): form[key]})
            # delete key once duplicated
            form.pop(key)
        # remove repeat section and replace with `barcode`
        form.pop(u'%s_scan' % step)
        form.update({u'barcode': barcode})

        forms.append(form)
    del(jsform)

    def json2xform(jsform):
        # changing the form_id to match correct Step
        dd = {'form_id': u'ESTS_%s' % step.title()}
        xml_head = u"<?xml version='1.0' ?><%(form_id)s id='%(form_id)s'>" % dd
        xml_tail = u"</%(form_id)s>" % dd

        # remove the parent's instance ID and step
        try:
            jsform['%s_meta' % step].pop('instanceID')
            # jsform['%s_formhub' % step].pop('uuid')
            jsform.pop('%s_step' % step)
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
        submit_xml_forms_formhub(project, xforms, as_bulk=True)
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
        # re-organize JSON to match semantic
        nest_flat_dict(jsform)
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
    found = bool(len(jsform.get(u'found', {})) > 1)

    for key in positions.keys():
        positions[key] = jsform.get(u'found', {}).get(key, '')
        if not re.match(r'[a-zA-Z0-9\_\-]+', positions[key]):
            positions[key] = None

    # delete all position keys
    for key in positions.keys():
        try:
            jsform[u'found'].pop(key)
        except KeyError:
            pass

    for position in positions.keys():
        if not positions[position]:
            continue

        # extract sample identifier
        barcode = positions.get(position)

        # duplicate whole form to grab meta data.
        form = copy.deepcopy(jsform)

        # add `barcode` field
        form[u'barcode'] = barcode
        form[u'position'] = position

        forms.append(form)

    if not found:
        # make a single submission since we don't have barcodes
        form = copy.deepcopy(jsform)
        form[u'barcode'] = u'n/a__%s' % uuid.uuid4().hex
        form[u'position'] = u'not_found'
        forms.append(form)

    # free some mem
    del(jsform)

    def json2xform(jsform):
        # changing the form_id to match correct Step
        dd = {'form_id': u'ESTS_ET_sample'}
        xml_head = u"<?xml version='1.0' ?><%(form_id)s id='%(form_id)s'>" % dd
        xml_tail = u"</%(form_id)s>" % dd

        # remove the parent's instance ID and step
        try:
            jsform[u'meta'].pop('instanceID')
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
        submit_xml_forms_formhub(project, xforms, as_bulk=True)
    except (ErrorUploadingDataToFormhub,
            ErrorMultipleUploadingDataToFormhub) as e:
        return HttpResponse(u"%(intro)s\n%(detail)s"
                            % {'intro': e,
                               'detail': e.details()}, status=502)
    except Exception as e:
        return HttpResponse(str(e), status=500)

    return HttpResponse('OK', status=201)
