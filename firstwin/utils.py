import datetime
import json
from os import makedirs

from django.contrib.auth.models import User
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

# return list of current time in next order: Year (4 digits), Month (2d), Day (2d), Hour (2d), Minute (2d), Second (2d)

def get_current_time_tuple():
    cur_year = str(datetime.datetime.now().strftime('%Y'))
    cur_month = str(datetime.datetime.now().strftime('%m'))
    cur_day = str(datetime.datetime.now().strftime('%d'))
    cur_hour = str(datetime.datetime.now().strftime('%H'))
    cur_min = str(datetime.datetime.now().strftime('%M'))
    cur_sec = str(datetime.datetime.now().strftime('%S'))

    return tuple([cur_year, cur_month, cur_day, cur_hour, cur_min, cur_sec])


# return QuerySet of DefectSearch table, unnamed arguments considered as arguments for order_by
def get_defect_search_queryset(*args, **kwargs):
    # if kwargs['time']:
    #     kwargs['time'] = '%s-%s-%s %s:%s:%s' % kwargs['time'].split('-')
    if args:
        return DefectSearch.objects.filter(**kwargs).order_by(*args)
    else:
        return DefectSearch.objects.filter(**kwargs)


# return QuerySet of Defect table, unnamed arguments considered as arguments for order_by
def get_defect_queryset(*args, **kwargs):
    if args:
        return Defect.objects.filter(**kwargs).order_by(*args)
    else:
        return Defect.objects.filter(**kwargs)


# return tuple of all (public) user repositories from bitbucket
def get_bitbucket_repos_tuple(user_name):
    bb_repos_list_json = get('https://api.bitbucket.org/2.0/repositories/%s' % user_name)

    return tuple((str(n['name']), str(n['name'])) for n in json.loads(bb_repos_list_json.text)['values'])


# return tuple of all (public) user repositories from github
def get_github_repos_tuple(user_name):
    github_repos_list_json = get('https://api.github.com/users/%s/repos' % user_name)

    return tuple((str(n['name']), str(n['name'])) for n in json.loads(github_repos_list_json.text))


# return name of system version manager from bitbucket for given user and repository
def get_bitbucket_repo_scm_str(user_name, repository):
    bb_repo_list_json = get('https://api.bitbucket.org/2.0/repositories/%s/%s' % (user_name, repository))

    return str(json.loads(bb_repo_list_json.text)['scm'])


# return list of commands for cloning git repository
def get_cloning_commands_list(user_name, auth_provider, repository, working_dir):
    if auth_provider == 'github':
        return ['git', 'clone', 'https://github.com/%s/%s' % (user_name, repository), '%s' % working_dir]

    if auth_provider == 'bitbucket':
        repo_scm = get_bitbucket_repo_scm_str(user_name, repository)

        if repo_scm == 'git':
            return ['git', 'clone', 'https://bitbucket.com/%s/%s' % (user_name, repository), '%s' % working_dir]

        if repo_scm == 'hg':
            return ['hg', 'clone', 'https://bitbucket.com/%s/%s' % (user_name, repository), '%s' % working_dir]


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
                "sudo", "/home/borealis/borealis/wrapper", "%s" % source_file_name,
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


# creates working dir in format '/tmp/borya/[user_name]/[current-time(YYYY-MM-DD-hh-mm-ss)]', return absolute path
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


# send email to user with amount of founded defects
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
#                                                Defects Processing                                                    #
########################################################################################################################


# process defects from anonymous user input (index page)
def default_defects_processing(working_dir, creation_time_tuple):
    try:
        with open('%s/persistentDefectData.json' % working_dir) as mistakes_dump:
            mistakes_data = json.load(mistakes_dump)

        mistakes_list = dict()
        for mistake in mistakes_data:
            if bool(mistake):
                mistakes_list = mistake

        current_search = DefectSearch.objects.create(
            user=User.objects.get_or_create(username='ridingTheDragon')[0],
            time='%s-%s-%s %s:%s:%s' % creation_time_tuple,
            repository=str('ridingTheDragon'),
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
        print('No defects found')
        return False

    return True


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

        defected_lines_list = [(item.line, item.type_of_defect) for item in defects_query]

        # !Important! lines in lines_with_defects should be sorted in increasing order
        lines_iterator = 0
        for idx, item in enumerate(styled_code_list, 1):
            if idx == defected_lines_list[lines_iterator][0]:
                tmp_item_str = '<span style="background-color: #fd2a2a; padding: 0 5px 0 5px">%s</span> ERROR: ' % item

                tmp_lines_iterator = lines_iterator

                while idx == defected_lines_list[tmp_lines_iterator][0]:
                    tmp_item_str += defected_lines_list[tmp_lines_iterator][1] + ' '

                    tmp_lines_iterator += 1

                    if tmp_lines_iterator >= len(defected_lines_list):
                        break

                styled_code_list[idx - 1] = tmp_item_str

                lines_iterator = tmp_lines_iterator
                if lines_iterator >= len(defected_lines_list):
                    break

        return styled_code_list

    except FileNotFoundError:
        return None

########################################################################################################################
#                                                End Mark Defects                                                      #
########################################################################################################################
