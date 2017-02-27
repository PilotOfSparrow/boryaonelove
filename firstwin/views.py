import json
import subprocess
from requests import get
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
# Create your views here.

from .forms import CodeInsertForm, ChooseMeSenpai


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
        form_class = CodeInsertForm
        return render(request, 'index.html', {
            'form': form_class,
        })


@login_required
def home(request):
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
                if (file['name'] == 'Makefile' or
                            file['name'] == 'makefile'):
                    subprocess.call(['git', 'clone', '--depth=1',
                                     'https://github.com/%s/%s' % (request.user, urepos_choice),
                                     '/tmp/%s/%s' % (request.user, urepos_choice)])

                    subprocess.call(['make', '-C', '/tmp/%s/%s' % (request.user, urepos_choice)])
                    return HttpResponse('love')


            return HttpResponse('Selected repository doesn\'t contain makefile!')




    # print(request.user)

    choose = ChooseMeSenpai(rep_choices=urepos_tuple_list)
    return render(request, 'home.html', {
        'ch': choose
    })
