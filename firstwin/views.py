import datetime
import json
import os
import subprocess

from django.core.mail import send_mail
from requests import get
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.core.cache import cache
# Create your views here.
from boryaonelove import settings
from firstwin.models import DefectSearch, Defect
from firstwin.utility import formatted_current_time
from .forms import CodeInsertForm, ChooseMeSenpai


# docker run -i -t -w /home/borealis/borealis/ -v /var/os:/home/borealis/borealis/shamanKing vorpal/borealis-standalone
# ./wrapper -c /home/borealis/borealis/shamanKing/main.c
def index(request):
    if request.method == "POST":
        form_class = CodeInsertForm(request.POST)

        if form_class.is_valid():
            var = form_class.cleaned_data["content"]

            tmp_source_file_name = "tmpS"
            tmp_source_file_extension = "c"
            tmp_outp_extension = "s"

            str_current_run_dir = '/tmp/borya/ridingTheDragon/%s' % formatted_current_time()

            os.makedirs(str_current_run_dir)

            tmp_source_code_file = open("%s/%s.%s" %
                                        (str_current_run_dir, tmp_source_file_name, tmp_source_file_extension), "w")
            tmp_source_code_file.write("%s" % var)
            tmp_source_code_file.close()

            subprocess.call(["docker", "run",
                             # меняем рабочую директорию(для мейка)
                             "-w", "/home/borealis/borealis/checkingTmp",
                             # расшариваем директорию с проектом
                             "-v", "%s:/home/borealis/borealis/checkingTmp" % str_current_run_dir,
                             # имя запускаемого образа
                             "vorpal/borealis-standalone",
                             # команда, запускаемая в контейнере
                             "sudo", "/home/borealis/borealis/wrapper", "-c",
                             "%s.%s" % (tmp_source_file_name, tmp_source_file_extension),
                             ])

            try:
                with open('%s/persistentDefectData.json' % str_current_run_dir) as mistakes_dump:
                    mistakes_data = json.load(mistakes_dump)
            except FileNotFoundError:
                print('Borealis can\'t find any mistakes')
                return HttpResponse('Borealis can\'t find any mistakes')

            mistakes_list = dict()
            for mistake in mistakes_data:
                if bool(mistake):
                    mistakes_list = mistake

            return HttpResponse(mistakes_list)

    else:

        form_class = CodeInsertForm
        return render(request, 'index.html', {
            'form': form_class,
        })


@login_required
def home(request):
    user_backend = cache.get('backend')

    logged_user_object = request.user.social_auth.get(user=request.user.id, provider=user_backend)

    # может попробовать посылать access_token c подвывертом?
    # if user_backend == 'bitbucket':
    #     access_token = logged_user_object.access_token
    #     bb_rep_list_json = get('https://api.bitbucket.org/2.0/repositories/pilotofsparrow?oauth_token_secret=%s&oauth_token=%s'
    #                            % (access_token['oauth_token_secret'], access_token['oauth_token']))
    #     print(bb_rep_list_json.text)
    #     return HttpResponse("You logged in as bitbucket user")

    urepos_list_json = get('https://api.github.com/users/%s/repos' % request.user)

    reps_dict = {}
    for reps in json.loads(urepos_list_json.text):
        reps_dict[reps['name']] = reps['html_url']

    urepos_tuple_list = tuple((str(n), str(n)) for n in reps_dict.keys())

    if request.method == 'POST':
        which = ChooseMeSenpai(request.POST, rep_choices=urepos_tuple_list)

        if which.is_valid():
            urepos_choice = which.cleaned_data['ch']
            # print(var)

            urepos_content_json = get('https://api.github.com/repos/%s/%s/contents' % (request.user, urepos_choice))
            for file in json.loads(urepos_content_json.text):
                if file['name'] == 'Makefile' or file['name'] == 'makefile':
                    # генерируем имя для рабочей дериктории
                    cur_year = str(datetime.datetime.now().strftime('%Y'))
                    cur_month = str(datetime.datetime.now().strftime('%m'))
                    cur_day = str(datetime.datetime.now().strftime('%d'))
                    cur_hour = str(datetime.datetime.now().strftime('%H'))
                    cur_min = str(datetime.datetime.now().strftime('%M'))
                    cur_sec = str(datetime.datetime.now().strftime('%S'))
                    cur_time = '%s-%s-%s-%s-%s-%s' % (cur_year, cur_month, cur_day, cur_hour, cur_min, cur_sec)
                    str_current_run_dir = '/tmp/borya/%s/%s' % (request.user, cur_time)

                    os.makedirs(str_current_run_dir)

                    subprocess.call(['git', 'clone', '--depth=1',
                                     'https://github.com/%s/%s' % (request.user, urepos_choice),
                                     '%s' % str_current_run_dir])

                    subprocess.call(["docker", "run",
                                     # меняем рабочую директорию(для мейка)
                                     "-w", "/home/borealis/borealis/checkingTmp",
                                     # расшариваем директорию с проектом
                                     "-v", "%s:/home/borealis/borealis/checkingTmp" % str_current_run_dir,
                                     # имя запускаемого образа
                                     "vorpal/borealis-standalone",
                                     # команда, запускаемая в контейнере
                                     "sudo", "make", "CC=/home/borealis/borealis/wrapper",
                                     ])

                    try:
                        with open('%s/persistentDefectData.json' % str_current_run_dir) as mistakes_dump:
                            mistakes_data = json.load(mistakes_dump)

                    except FileNotFoundError:
                        print('Borealis can\'t find any mistakes')
                        send_mail(
                            '%s checked!' % urepos_choice,
                            'Borya cant find any mistakes',
                            settings.EMAIL_HOST_USER,
                            [request.user.email],
                        )
                        return HttpResponse('Borealis can\'t find any mistakes')

                    mistakes_list = dict()
                    for mistake in mistakes_data:
                        if bool(mistake):
                            mistakes_list = mistake

                    current_search = DefectSearch.objects.create(
                        user=request.user,
                        time='%s-%s-%s %s:%s:%s' % (cur_year, cur_month, cur_day, cur_hour, cur_min, cur_sec),
                        repository=str(urepos_choice),
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

                    send_mail(
                        '%s checked!' % urepos_choice,
                        'Borya founded %s mistakes' % len(mistakes_list),
                        settings.EMAIL_HOST_USER,
                        [request.user.email],
                    )

                    return HttpResponse(mistakes_data)

                    # __future__ http response
                    # return HttpResponse('Thank you for using Borealis! '
                    #                     'It\'s can take a while to check whole project, so'
                    #                     'we will inform you via email when it\'s ready.')

            return HttpResponse('Selected repository doesn\'t contain makefile!')

    choose = ChooseMeSenpai(rep_choices=urepos_tuple_list)

    return render(request, 'home.html', {
        'ch': choose,
    })


@login_required
def history(request):
    user_searches = DefectSearch.objects.filter(user=request.user).order_by('-time')

    return render(request, 'history.html', {
        'user_searches': user_searches,
    })


@login_required
def search_detail(request, repository, time):
    year, month, day, hour, minute, second = time.split('-')
    search = DefectSearch.objects.filter(user=request.user, repository=repository,
                                         time='%s-%s-%s %s:%s:%s' % (year, month, day, hour, minute, second))

    defects_query = Defect.objects.filter(defect_search=search).order_by('file_name', 'line')

    return render(request, 'search_detail.html', {
        'defects_query': defects_query,
    })
