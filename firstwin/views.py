import subprocess

from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

from django import forms
from codemirror import CodeMirrorTextarea


class ContactForm(forms.Form):
    # codemirror_widget = CodeMirrorTextarea(
    #         mode="text/x-csrc",
    #         theme="cobalt",
    #         config={
    #             'fixedGutter': True
    #             },
    #         )
    content = forms.CharField(required=False, widget=CodeMirrorTextarea)


def firstwin(request):
    if request.method == "POST":
        form_class = ContactForm(request.POST)

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
            outp = open("%s.%s" % (tmp_source_file_name, tmp_outp_extension), "r")
            love = outp.read()
            return HttpResponse(love)

    else:
        form_class = ContactForm
        return render(request, 'firstwin.html', {
            'form': form_class,
            })
