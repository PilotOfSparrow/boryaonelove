from django.conf.urls import url

from . import views

app_name = 'firstwin'

urlpatterns = [
        url(r'^$', views.index_view, name='index'),
        url(r'^logout/$', views.logout_view, name='logout'),
        url(r'^home/$', views.home_view, name='home'),
        url(r'^result/$', views.result_view, name='result'),
        url(r'^history/$', views.history_view, name='history'),
        url(r'^history/(?P<repository>[\w-]+)/(?P<time>[\d-]+)$', views.search_detail_view, name='search_detail'),
        url(r'^history/(?P<repository>[\w-]+)/(?P<time>[\d-]+)/(?P<file_name>(\.\/)?[\w-]+\.[\w-]+)$',
            views.show_defects_view, name='show_defects'),
        ]
