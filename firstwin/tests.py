import os
import shutil

from django.contrib.auth.models import User
from django.test import TestCase

# Create your tests here.
from firstwin.models import DefectSearch, Defect
from firstwin.utils import get_current_time_tuple, get_defect_search_queryset, get_defect_queryset, \
    get_docker_commands_list, create_working_dir


class DefectSearchGetAbsUrlTest(TestCase):
    def setUp(self):
        defect_search = DefectSearch.objects.create(
            user=User.objects.create(),
            time='1999-12-11 13:43:07',
            repository='love',
            defects_amount=4,
        )
        Defect.objects.create(
            defect_search=defect_search,
            file_name='testfile.c',
            type_of_defect='BUF-01',
            column=3,
            line=211,
        )

    def test_get_absolute_url(self):
        defect_search = DefectSearch.objects.get(time='1999-12-11 13:43:07', repository='love')
        defected_file = Defect.objects.get(defect_search=defect_search)
        self.assertEqual(defect_search.get_absolute_url(), '/history/love/1999-12-11-13-43-07')
        self.assertEqual(defected_file.get_absolute_url(), '/history/love/1999-12-11-13-43-07/testfile.c')


class GetMethodsTest(TestCase):
    def setUp(self):
        user = User.objects.create(username='cat', email='love@ya.ru', password='Nonono')
        defect_search = DefectSearch.objects.create(
            user=user,
            time='1233-12-11 11:23:07',
            repository='me',
            defects_amount=4,
        )
        DefectSearch.objects.create(
            user=user,
            time='1000-10-10 10:20:00',
            repository='me',
            defects_amount=56,
        )
        Defect.objects.create(
            defect_search=defect_search,
            file_name='runforest',
            type_of_defect='BUF-01',
            column=3,
            line=211,
        )
        Defect.objects.create(
            defect_search=defect_search,
            file_name='runforest',
            type_of_defect='LEO-03',
            column=3,
            line=100,
        )

    def test_get_defect_search_queryset(self):
        defect_search = DefectSearch.objects.get(time='1233-12-11 11:23:07', repository='me')
        younger_defect_search = DefectSearch.objects.get(time='1000-10-10 10:20:00', repository='me')
        self.assertEqual(get_defect_search_queryset(repository='me').first(), defect_search)
        self.assertEqual(get_defect_search_queryset('time', repository='me').first(), younger_defect_search)

    def test_get_defect_queryset(self):
        defect_1 = Defect.objects.get(file_name='runforest', column=3, line=100)
        defect_2 = Defect.objects.get(file_name='runforest', column=3, line=211)
        self.assertEqual(get_defect_queryset(file_name='runforest', column=3, line=100).first(), defect_1)
        self.assertEqual(get_defect_queryset('-line', file_name='runforest').first(), defect_2)

    def test_get_docker_commands_list(self):
        right_list = ["docker", "run", "-w", "/home/borealis/borealis/checkingTmp",
                      "-v", "%s:/home/borealis/borealis/checkingTmp" % '/tmp/love',
                      "vorpal/borealis-standalone",
                      "sudo", "make", "CC=/home/borealis/borealis/wrapper",
                      ]
        self.assertEqual(get_docker_commands_list('/tmp/love'), right_list)


class CreateDirTest(TestCase):
    def test_create_working_dir(self):
        test_time = tuple(['0000', '00', '00', '00', '00', '00'])
        test_user_name = 'love'
        test_dir = create_working_dir(test_user_name, test_time)

        self.assertTrue(os.path.isdir(test_dir))

        shutil.rmtree(test_dir)
