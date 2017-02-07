from django.conf.urls import url

from . import views

app_name = 'firstwin'

urlpatterns = [
        url(r'^$', views.firstwin, name='index'),
        ]
