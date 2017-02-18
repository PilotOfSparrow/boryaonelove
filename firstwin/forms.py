from django import forms
from codemirror import CodeMirrorTextarea

class CodeInsertForm(forms.Form):
    # codemirror_widget = CodeMirrorTextarea(
    #         mode="text/x-csrc",
    #         theme="cobalt",
    #         config={
    #             'fixedGutter': True
    #             },
    #         )
    content = forms.CharField(required=False, widget=CodeMirrorTextarea)