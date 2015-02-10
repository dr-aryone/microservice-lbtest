from django.conf.urls import patterns, url

from queuer import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^queue', views.queue_player),
    url(r'^dequeue', views.dequeue_player),
    url(r'^report', views.report_results),
    url(r'^check', views.check),
)
