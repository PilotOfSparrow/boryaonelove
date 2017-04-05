from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse


class DefectSearch(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
    )
    time = models.DateTimeField()
    repository = models.CharField(max_length=150)
    defects_amount = models.IntegerField(default=0)

    def get_absolute_url(self):
        return reverse('firstwin:search_detail', kwargs={'repository': self.repository,
                                                         'time': str(self.time.strftime('%Y-%m-%d-%H-%M-%S')),
                                                         })


class Defect(models.Model):
    defect_search = models.ForeignKey(
        DefectSearch,
        on_delete=models.DO_NOTHING,
    )
    file_name = models.CharField(max_length=150)
    type_of_defect = models.CharField(max_length=150)
    column = models.IntegerField()
    line = models.IntegerField()

    def get_absolute_url(self):
        search = DefectSearch.objects.get(id=self.defect_search.id)
        return reverse('firstwin:show_defects', kwargs={'repository': search.repository,
                                                        'time': str(search.time.strftime('%Y-%m-%d-%H-%M-%S')),
                                                        'file_name': self.file_name,
                                                        })

    def get_specific_line_url(self):
        search = DefectSearch.objects.get(id=self.defect_search.id)
        return reverse('firstwin:show_specific_defect', kwargs={'repository': search.repository,
                                                                'time': str(search.time.strftime('%Y-%m-%d-%H-%M-%S')),
                                                                'file_name': self.file_name,
                                                                'line': self.line,
                                                                })
