
from django.conf.urls import patterns, url
from django.views.generic.simple import direct_to_template


urlpatterns = patterns('',
    url(r'^$', 'reportcard.views.home', name='home'),
    url(r'^touch$', 'reportcard.views.update_data', name='touch'),
    url(r'^submissions$', 'reportcard.views.list_submissions',
        name='submissions'),
    url(r'^teachers$', 'reportcard.views.list_teachers', name='teachers'),
    url(r'^teachers/(?P<uid>[a-z0-9]+)$', 
        'reportcard.views.detail_teacher', name='teacher'),
    url(r'^teachers/(?P<uid>[a-z0-9]+)/card$', 
        'reportcard.views.card_teacher', name='teacher_card'),
    url(r'^form$', 'reportcard.views.form', name='form'),
    url(r'^help/?$', 
        direct_to_template, {'template': 'about.html',
                             'extra_context': {'category': 'about'}},
        name='about'),
)
