
from django.shortcuts import render
from django.contrib.auth.decorators import permission_required

from microsite.decorators import login_maybe_required
from microsite.barcode import b64_random_qrcode


DEFAULT_IDS = 5


@login_maybe_required
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
        all_ids.append(b64_random_qrcode(as_tuple=True))

    context.update({'generated_ids': all_ids})

    return render(request, 'idgen.html', context)


from django import forms
from microsite.models import Option

class OptionForm(forms.ModelForm):

    error_css_class = 'alert alert-error'
    required_css_class = 'alert alert-error'

    class Meta:
        model = Option
        hidden = ('key')

    json_value = forms.CharField(widget=forms.TextInput, required=False)


@permission_required('option.can_edit')
def options(request):

    context = {'category': 'options'}

    if request.method == "POST":
        forms = [OptionForm(request.POST, prefix=str(option), instance=option) for option in Option.objects.all()]

        if all([of.is_valid() for of in forms]):
            print('VALID')
            for of in forms:
                of.save()
            # return HttpResponseRedirect('/polls/add/')
        else:
            print('INVALID')
            for of in forms:
                print(of)
                print(of.errors)
    else:
        forms = [OptionForm(prefix=str(option), instance=option) for option in Option.objects.all()]
    # return render_to_response('add_poll.html', )

    context.update({'forms': forms})

    return render(request, 'options.html', context)