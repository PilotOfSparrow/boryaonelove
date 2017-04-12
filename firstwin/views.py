from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from firstwin.utils import *
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

    if request.session['social_auth_last_login_backend']:
        user_auth_backend = request.session['social_auth_last_login_backend']
    else:
        return HttpResponse('Can\'t detect your authentication backend')

    if user_auth_backend == 'bitbucket':
        user_repos_tuple = get_bitbucket_repos_tuple(user_object.username)

    if user_auth_backend == 'github':
        user_repos_tuple = get_github_repos_tuple(user_object.username)

    # logged_user_object = user_object.social_auth.get(user=request.user.id, provider=user_auth_backend)

    if request.method == 'POST':
        choice = ChooseMeSenpai(request.POST, repos_choices=user_repos_tuple)

        if choice.is_valid():
            user_repos_choice = choice.cleaned_data['choices']

            if wrapper_defects_processing(user_object, user_auth_backend, user_repos_choice):
                return HttpResponse('Thank you for using Borealis! '
                                    'It\'s can take a while to check whole project, so '
                                    'we will inform you via email when it\'s ready.')
            else:
                return HttpResponse('Selected repository doesn\'t contain makefile!')
    else:
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
    styled_code_list = mark_defects_in_file(request.user, repository, time, file_name)

    if styled_code_list:
        return HttpResponse('\n'.join(styled_code_list))
    else:
        return HttpResponse('Can\'t find selected file.')
