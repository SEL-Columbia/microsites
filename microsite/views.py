
from django import forms
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect

from microsite.utils import dump_json, load_json
from microsite.models import Option
from microsite.bamboo import getset_bamboo_dataset
from microsite.barcode import b64_random_qrcode
from microsite.decorators import unconfigured_project_required


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
        hidden = ('key', 'name')
        exclude = ('project',)

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
        forms = [OptionForm(request.POST, prefix=str(option), instance=option) 
                 for option
                 in Option.objects.filter(project=request.user.project)]

        if all([of.is_valid() for of in forms]):
            for of in forms:
                of.save()

            # try to update bamboo datasets
            getset_bamboo_dataset(request.user.project)
            getset_bamboo_dataset(request.user.project, is_registration=True)

            return redirect(options)

    else:
        forms = [OptionForm(prefix=str(option), instance=option) 
                 for option 
                 in Option.objects.filter(project=request.user.project)
                                  .order_by('name')]

    context.update({'forms': forms})

    return render(request, 'options.html', context)


def login_greeter(request):

    from django.contrib.auth.views import login
    from microsite.models import Project

    context = {'category': 'login',
               'projects': Project.objects.all().order_by('name')}

    return login(request, template_name='login.html', extra_context=context)