# Create your tasks here
from __future__ import absolute_import, unicode_literals

import json

import subprocess
from django.contrib.auth.models import User

from celery import shared_task
from django.contrib.auth.models import User

from firstwin.models import DefectSearch, Defect

# first, function opening defects file,
# second, create DefectSearch object instance for current checking,
# third, it's create Defect object instance for every defect from file
# returning amount of defects
from firstwin.utils import get_current_time_tuple, create_working_dir, get_cloning_commands_list, \
    get_docker_commands_list, send_notification, check_bitbucket_for_makefile, check_github_for_makefile, \
    defects_processing, default_defects_processing, mark_defects_in_file


# @shared_task
# def defects_processing(user_id, repository, working_dir, creation_time_tuple):
#     try:
#         with open('%s/persistentDefectData.json' % working_dir) as mistakes_dump:
#             mistakes_data = json.load(mistakes_dump)
#
#         mistakes_list = dict()
#         for mistake in mistakes_data:
#             if bool(mistake):
#                 mistakes_list = mistake
#
#         current_search = DefectSearch.objects.create(
#             user=User.objects.get(pk=user_id),
#             time='%s-%s-%s %s:%s:%s' % tuple(creation_time_tuple),
#             repository=str(repository),
#             defects_amount=len(mistakes_list),
#         )
#
#         for mis in mistakes_list:
#             Defect.objects.create(
#                 defect_search=current_search,
#                 file_name=mis['location']['filename'],
#                 type_of_defect=mis['type'],
#                 column=mis['location']['loc']['col'],
#                 line=mis['location']['loc']['line'],
#             )
#
#     except FileNotFoundError:
#         print('Defects file not found')
#         return 0
#
#     return len(mistakes_list)

@shared_task
def wrapper_default_defects_processing(source_code):
    default_anonymous_user_name_str = 'ridingTheDragon'

    default_source_file_name_str = "tmpS.c"
    # default_source_file_extension_str = "c"

    current_time_tuple = get_current_time_tuple()

    working_dir = create_working_dir(default_anonymous_user_name_str, current_time_tuple)

    try:
        with open("%s/%s" % (working_dir, default_source_file_name_str), "w") as default_source_code_file:
            default_source_code_file.write("%s" % source_code)

        subprocess.call(get_docker_commands_list(working_dir, default_source_file_name_str))

        default_defects_processing(working_dir, current_time_tuple)

        return mark_defects_in_file(User.objects.get(username='ridingTheDragon'),
                                    'ridingTheDragon',
                                    '%s-%s-%s-%s-%s-%s' % current_time_tuple,
                                    'tmpS.c')

    except FileNotFoundError:
        print('Can\'t create source file')
        return False

@shared_task
def wrapper_defects_processing(user_id, user_auth_backend, repository):
    user_object = User.objects.get(pk=user_id)

    if (user_auth_backend == 'bitbucket' and check_bitbucket_for_makefile(user_object.username, repository)) \
            or (user_auth_backend == 'github' and check_github_for_makefile(user_object.username, repository)):

        current_time_tuple = get_current_time_tuple()

        current_working_dir_str = create_working_dir(user_object.username, current_time_tuple)

        subprocess.call(get_cloning_commands_list(user_object.username,
                                                  user_auth_backend,
                                                  repository,
                                                  current_working_dir_str))

        subprocess.call(get_docker_commands_list(current_working_dir_str))

        # print(User.objects.get(id=user_object.pk))

        defects_amount_int = defects_processing(user_object,
                                                repository,
                                                current_working_dir_str,
                                                current_time_tuple)

        # defects_amount_int = defects_processing(user_object, repository, current_working_dir_str, current_time_tuple)

        send_notification(user_object.email, repository, defects_amount_int)

        return True
    else:
        return False
