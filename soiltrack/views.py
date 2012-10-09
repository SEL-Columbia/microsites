# encoding=utf-8

from django.shortcuts import render
from pybamboo import ErrorRetrievingBambooData

from microsite.views import DEFAULT_IDS
from microsite.models import Project
from microsite.barcode import b64_qrcode
from microsite.decorators import project_required
from microsite.bamboo import Bamboo

from soiltrack.spid_ssid import generate_ssids

DEFAULT_PROJECT = Project.objects.get(slug='soiltrack')


@project_required(guests=DEFAULT_PROJECT)
def dashboard(request):
    context = {'category': 'home'}

    bamboo = Bamboo()

    # total number of plots (EthioSIS_ET submissions)
    ethiosis_ds = '6f4e2e5cf11e4117b8d1fcd9fb2051a4'
    try:
        nb_plots = int(bamboo.count_submissions(ethiosis_ds, 'found_top_qr'))
    except ErrorRetrievingBambooData:
        nb_plots = None

    context.update({'nb_plots': nb_plots})

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