# encoding=utf-8

from django.shortcuts import render

from microsite.views import DEFAULT_IDS
from microsite.decorators import project_required
from microsite.barcode import b64_qrcode
from soillab.spid_ssid import generate_ssids


@project_required
def samples_list(request, search_string=None):
    context = {}

    return render(request, 'samples_list.html', context)


@project_required
def sample_detail(request, sample_id):
    context = {}
    
    return render(request, 'sample_detail.html', context)


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
        all_ids.append((ssid, b64_qrcode(ssid)))

    context.update({'generated_ids': all_ids})

    return render(request, 'idgen.html', context)


def form_splitter(request):
    ''' Master XForm to Sub XFrom

        1. Receives a grouped JSON POST from formhub containing A-Z sample data
        2. Extract and transform data for each sample into a new XForm
        3. Submits the resulting XForms to formhub. '''

    print(request.raw_post_data)
    with open('/tmp/toto.json') as f:
        f.write(request.raw_post_data)
    
    from pprint import pprint as pp ; pp(request.raw_post_data)