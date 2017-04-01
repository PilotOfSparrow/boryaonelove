from django.conf.urls import url

from . import views

app_name = 'firstwin'

urlpatterns = [
        url(r'^$', views.index, name='index'),
        url(r'^home/$', views.home, name='home'),
        url(r'^history/$', views.history, name='history'),
        url(r'^history/(?P<repository>[\w-]+)/(?P<time>[\d-]+)$', views.search_detail, name='search_detail'),
        ]

# url(r'^(?P<repository>[\w-]+)/(?P<time>[\d-]+)/$', views.search_detail, name='search_detail'),