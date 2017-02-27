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


class ChooseMeSenpai(forms.Form):
    # rl = {}

    def __init__(self, *args, **kwargs):
        rep_choices = kwargs.pop('rep_choices')
        super(ChooseMeSenpai, self).__init__(*args, **kwargs)
        self.fields['ch'].choices = rep_choices

    ch = forms.ChoiceField()
