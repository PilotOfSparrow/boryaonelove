from requests import request
from social_core.pipeline.partial import partial

import json


@partial
def request_list_of_repos(details, *args, **kwargs):
    print(details.get('username'))

    tmp = request('GET', 'https://api.github.com/users/%s/repos' % details.get('username'))

    tmp1 = json.loads(tmp.text)
    # print(*tmp1, sep='\n')
