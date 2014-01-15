#!/usr/bin/env python

import itertools
import alfred

from argparse import ArgumentParser
from github_api import Request
from util import *
from fuzzy_matching import fuzzy_match

parser = ArgumentParser()
parser.add_argument('-l', '--lazy', help='get repos only from cache', action='store_true')
parser.add_argument('--debug', help='show debug messages', action='store_true')
parser.add_argument('query', help='get repos only from cache', nargs='?')
args = parser.parse_args()

github_api = Request(lazy=args.lazy, debug=args.debug)

def get_orgs():
  return github_api.request('/user/orgs')

def get_org_repos(org):
  return github_api.request('/orgs/' + org + '/repos?per_page=100')

def get_own_repos():
  return github_api.request('/user/repos?per_page=100')

def get_all_repos():
  orgs = get_orgs()
  org_names = pluck(orgs, 'login')
  org_repos = flatten(get_org_repos(org) for org in org_names)
  own_repos = get_own_repos()
  return itertools.chain(org_repos, own_repos)

#import pprint
#pprint.PrettyPrinter(indent=2).pprint(get_org_repos('ProductMadness')[0])

all_repos = get_all_repos()

feedback = alfred.Feedback()
for repo in all_repos:
  title = repo.get('owner').get('login') + '/' + repo.get('name')
  if not args.query or fuzzy_match(args.query, title):
    feedback.append_item(uid=str(repo.get('id')),
                      arg=repo.get('html_url'),
                      valid='yes',
                      title=title)

print(feedback.xml())

