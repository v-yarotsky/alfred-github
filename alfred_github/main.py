# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import itertools
from alfred_github import alfred, fuzzy_matching, github_api
from alfred_github.util import *
from alfred_github.keychain import Keychain

def main():
    parser = ArgumentParser()
    parser.add_argument('-l', '--lazy', help='get repos only from cache', action='store_true')
    parser.add_argument('--debug', help='show debug messages', action='store_true')
    parser.add_argument('query', help='get repos only from cache', nargs='?')
    args = parser.parse_args()

    keychain = Keychain('Alfred Github')
    token = keychain.get_password('Alfred Github')

    if not token:
        from alfred_github import gui
        print("Authorizing")
        github_username = gui.input_box("Github username")
        github_password = gui.input_box("Github password")

        token = github_api.authorize(username=github_username,
                                    password=github_password,
                                    client_id=alfred.preferences['github_api']['client_id'],
                                    client_secret=alfred.preferences['github_api']['client_secret'],
                                    scopes=['repo'],
                                    note='Alfred Github extension')
        keychain.store_password('Alfred Github', token)


    gh = github_api.AuthenticatedGithub(token, lazy=args.lazy, debug=args.debug)

    def get_all_repos():
        orgs = gh.get_orgs()
        org_names = pluck(orgs, 'login')
        org_repos = flatten(gh.get_org_repos(org) for org in org_names)
        own_repos = gh.get_own_repos()
        return itertools.chain(org_repos, own_repos)

    all_repos = get_all_repos()

    feedback = alfred.Feedback()
    for repo in all_repos:
        title = repo.get('owner').get('login') + '/' + repo.get('name')
        if not args.query or fuzzy_matching.fuzzy_match(args.query, title):
            feedback.append_item(uid=str(repo.get('id')),
                                arg=repo.get('html_url'),
                                valid='yes',
                                title=title)

    print(feedback.xml())

