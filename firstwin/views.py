import subprocess

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
# Create your views here.

from .forms import CodeInsertForm


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
    return render(request, 'home.html')