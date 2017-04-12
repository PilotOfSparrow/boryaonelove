import datetime
import json
import subprocess
from os import makedirs

from django.core.mail import send_mail
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.c_cpp import CLexer
from requests import get

from boryaonelove import settings
from firstwin.models import DefectSearch, Defect


########################################################################################################################
#                                                   Get Methods                                                        #
########################################################################################################################

# returning list of current time in next order:
#                                             Year (4 digits), Month (2d), Day (2d), Hour (2d), Minute (2d), Second (2d)
def get_current_time_tuple():
    cur_year = str(datetime.datetime.now().strftime('%Y'))
    cur_month = str(datetime.datetime.now().strftime('%m'))
    cur_day = str(datetime.datetime.now().strftime('%d'))
    cur_hour = str(datetime.datetime.now().strftime('%H'))
    cur_min = str(datetime.datetime.now().strftime('%M'))
    cur_sec = str(datetime.datetime.now().strftime('%S'))

    return tuple([cur_year, cur_month, cur_day, cur_hour, cur_min, cur_sec])


# returning QuerySet of DefectSearch table, unnamed arguments considered as reason for order_by
def get_defect_search_queryset(*args, **kwargs):
    # if kwargs['time']:
    #     kwargs['time'] = '%s-%s-%s %s:%s:%s' % kwargs['time'].split('-')
    if args:
        return DefectSearch.objects.filter(**kwargs).order_by(*args)
    else:
        return DefectSearch.objects.filter(**kwargs)


# returning QuerySet of Defect table, unnamed arguments considered as reason for order_by
def get_defect_queryset(*args, **kwargs):
    if args:
        return Defect.objects.filter(**kwargs).order_by(*args)
    else:
        return Defect.objects.filter(**kwargs)


# return tuple of all (public) user repositories from bitbucket
def get_bitbucket_repos_tuple(user_name):
    bb_rep_list_json = get('https://api.bitbucket.org/2.0/repositories/%s' % user_name)

    return tuple((str(n['name']), str(n['name'])) for n in json.loads(bb_rep_list_json.text)['values'])


# return tuple of all (public) user repositories from github
def get_github_repos_tuple(user_name):
    user_repos_list_json = get('https://api.github.com/users/%s/repos' % user_name)

    reps_dict = {}
    for reps in json.loads(user_repos_list_json.text):
        reps_dict[reps['name']] = reps['html_url']

    return tuple((str(n), str(n)) for n in reps_dict.keys())


# return list of commands for cloning git repository
def get_cloning_commands_git_list(user_name, provider, repository, working_dir):
    return ['git', 'clone', '--depth=1', 'https://%s.com/%s/%s' % (provider, user_name, repository), '%s' % working_dir]


# return list of command for running borealis docker image
def get_docker_commands_list(working_dir, source_file_name=None):
    if source_file_name:
        return ["docker", "run",
                # меняем рабочую директорию(для мейка)
                "-w", "/home/borealis/borealis/checkingTmp",
                # расшариваем директорию с проектом
                "-v", "%s:/home/borealis/borealis/checkingTmp" % working_dir,
                # имя запускаемого образа
                "vorpal/borealis-standalone",
                # команда, запускаемая в контейнере
                "sudo", "/home/borealis/borealis/wrapper", "-c", "%s" % source_file_name,
                ]
    else:
        return ["docker", "run",
                # меняем рабочую директорию(для мейка)
                "-w", "/home/borealis/borealis/checkingTmp",
                # расшариваем директорию с проектом
                "-v", "%s:/home/borealis/borealis/checkingTmp" % working_dir,
                # имя запускаемого образа
                "vorpal/borealis-standalone",
                # команда, запускаемая в контейнере
                "sudo", "make", "CC=/home/borealis/borealis/wrapper",
                ]


########################################################################################################################
#                                                End Get Methods                                                       #
########################################################################################################################

########################################################################################################################
#                                              Check for makefile                                                      #
########################################################################################################################


# return True if chosen bitbucket repository contains makefile
def check_bitbucket_for_makefile(user_name, repository):
    user_repos_content_json = get('https://api.bitbucket.org/1.0/repositories/%s/%s/src/master/' % (user_name,
                                                                                                    repository))

    for file in json.loads(user_repos_content_json.text)['files']:
        if file['path'] == 'Makefile' or file['path'] == 'makefile':
            return True

    return False


# return True if chosen github repository contains makefile
def check_github_for_makefile(user_name, repository):
    user_repos_content_json = get('https://api.github.com/repos/%s/%s/contents' % (user_name, repository))

    for file in json.loads(user_repos_content_json.text):
        if file['name'] == 'Makefile' or file['name'] == 'makefile':
            return True

    return False

########################################################################################################################
#                                               End Check for makefile                                                 #
########################################################################################################################

########################################################################################################################
#                                                    Create Dir                                                        #
########################################################################################################################


# creates working dir in format '/tmp/borya/[user_name]/[current-time(YYYY-MM-DD-hh-mm-ss)]', returning absolute path
#                                                                                                         to created dir
def create_working_dir(user_name, current_time_tuple):
    current_time_str = '%s-%s-%s-%s-%s-%s' % current_time_tuple
    str_current_run_dir = '/tmp/borya/%s/%s' % (user_name, current_time_str)

    makedirs(str_current_run_dir)

    return str_current_run_dir

########################################################################################################################
#                                                  End Create Dir                                                      #
########################################################################################################################

########################################################################################################################
#                                                Send Notification                                                     #
########################################################################################################################


# sending email to user with amount of founded defects
def send_notification(email, repository, defects_amount=None):
    if defects_amount:
        send_mail(
            '%s checked!' % repository,
            'Borya founded %s mistakes' % defects_amount,
            settings.EMAIL_HOST_USER,
            [email],
        )
    else:
        send_mail(
            '%s checked!' % repository,
            'Borya cant find any mistakes',
            settings.EMAIL_HOST_USER,
            [email],
        )

########################################################################################################################
#                                               End Send Notification                                                  #
########################################################################################################################

########################################################################################################################
#                                                    Wrappers                                                          #
########################################################################################################################


def wrapper_default_defects_processing(source_code):
    default_anonymous_user_name_str = 'ridingTheDragon'

    default_source_file_name_str = "tmpS.c"
    # default_source_file_extension_str = "c"

    working_dir = create_working_dir(default_anonymous_user_name_str, get_current_time_tuple())

    try:
        with open("%s/%s" % (working_dir, default_source_file_name_str), "w") as default_source_code_file:
            default_source_code_file.write("%s" % source_code)

        subprocess.call(get_docker_commands_list(working_dir, default_source_file_name_str))

        return default_defects_processing(working_dir)

    except FileNotFoundError:
        print('Can\'t create source file')


def wrapper_defects_processing(user_object, user_auth_backend, repository):
    if (user_auth_backend == 'bitbucket' and check_bitbucket_for_makefile(user_object.username, repository)) \
            or (user_auth_backend == 'github' and check_github_for_makefile(user_object.username, repository)):

        current_time_tuple = get_current_time_tuple()
        current_working_dir_str = create_working_dir(user_object.username, current_time_tuple)

        subprocess.call(get_cloning_commands_git_list(user_object.username,
                                                      user_auth_backend,
                                                      repository,
                                                      current_working_dir_str))

        subprocess.call(get_docker_commands_list(current_working_dir_str))

        defects_amount_int = defects_processing(user_object,
                                                repository,
                                                current_working_dir_str,
                                                current_time_tuple)

        send_notification(user_object.email, repository, defects_amount_int)

        return True
    else:
        return False

########################################################################################################################
#                                                    End Wrappers                                                      #
########################################################################################################################

########################################################################################################################
#                                                Defects Processing                                                    #
########################################################################################################################


# process defects from anonymous user input (index page)
def default_defects_processing(working_dir):
    try:
        with open('%s/persistentDefectData.json' % working_dir) as mistakes_dump:
            mistakes_data = json.load(mistakes_dump)

        mistakes_list = dict()
        for mistake in mistakes_data:
            if bool(mistake):
                mistakes_list = mistake

    except FileNotFoundError:
        print('No defects found')
        return [False]

    return [True, mistakes_list]


# first function opening defects file,
# second create DefectSearch object instance for current checking,
# third it's create Defect object instance for every defect from file
# returning amount of defects
def defects_processing(user_object, repository, working_dir, creation_time_tuple):
    try:
        with open('%s/persistentDefectData.json' % working_dir) as mistakes_dump:
            mistakes_data = json.load(mistakes_dump)

        mistakes_list = dict()
        for mistake in mistakes_data:
            if bool(mistake):
                mistakes_list = mistake

        current_search = DefectSearch.objects.create(
            user=user_object,
            time='%s-%s-%s %s:%s:%s' % creation_time_tuple,
            repository=str(repository),
            defects_amount=len(mistakes_list),
        )

        for mis in mistakes_list:
            Defect.objects.create(
                defect_search=current_search,
                file_name=mis['location']['filename'],
                type_of_defect=mis['type'],
                column=mis['location']['loc']['col'],
                line=mis['location']['loc']['line'],
            )

    except FileNotFoundError:
        # send_notification(user_object.email, user_repos_choice)
        print('Defects file not found')
        return 0

    return len(mistakes_list)

########################################################################################################################
#                                              End Defects Processing                                                  #
########################################################################################################################

########################################################################################################################
#                                                  Mark Defects                                                        #
########################################################################################################################


def mark_defects_in_file(user_object, repository, time, file_name):
    try:
        with open('/tmp/borya/%s/%s/%s' % (user_object.username, time, file_name)) as defected_file:
            code = defected_file.readlines()

        styled_code_str = highlight(" ".join(code), CLexer(), HtmlFormatter(noclasses=True, linenos='inline'))

        styled_code_list = styled_code_str.split('\n')

        search = get_defect_search_queryset(user=user_object, repository=repository,
                                            time='%s-%s-%s %s:%s:%s' % tuple(time.split('-')))

        defects_query = get_defect_queryset('line', defect_search=search, file_name=file_name)

        lines_with_defect = [item.line for item in defects_query]

        for idx, item in enumerate(styled_code_list, 1):
            if idx in lines_with_defect:
                tmp_item_str = '<span style="background-color: #fd2a2a; padding: 0 5px 0 5px">%s</span>' % item
                styled_code_list[idx - 1] = tmp_item_str

        return styled_code_list

    except FileNotFoundError:
        return None

########################################################################################################################
#                                                End Mark Defects                                                      #
########################################################################################################################
