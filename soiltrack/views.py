# encoding=utf-8

from django.shortcuts import render
from pybamboo import ErrorRetrievingBambooData
from django.contrib import messages

from microsite.views import options as ms_options
from microsite.utils import get_option
from microsite.bamboo import raw_getset_bamboo_dataset
from microsite.views import DEFAULT_IDS
from microsite.models import Project
from microsite.barcode import b64_qrcode
from microsite.decorators import project_required
from microsite.bamboo import Bamboo, count_submissions

from soiltrack.spid_ssid import generate_ssids
from soiltrack.utils import ensure_fixtures_ready

DEFAULT_PROJECT = Project.objects.get(slug='soiltrack')

# check-for/create datasets fixtures
ensure_fixtures_ready(DEFAULT_PROJECT)


@project_required(guests=DEFAULT_PROJECT)
def dashboard(request):
    context = {'category': 'home'}

    bamboo = Bamboo()

    def pc(num, denum):
        try:
            return float(num) / float(denum)
        except (ZeroDivisionError, TypeError, ValueError):
            return 0.0

    # total number of plots (EthioSIS_ET submissions)
    try:
        nb_plots = int(count_submissions(request.user.project, 'found_top_qr'))
    except ErrorRetrievingBambooData:
        nb_plots = None
    nb_plots = 3000

    # collected samples (ESTS1)
    try:
        ests1 = get_option(request.user.project, 'ests1_dataset')
        nb_collected = int(bamboo.info(ests1, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_collected = 0

    # being processed samples (ESTS2)
    try:
        ests2 = get_option(request.user.project, 'ests2_dataset')
        nb_processing = int(bamboo.info(ests2, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_processing = 0

    # processed samples (ESTS3)
    try:
        ests3 = get_option(request.user.project, 'ests3_dataset')
        nb_processed = int(bamboo.info(ests3, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_processed = 0

    # being analyzed samples (ESTS4)
    try:
        ests4 = get_option(request.user.project, 'ests4_dataset')
        nb_analyzing = int(bamboo.info(ests4, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_analyzing = 0

    # analyzed samples (ESTS5)
    try:
        ests5 = get_option(request.user.project, 'ests5_dataset')
        nb_analyzed = int(bamboo.info(ests5, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_analyzed = 0

    # archived samples (ESTS6)
    try:
        ests6 = get_option(request.user.project, 'ests6_dataset')
        nb_archived = int(bamboo.info(ests6, cache=True).get('num_rows', 0))
    except ErrorRetrievingBambooData:
        nb_archived = 0

    # lost/missing samples
    nb_lost = 1

    # total form submissions:
    nb_submissions = sum([nb_plots, nb_collected, nb_processing, nb_processed,
                          nb_analyzing, nb_analyzed, nb_archived])

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
                    'nb_submissions': nb_submissions})

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