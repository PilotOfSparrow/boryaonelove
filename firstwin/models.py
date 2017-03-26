from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class DefectSearch(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
    )
    time = models.DateTimeField()
    repository = models.CharField(max_length=150)


class Defect(models.Model):
    defect_search = models.ForeignKey(
        DefectSearch,
        on_delete=models.DO_NOTHING,
    )
    file_name = models.CharField(max_length=150)
    type_of_defect = models.CharField(max_length=150)
    column = models.IntegerField()
    line = models.IntegerField()
