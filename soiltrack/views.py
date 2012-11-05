# encoding=utf-8

from django.shortcuts import render
from pybamboo import ErrorRetrievingBambooData
from django.contrib import messages
from django.http import Http404

from microsite.views import options as ms_options
from microsite.utils import get_option
from microsite.bamboo import raw_getset_bamboo_dataset
from microsite.views import DEFAULT_IDS
from microsite.models import Project
from microsite.barcode import b64_qrcode
from microsite.decorators import project_required
from microsite.bamboo import Bamboo, get_bamboo_dataset_id, get_bamboo_url

from soiltrack.spid_ssid import generate_ssids
from soiltrack.utils import ensure_fixtures_ready

DEFAULT_PROJECT = Project.objects.get(slug='soiltrack')

PROCESSING_CENTERS = {
    'awassa': (u"awassa", u"hawassa soil lab",
               u"hawassa soil testing laboratory"),
    'nekempte': (u"nekempte"),
    'jimma': (u"jimma", u"jima"),
    'nstc_pc': (u"nstc pc", u"nstc"),
    'bar_hadir': (u"bar hadir"),
    'dessie': (u"dessie"),
    'mekelle': (u"mekelle"),
}

# check-for/create datasets fixtures
ensure_fixtures_ready(DEFAULT_PROJECT)


@project_required(guests=DEFAULT_PROJECT)
def dashboard(request):
    context = {'category': 'home'}

    # init bamboo with user's URL
    project = request.user.project
    bamboo = Bamboo(get_bamboo_url(project))
    main_dataset = get_bamboo_dataset_id(project)

    def pc(num, denum):
        try:
            return float(num) / float(denum)
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0

    # total number of plots (EthioSIS_ET submissions)
    try:
        nb_plots = int(bamboo.count_submissions(main_dataset,
                                                'found_top_qr', cache=True))
    except ErrorRetrievingBambooData:
        nb_plots = None

    # collected samples (ESTS1)
    try:
        ests1 = get_option(project, 'ests1_dataset')
        nb_collected = int(bamboo.info(ests1, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_collected = 0

    # being processed samples (ESTS2)
    try:
        ests2 = get_option(project, 'ests2_dataset')
        nb_processing = int(bamboo.info(ests2, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_processing = 0

    # processed samples (ESTS3)
    try:
        ests3 = get_option(project, 'ests3_dataset')
        nb_processed = int(bamboo.info(ests3, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_processed = 0

    # being analyzed samples (ESTS4)
    try:
        ests4 = get_option(project, 'ests4_dataset')
        nb_analyzing = int(bamboo.info(ests4, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_analyzing = 0

    # analyzed samples (ESTS5)
    try:
        ests5 = get_option(project, 'ests5_dataset')
        nb_analyzed = int(bamboo.info(ests5, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_analyzed = 0

    # archived samples (ESTS6)
    try:
        ests6 = get_option(project, 'ests6_dataset')
        nb_archived = int(bamboo.info(ests6, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_archived = 0

    # lost/missing samples
    nb_lost = 1

    # total form submissions:
    nb_submissions = sum([nb_plots, nb_collected, nb_processing, nb_processed,
                          nb_analyzing, nb_analyzed, nb_archived])

    last_events = []
    for dataset in (ests1, ests2, ests3, ests4, ests5, ests6):
        print(dataset)
        try:
            last_events.append(bamboo.query(dataset,
                                            order_by='-end_time', limit=10))
        except:
            continue
    last_events.sort(key=lambda e: e.get('end_time'), reverse=True)
    last_events = last_events[:9]

    from pprint import pprint as pp ; pp(last_events)

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
                    'last_events': last_events})

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

    # init bamboo with user's URL
    project = request.user.project
    bamboo = Bamboo(get_bamboo_url(project))
    main_dataset = get_bamboo_dataset_id(project)

    pc_slug = pc_slug.lower()
    if not pc_slug in PROCESSING_CENTERS.keys():
        raise Http404(u"Unable to find matching Processing Center")


    def find_pc_from_slug(slug):

        for center_id, names in PROCESSING_CENTERS.items():
            if slug in names:
                return center_id
        return None


    # being processed samples (ESTS2)
    try:
        ests2 = get_option(project, 'ests2_dataset')
        processing = bamboo.query(ests2, cache=True)
    except ErrorRetrievingBambooData:
        processing = []


    from pprint import pprint as pp ; pp([pc.get('pc_name').lower() for pc in processing if pc.get('pc_name')])

    # processed samples (ESTS3)
    try:
        ests3 = get_option(project, 'ests3_dataset')
        processed = bamboo.query(ests3, cache=True)
    except ErrorRetrievingBambooData:
        processed = []

    from pprint import pprint as pp ; pp([pc.get('pc_name').lower() for pc in processed if pc.get('pc_name')])

    # center = find_pc_from_slug('hey')

    nb_received = 30
    nb_received_7days = 10
    nb_processed = 9
    nb_processed_7days = 7
    avg_processing = 3.17

    context.update({'pc': pc_slug,
                    'nb_received': nb_received,
                    'nb_received_7days': nb_received_7days,
                    'nb_processed': nb_processed,
                    'nb_processed_7days': nb_processed_7days,
                    'avg_processing': avg_processing})

    return render(request, 'pc.html', context)


@project_required(guests=DEFAULT_PROJECT)
def sample_detail(request):

    context = {'category': 'sample'}

    sample_id = request.GET.get('sid', None)

    if not sample_id:
        raise Http404(u"Incorect Sample ID.")

    # Find Sample in all datasets.
    # build the SM of the sample
    # Maybe add durations to each steps?


    context.update({'sample_id': sample_id})

    return render(request, 'sample_detail.html', context)
