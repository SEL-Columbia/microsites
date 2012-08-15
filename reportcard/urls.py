
from django.conf.urls import patterns, url
from django.views.generic.simple import direct_to_template


urlpatterns = patterns('',
    url(r'^$', 'reportcard.views.home', name='home'),
    url(r'^touch$', 'reportcard.views.update_data', name='touch'),
    url(r'^reports$', 'reportcard.views.list_reports', name='reports'),
    # url(r'^class/(?P<class_uuid>[a-z]+)$', 'reportcard.views.list_classes', name='classes'),
    url(r'^submissions$', 'reportcard.views.list_submissions',
        name='submissions'),
    url(r'^teachers$', 'reportcard.views.list_teachers', name='teachers'),
    url(r'^form$', 'reportcard.views.form', name='form'),
    url(r'^help/?$', 
        direct_to_template, {'template': 'about.html',
                             'extra_context': {'category': 'about'}},
        name='about'),
)
