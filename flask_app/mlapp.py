from collections import namedtuple, Counter
from github3 import GitHub
from pathlib import Path
from cryptography.hazmat.backends import default_backend
import time
import json
import jwt
import requests
from tqdm import tqdm
from typing import List

class GitHubApp(GitHub):
    """
    This is a small wrapper around the github3.py library
    
    Provides some convenience functions for testing purposes.
    """
    
    def __init__(self, pem_path, app_id):
        super().__init__()
        
        self.path = Path(pem_path)
        self.app_id = app_id
        
        if not self.path.is_file():
            raise ValueError(f'argument: `pem_path` must be a valid filename. {pem_path} was not found.')        
    
    def get_app(self):
        with open(self.path, 'rb') as key_file:
            client = GitHub()
            client.login_as_app(private_key_pem=key_file.read(),
                        app_id=self.app_id)
        return client
    
    def get_installation(self, installation_id):
        "login as app installation without requesting previously gathered data."
        with open(self.path, 'rb') as key_file:
            client = GitHub()
            client.login_as_app_installation(private_key_pem=key_file.read(),
                                             app_id=self.app_id,
                                             installation_id=installation_id)
        return client
        
    def get_test_installation_id(self):
        "Get a sample test_installation id."
        client = self.get_app()
        return next(client.app_installations()).id
        
    def get_test_installation(self):
        "login as app installation with the first installation_id retrieved."
        return self.get_installation(self.get_test_installation_id())
    
    def get_test_repo(self):
        repo = self.get_all_repos(self.get_test_installation_id())[0]
        appInstallation = self.get_test_installation()
        owner, name = repo['full_name'].split('/')
        return appInstallation.repository(owner, name)
        
    def get_test_issue(self):
        test_repo = self.get_test_repo()
        return next(test_repo.issues())
        
    def get_jwt(self):
        """
        This is needed to retrieve the installation access token (for debugging). 
        
        Useful for debugging purposes.  Must call .decode() on returned object to get string.
        """
        now = self._now_int()
        payload = {
            "iat": now,
            "exp": now + (60),
            "iss": self.app_id
        }
        with open(self.path, 'rb') as key_file:
            private_key = default_backend().load_pem_private_key(key_file.read(), None)
            return jwt.encode(payload, private_key, algorithm='RS256')
    
    def get_installation_id(self, owner, repo):
        "https://developer.github.com/v3/apps/#find-repository-installation"
        url = f'https://api.github.com/repos/{owner}/{repo}/installation'

        headers = {'Authorization': f'Bearer {self.get_jwt().decode()}',
                   'Accept': 'application/vnd.github.machine-man-preview+json'}
        
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            raise Exception(f'Status code : {response.status_code}, {response.json()}')
        return response.json()['id']

    def get_installation_access_token(self, installation_id):
        "Get the installation access token for debugging."
        
        url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
        headers = {'Authorization': f'Bearer {self.get_jwt().decode()}',
                   'Accept': 'application/vnd.github.machine-man-preview+json'}
        
        response = requests.post(url=url, headers=headers)
        if response.status_code != 201:
            raise Exception(f'Status code : {response.status_code}, {response.json()}')
        return response.json()['token']

    def _extract(self, d, keys):
        "extract selected keys from a dict."
        return dict((k, d[k]) for k in keys if k in d)
    
    def _now_int(self):
        return int(time.time())

    def get_all_repos(self, installation_id):
        """Get all repos that this installation has access to.
        
        Useful for testing and debugging.
        """
        url = 'https://api.github.com/installation/repositories'
        headers={'Authorization': f'token {self.get_installation_access_token(installation_id)}',
                 'Accept': 'application/vnd.github.machine-man-preview+json'}
        
        response = requests.get(url=url, headers=headers)
        
        if response.status_code >= 400:
            raise Exception(f'Status code : {response.status_code}, {response.json()}')
        
        fields = ['name', 'full_name', 'id']
        return [self._extract(x, fields) for x in response.json()['repositories']]
    
    def get_reactions(self, owner: str, repo: str, comment_id: int, iat: str):
        """Get a list of reactions.

        https://developer.github.com/v3/reactions/#list-reactions-for-a-commit-comment
        """
        url = f'https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions'
        # installation_id = self.get_installation_id(owner, repo)
        # headers={'Authorization': f'token {self.get_installation_access_token(installation_id)}',
        #          'Accept': 'application/vnd.github.squirrel-girl-preview+json'}
        headers={'Authorization': f'token {iat}',
                 'Accept': 'application/vnd.github.squirrel-girl-preview+json'}
        
        response = requests.get(url=url, headers=headers)
        
        if response.status_code >= 400:
            raise Exception(f'Status code : {response.status_code}, {response.json()}')
        
        results = [self._extract(x, ['content']) for x in response.json()]
        # count the reactions
        return Counter([x['content'] for x in results])


    @staticmethod
    def unpack_issues(client, owner, repo, label_only=True):
        """
        extract relevant data from issues.

        returns a list of namedtuples which contains the following fields:
            title: str
            number: int
            body: str
            labels: list
            url: str

        """
        Issue = namedtuple('Issue', ['title', 'number', 'body', 'labels', 'url'])

        issue_data = []
        issues = list(client.issues_on(owner, repo))
        for issue in tqdm(issues, total=len(issues)):
            labels=[label.name for label in issue.labels()]
            
            # if there are no labels, then optionally skip
            if label_only and not labels:
                continue
    
            issue_data.append(Issue(title=issue.title,
                                    number=issue.number,
                                    body=issue.body,
                                    labels=[label.name for label in issue.labels()],
                                    url=issue.html_url)
                             )
        return issue_data

    def generate_installation_curl(self, endpoint):
        iat = self.get_installation_access_token()
        print(f'curl -i -H "Authorization: token {iat}" -H "Accept: application/vnd.github.machine-man-preview+json" https://api.github.com{endpoint}')