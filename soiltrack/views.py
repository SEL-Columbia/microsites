# encoding=utf-8

from django.shortcuts import render
# from pybamboo import ErrorRetrievingBambooData
from django.contrib import messages
from django.http import Http404
from pybamboo.connection import Connection
from pybamboo.exceptions import BambooError, ErrorParsingBambooData

from microsite.views import options as ms_options
from microsite.utils import get_option
from microsite.bamboo import raw_getset_bamboo_dataset
from microsite.views import DEFAULT_IDS
from microsite.models import Project
from microsite.barcode import b64_qrcode
from microsite.decorators import project_required
from microsite.bamboo import get_bamboo_dataset_id, get_bamboo_url, CachedDataset

from soiltrack.spid_ssid import generate_ssids
from soiltrack.utils import ensure_fixtures_ready
from soiltrack.sample import ESTSSample


DEFAULT_PROJECT = Project.objects.get(slug='soiltrack')

PROCESSING_CENTERS = {
    'awassa': (u"awassa", u"hawassa soil lab",
               u"hawassa soil testing laboratory"),
    'nekempte': (u"nekempte",),
    'jimma': (u"jimma", u"jima"),
    'nstc_pc': (u"nstc pc", u"nstc"),
    'bar_hadir': (u"bar hadir",),
    'dessie': (u"dessie",),
    'mekelle': (u"mekelle",),
}

# check-for/create datasets fixtures
ensure_fixtures_ready(DEFAULT_PROJECT)


@project_required(guests=DEFAULT_PROJECT)
def dashboard(request):
    context = {'category': 'home'}

    # init bamboo with user's URL
    project = request.user.project
    connection = Connection(get_bamboo_url(project))
    # main_dataset = CachedDataset(get_bamboo_dataset_id(project), connection=connection)
    main_dataset = CachedDataset(u'ddc7943d6d284b7dadc1b02de39f33eb', connection=connection)

    def pc(num, denum):
        try:
            return float(num) / float(denum)
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0

    # total number of plots (EthioSIS_ET submissions)
    try:
        nb_plots = int(main_dataset.count('found_top_qr', cache=True))
    except (BambooError, ErrorParsingBambooData):
        nb_plots = None

    # collected samples (ESTS1)
    try:
        # ests1 = CachedDataset(get_option(project, 'ests1_dataset'), connection=connection)
        ests1 = CachedDataset(u'1a889141be2d4264b4b4bb77b33d330d', connection=connection)
        nb_collected = int(ests1.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_collected = 0

    # being processed samples (ESTS2)
    try:
        # ests2 = CachedDataset(get_option(project, 'ests2_dataset'), connection=connection)
        ests2 = CachedDataset(u'bf56cd8eb1054df287dc0a1350677231', connection=connection)
        nb_processing = int(ests2.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_processing = 0

    # processed samples (ESTS3)
    try:
        # ests3 = CachedDataset(get_option(project, 'ests3_dataset'), connection=connection)
        ests3 = CachedDataset(u'33a6530d513242d9af9683146e69a5a3', connection=connection)
        nb_processed = int(ests3.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_processed = 0

    # being analyzed samples (ESTS4)
    try:
        # ests4 = CachedDataset(get_option(project, 'ests4_dataset'), connection=connection)
        ests4 = CachedDataset(u'd32110b1706945e7ab276f6e7e23b194', connection=connection)
        nb_analyzing = int(ests4.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_analyzing = 0

    # analyzed samples (ESTS5)
    try:
        ests5 = CachedDataset(get_option(project, 'ests5_dataset'), connection=connection)
        ests5 = CachedDataset(u'none', connection=connection)
        nb_analyzed = int(ests5.get_info(cache=True).get('num_rows', 0))
    except (BambooError, ErrorParsingBambooData):
        nb_analyzed = 0

    # archived samples (ESTS6)
    try:
        # ests6 = CachedDataset(get_option(project, 'ests6_dataset'), connection=connection)
        ests6 = CachedDataset(u'3021738ddad04a8d9195db5bd119a5c8', connection=connection)
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
        print(u'%s dataset: %s' % (ds_type, dataset))

        last_ten = dataset.get_data(order_by='-end_time', limit=10, select=['scan_soil_id', 'end_time'], cache=True, cache_expiry=60 * 60 * 5)
        if isinstance(last_ten, list):
            last_events_id += last_ten

    last_events_id.sort(key=lambda e: e.get('end_time'), reverse=True)
    last_events_id = last_events_id[:9]
    for event in last_events_id:
        try:
            print('Trying sample %s' % event.get(u'scan_soil_id'))
            sample = ESTSSample(event.get(u'scan_soil_id'))
            print('sample: %s' % sample.__str__())
            last_events.append(sample)
        except ValueError as e:
            print('ValueError: %s' % e)

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
                    'processing_centers': [(k, v[0]) for k, v in PROCESSING_CENTERS.items()]})

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

    from pybamboo.dataset import Dataset

    # init bamboo with user's URL
    project = request.user.project
    connection = Connection(get_bamboo_url(request.user.project), debug=True)
    plot_dataset = CachedDataset(u'ddc7943d6d284b7dadc1b02de39f33eb',
                                 connection=connection)

    pc_slug = pc_slug.lower()
    if not pc_slug in PROCESSING_CENTERS.keys():
        raise Http404(u"Unable to find matching Processing Center")


    def find_pc_from_slug(slug):

        for center_id, names in PROCESSING_CENTERS.items():
            if slug in names:
                return center_id
        return None


    arrived_pc = Dataset(u'bf56cd8eb1054df287dc0a1350677231',
                               connection=connection)
    left_pc = CachedDataset(u'33a6530d513242d9af9683146e69a5a3',
                            connection=connection)

    # # being processed samples (ESTS2)
    # try:
    #     ests2 = get_option(project, 'ests2_dataset')
    #     processing = bamboo.query(ests2, cache=True)
    # except (BambooError, ErrorParsingBambooData):
    #     processing = []


    # # from pprint import pprint as pp ; pp([pc.get('pc_name').lower() for pc in processing if pc.get('pc_name')])

    # # processed samples (ESTS3)
    # try:
    #     ests3 = get_option(project, 'ests3_dataset')
    #     processed = bamboo.query(ests3, cache=True)
    # except (BambooError, ErrorParsingBambooData):
    #     processed = []

    # from pprint import pprint as pp ; pp([pc.get('pc_name').lower() for pc in processed if pc.get('pc_name')])

    # center = find_pc_from_slug('hey')

    try:
        nb_received = len(arrived_pc.get_data(query={"pc_name": pc_slug}))
    except TypeError:
        nb_received = 0

    nb_received_7days = 10
    nb_processed = 9
    nb_processed_7days = 7
    avg_processing = 3.17

    context.update({'pc': pc_slug,
                    'pc_name': PROCESSING_CENTERS[pc_slug][0],
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

    try:
        sample = ESTSSample(sample_id)
        assert sample.is_valid
    except (BambooError, ErrorParsingBambooData, AssertionError):
        raise Http404(u"Unable to retrieve data about this ID.")

    connection = Connection(get_bamboo_url(request.user.project))
    plot_dataset = CachedDataset(u'ddc7943d6d284b7dadc1b02de39f33eb',
                                 connection=connection)

    context.update({'sample_id': sample_id,
                    'sample': sample})

    # from pprint import pprint as pp ; pp(sample.events())

    # from pprint import pprint as pp ; pp(sample.plot)

    return render(request, 'sample_detail.html', context)
