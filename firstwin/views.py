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
from .forms import CodeInsertForm, ChooseMeSenpai


# docker run -i -t -w /home/borealis/borealis/ -v /var/os:/home/borealis/borealis/shamanKing vorpal/borealis-standalone
# ./wrapper -c /home/borealis/borealis/shamanKing/main.c
def index(request):
    if request.method == "POST":
        form_class = CodeInsertForm(request.POST)

        if form_class.is_valid():
            var = form_class.cleaned_data["content"]
            print(var)
            tmp_source_file_name = "tmpS"
            tmp_source_file_extension = "c"
            tmp_outp_extension = "s"
            tmp_source_code_file = open("%s.%s" % (tmp_source_file_name, tmp_source_file_extension), "w")
            tmp_source_code_file.write("%s" % var)
            tmp_source_code_file.close()
            # subprocess.call(["gcc", "-S", "%s.%s" % (tmp_source_file_name, tmp_source_file_extension)])
            subprocess.call(["docker", "start", "gcc"])
            subprocess.call(["docker", "cp", "./tmpS.c", "gcc:./"])
            subprocess.call(["docker", "exec", "gcc", "gcc", "-S", "%s.%s"
                             % (tmp_source_file_name, tmp_source_file_extension)])
            subprocess.call(["docker", "cp", "gcc:./tmpS.s", "./"])
            subprocess.call(["docker", "exec", "gcc", "rm", "-r", "%s.%s"
                             % (tmp_source_file_name, tmp_source_file_extension)])
            subprocess.call(["docker", "exec", "gcc", "rm", "-r", "%s.%s"
                             % (tmp_source_file_name, tmp_outp_extension)])
            subprocess.call(["docker", "stop", "gcc"])

            outp = open("%s.%s" % (tmp_source_file_name, tmp_outp_extension), "r")
            love = outp.read()
            return HttpResponse(love)

    else:

        # TEST!!!!!
        try:
            with open('/var/os/iputils/persistentDefectData.json') as mistakes_dump:
                mistakes_data = json.load(mistakes_dump)


        except FileNotFoundError:
            print('Borealis can\'t find any mistakes')
            return HttpResponse('Borealis can\'t find any mistakes')

        for mistake in mistakes_data:
            if bool(mistake):
                mistake_list = mistake

        # TEST!!!!



        form_class = CodeInsertForm
        return render(request, 'index.html', {
            'form': form_class,
        })


@login_required
def home(request):
    user_backend = cache.get('backend')

    logged_user_object = request.user.social_auth.get(user=request.user.id, provider=user_backend)

    # user_provider = logged_user_object.provider

    # может попробовать посылать access_token?
    # if user_backend == 'bitbucket':
    #     access_token = logged_user_object.access_token
    #     bb_rep_list_json = get('https://api.bitbucket.org/2.0/repositories/pilotofsparrow?oauth_token_secret=%s&oauth_token=%s'
    #                            % (access_token['oauth_token_secret'], access_token['oauth_token']))
    #     print(bb_rep_list_json.text)
    #     return HttpResponse("You logged in as bitbucket user")

    urepos_list_json = get('https://api.github.com/users/%s/repos' % request.user)

    # print(*tmp, sep='\n')
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

                    current_search = DefectSearch.objects.create(
                        user=request.user,
                        time= '%s-%s-%s %s:%s:%s' % (cur_year, cur_month, cur_day, cur_hour, cur_min, cur_sec),
                        repository=str(urepos_choice),
                    )

                    # subprocess.call(['make', '-C', '/tmp/%s/%s' % (request.user, urepos_choice)])

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

                    index_of_mistake = 0
                    for mistake in mistakes_data:
                        if bool(mistake):
                            mistakes_list = mistake
                            Defect.objects.create(
                                defect_search=current_search,
                                file_name=mistake[index_of_mistake]['location']['filename'],
                                type_of_defect=mistake[index_of_mistake]['type'],
                                column=mistake[index_of_mistake]['location']['loc']['col'],
                                line=mistake[index_of_mistake]['location']['loc']['line'],
                            )
                            ++index_of_mistake


                    # some = Defect.objects.filter(defect_search=current_search)



                    send_mail(
                        '%s checked!' % urepos_choice,
                        'Borya founded %s mistakes' % len(mistake),
                        settings.EMAIL_HOST_USER,
                        [request.user.email],
                    )

                    return HttpResponse(mistakes_data)

                    # __future__ http response
                    # return HttpResponse('Thank you for using Borealis! '
                    #                     'It\'s can take a while to check whole project, so'
                    #                     'we will inform you via email when it\'s ready.')

            return HttpResponse('Selected repository doesn\'t contain makefile!')

    # print(request.user)

    choose = ChooseMeSenpai(rep_choices=urepos_tuple_list)
    somebody = DefectSearch.objects.filter(user=request.user).latest('time')
    defects_query = Defect.objects.filter(defect_search=somebody)

    for p in defects_query:
        print(p.file_name)

    return render(request, 'home.html', {
        'ch': choose,
        'defects_query': defects_query,
    })
