from requests import get
from requests import request
from social_core.pipeline.partial import partial
from django.core.cache import cache

import json


@partial
def request_list_of_repos(backend,details, *args, **kwargs):
    cur_backend = backend.name
    cache.set('backend', backend.name)
    print(backend.name)


    # bb_rep_list_json = get('https://api.bitbucket.org/2.0/repositories/PilotOfSparrow')
    # print(bb_rep_list_json.text)
    # tmp = request('GET', 'https://api.github.com/users/%s/repos' % details.get('username'))

    # tmp1 = json.loads(tmp.text)
    # print(*tmp1, sep='\n')
