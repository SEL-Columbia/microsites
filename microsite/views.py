
import datetime

from django import forms
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.core.paginator import EmptyPage, PageNotAnInteger
from pybamboo.connection import Connection

from microsite.utils import (dump_json, load_json,
                             import_csv_content_into_namespace)
from microsite.decorators import project_required
from microsite.models import Option, KeyNamePair
from microsite.bamboo import getset_bamboo_dataset
from microsite.barcode import b64_random_qrcode, detailed_id_dict
from microsite.decorators import unconfigured_project_required
from microsite.digg_paginator import FlynsarmyPaginator
from microsite.bamboo import (get_bamboo_dataset_id, get_bamboo_url,
                              CachedDataset)


DEFAULT_IDS = 5


class JSONTextInput(forms.TextInput):

    def render(self, name, value, attrs=None):
        try:
            value = load_json(value)
        except:
            pass
        return super(JSONTextInput, self).render(name, value, attrs)


class OptionForm(forms.ModelForm):

    error_css_class = 'alert alert-error'
    required_css_class = 'alert alert-error'

    class Meta:
        model = Option
        hidden = ('key', 'name', 'project')
        # exclude = ()

    def __init__(self, *args, **kwargs):
        if 'project' in kwargs.keys():
            self._project = kwargs.pop('project')
        super(OptionForm, self).__init__(*args, **kwargs)

    def clean_project(self):
        if getattr(self, '_project', None):
            return self._project
        else:
            return self.cleaned_data.get('project')

    json_value = forms.CharField(widget=JSONTextInput, required=False)

    def clean_json_value(self):
        return dump_json(self.cleaned_data.get('json_value'))


@unconfigured_project_required
def idgen(request, nb_ids=DEFAULT_IDS):

    context = {'category': 'idgen'}

    # hard-coded max number of IDs to gen.
    try:
        nb_ids = 100 if int(nb_ids) > 100 else int(nb_ids)
    except ValueError:
        nb_ids = DEFAULT_IDS

    all_ids = []
    for i in xrange(0, nb_ids):
        # this is a tuple of (ID, B64_QRPNG)
        all_ids.append(b64_random_qrcode(as_tuple=True, as_url=True))

    context.update({'generated_ids': all_ids})

    return render(request, 'idgen.html', context)


@permission_required('option.can_edit')
def options(request):

    context = {'category': 'options'}

    if request.method == "POST":
        forms = [OptionForm(request.POST,
                            prefix=str(option),
                            instance=option,
                            project=request.user.project)
                 for option
                 in Option.objects.filter(project=request.user.project)]

        if all([of.is_valid() for of in forms]):
            for of in forms:
                of.save()

            # try to update bamboo datasets
            if getset_bamboo_dataset(request.user.project):
                messages.success(request,
                                 u"bamboo dataset retrieved successfuly.")
            else:
                messages.warning(request,
                                 u"Unable to retrieve bamboo dataset.")

            if getset_bamboo_dataset(request.user.project,
                                     is_registration=True):
                messages.success(request,
                                 u"bamboo dataset (registration) "
                                 u"retrieved successfuly.")
            else:
                messages.warning(request,
                                 u"Unable to retrieve bamboo "
                                 u"dataset (registration).")

            return redirect(options)

    else:
        forms = [OptionForm(prefix=str(option), instance=option)
                 for option
                 in Option.objects.filter(project=request.user.project)
                                  .order_by('name')]

    context.update({'forms': forms})

    return render(request, 'options.html', context)


@csrf_protect
@unconfigured_project_required
@permission_required('keynamepair.can_edit')
def key_name(request):

    context = {'category': 'key_name'}

    class UploadFileForm(forms.Form):
        title = forms.CharField(max_length=50)
        file = forms.FileField()

    if request.method == 'POST':

        namespace = request.POST.get('namespace', None)
        if (not namespace
            or not namespace in [x[0] for x in settings.KEY_NAME_NAMESPACES]):
            context.update({'namespace_invalid': True})

        uploaded_file = request.FILES.get('csv_file')
        if uploaded_file and namespace:
            try:
                import_csv_content_into_namespace(request.user.project,
                                                  namespace,
                                                  uploaded_file.read())
                messages.success(request,
                                 u"CSV file has been successfuly imported.")
                return redirect(key_name)
            except:
                context.update({'csv_file_error_parsing': True})

        else:
            context.update({'csv_file_error_missing': True})

    namespaces = []
    for ns_key, ns_name in settings.KEY_NAME_NAMESPACES:
        namespaces.append((ns_key, ns_name,
                           KeyNamePair.objects
                                      .filter(namespace=ns_key,
                                              project=request.user.project)
                                      .order_by('key')))
    context.update({'namespaces': namespaces})

    return render(request, 'key_name.html', context)


@unconfigured_project_required
def key_name_csv_export(request, namespace):

    if not namespace in [x[0] for x in settings.KEY_NAME_NAMESPACES]:
        raise Http404(u"Requested namespace (%(ns)s) does not exist."
                      % {'ns': namespace})

    response = HttpResponse(mimetype='application/csv')
    fname = (u"%(ns)s_%(date)s.csv"
             % {'ns': namespace,
                'date': datetime.datetime.now().strftime('%Y%m%d')})
    response['Content-Disposition'] = 'attachment; filename=%s' % fname
    response.write('Key,Name\n')
    for knp in (KeyNamePair.objects.filter(namespace=namespace,
                                           project=request.user.project)
                                   .order_by('key')):
        response.write('%(key)s,%(name)s\n' % {'key': knp.key,
                                               'name': knp.name})

    return response


def login_greeter(request):

    from django.contrib.auth.views import login
    from microsite.models import Project

    context = {'category': 'login',
               'projects': Project.objects.all().order_by('name')}

    return login(request, template_name='login.html', extra_context=context)


@project_required()
def list_submissions(request, id_prefix=u''):

    context = {'category': 'submissions'}

    connection = Connection(get_bamboo_url(request.user.project))
    dataset = CachedDataset(get_bamboo_dataset_id(request.user.project),
                            connection=connection)

    submissions_list = dataset.get_data()

    for submission in submissions_list:
        submission.update(detailed_id_dict(submission, prefix=id_prefix))

    paginator = FlynsarmyPaginator(submissions_list, 10, adjacent_pages=2)

    page = request.GET.get('page')
    try:
        submissions = paginator.page(page)
    except PageNotAnInteger:
        submissions = paginator.page(1)
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    context.update({'submissions': submissions})

    return render(request, 'list_submissions.html', context)
