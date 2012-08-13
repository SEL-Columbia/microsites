
from django.conf.urls import patterns, url


urlpatterns = patterns('',
    url(r'^$', 'reportcard.views.home', name='home'),
    url(r'^touch$', 'reportcard.views.update_data', name='touch'),
    url(r'^classes$', 'reportcard.views.list_classes', name='classes'),
    # url(r'^class/(?P<class_uuid>[a-z]+)$', 'reportcard.views.list_classes', name='classes'),
    url(r'^submissions$', 'reportcard.views.list_submissions',
        name='submissions'),
)
