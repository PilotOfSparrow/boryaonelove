from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.http import HttpResponse
from django.shortcuts import render

from firstwin.utility import *
from .forms import CodeInsertForm, ChooseMeSenpai


# docker run -i -t -w /home/borealis/borealis/ -v /var/os:/home/borealis/borealis/shamanKing vorpal/borealis-standalone
# ./wrapper -c /home/borealis/borealis/shamanKing/main.c
def index(request):
    if request.method == "POST":
        form_class = CodeInsertForm(request.POST)

        if form_class.is_valid():
            source_code = form_class.cleaned_data["content"]

            defects_status = wrapper_default_defects_processing(source_code)

            if defects_status[0]:
                return defects_status[1]
            else:
                return HttpResponse('Borealis can\'t find any mistakes!')
    else:
        form_class = CodeInsertForm
        return render(request, 'index.html', {
            'form': form_class,
        })


@login_required
def home(request):
    # tuple of all (public) user repositories
    user_repos_tuple = tuple

    user_object = request.user

    session_dict = dict()
    for sess in Session.objects.iterator():
        session_dict = sess.get_decoded()

    # user_login_backend = str()
    if 'social_auth_last_login_backend' in session_dict.keys():
        user_login_backend = session_dict['social_auth_last_login_backend']
    else:
        return HttpResponse('Can\'t detect your authentication backend')

    # может попробовать посылать access_token c подвывертом?
    # if user_login_backend == 'bitbucket':
    #     access_token = logged_user_object.access_token
    #     bb_rep_list_json = get('https://api.bitbucket.org/2.0/repositories/pilotofsparrow?'
    #                            'oauth_token_secret=%s&oauth_token=%s'
    #                            % (access_token['oauth_token_secret'], access_token['oauth_token']))
    #     print(bb_rep_list_json.text)
    #     return HttpResponse("You logged in as bitbucket user")

    if user_login_backend == 'github':

        user_repos_tuple = get_github_repos_tuple(user_object.username)

        if request.method == 'POST':
            choice = ChooseMeSenpai(request.POST, repos_choices=user_repos_tuple)

            if choice.is_valid():
                user_repos_choice = choice.cleaned_data['choices']

                if wrapper_github_defects_processing(user_object, user_login_backend, user_repos_choice):

                    return HttpResponse('Thank you for using Borealis! '
                                        'It\'s can take a while to check whole project, so '
                                        'we will inform you via email when it\'s ready.')
                else:
                    return HttpResponse('Selected repository doesn\'t contain makefile!')

    choices = ChooseMeSenpai(repos_choices=user_repos_tuple)

    return render(request, 'home.html', {
        'choices': choices,
    })


@login_required
def history(request):
    user_searches = get_defect_search_queryset('-time', user=request.user)

    return render(request, 'history.html', {
        'user_searches': user_searches,
    })


@login_required
def search_detail(request, repository, time):
    search = get_defect_search_queryset(user=request.user, repository=repository,
                                        time='%s-%s-%s %s:%s:%s' % tuple(time.split('-')))

    defects_query = get_defect_queryset('file_name', 'line', defect_search=search)

    return render(request, 'search_detail.html', {
        'defects_query': defects_query,
    })


@login_required
def show_defects(request, repository, time, file_name):
    styled_code_list = mark_file_defects_list(request.user, repository, time, file_name)

    if styled_code_list:
        return HttpResponse('\n'.join(styled_code_list))
    else:
        return HttpResponse('Can\'t find selected file.')
