"""Functions to interact with the Github API."""

import os
from urllib.parse import urlparse
from github import Github
from github.GithubException import UnknownObjectException, GithubException
from requests.exceptions import ReadTimeout
from retry import retry

from maintainability import log, config, gitutils

_GITHUB_API = None
def _get_github_api():
    """Init Github API client."""
    # authenticate github api
    global _GITHUB_API
    if _GITHUB_API is None:
        _GITHUB_API = Github(
            login_or_token=config.get('github_token')
        )
    return _GITHUB_API

def get_repo(user, project):
    """Get repo of a repository."""
    try:
        return _get_github_api().get_user(user).get_repo(project)
    except:
        pass
    return None

def _get_path_items_from_url(url):
    parse = urlparse(url)
    return parse.path.strip().split('/')

def _parse_pr_link(url):
    _, user, project, _, pull, *_ = _get_path_items_from_url(url)
    return (user, project, pull)

def get_commits_from_pull_request(pr_url):
    """Get merge and base commits of a pull request."""
    user, project, pr_number = _parse_pr_link(pr_url)
    repo = get_repo(user, project)
    pull = repo.get_pull(int(pr_number))
    merge_commit = pull.merge_commit_sha
    if merge_commit is None:
        merge_commit = pull.head.sha
        log.warning('Warning: merge commit is None:\n{}'.format(pr_url))
    base_commit = pull.base.sha
    try:
        commit_url = repo.get_git_commit(merge_commit).html_url
    except UnknownObjectException:
        merge_commit = pull.head.sha
        commit_url = repo.get_git_commit(merge_commit).html_url
        log.warning('Warning: merge commit is not reachable:\n{}'.format(pr_url))
    base_commit_url = repo.get_git_commit(base_commit).html_url
    return commit_url, base_commit_url

def get_repo_url_from_commit(commit_url):
    """Get the Github repo url from a commit url."""
    user, project, _ = parse_commit_url(commit_url)
    return get_repo_url(user, project)

def get_repo_url(user, project):
    """Get the Github repo url given its user and project name. """
    return f"https://github.com/{user}/{project}.git"

def parse_commit_url(url):
    """Parse commit url."""
    _, user, project, _, commit, *_ = _get_path_items_from_url(url)
    return (user, project, commit)

@retry(ReadTimeout, tries=3)
def _get_commit(repo, commit_sha):
    try:
        return repo.get_git_commit(commit_sha)
    except ReadTimeout:
        log.error("Error when trying to get commit {} from repo {}".format(commit_sha, repo))
        raise

def get_parent_commit(commit_url):
    """Get parent of the commit in the url."""
    user, project, commit_sha = parse_commit_url(commit_url)
    repo = get_repo(user, project)
    try:
        commit = _get_commit(repo, commit_sha)
    except UnknownObjectException:
        log.error("Error: could not find parent of commit {}".format(commit_url))
        return None
    except ReadTimeout:
        log.error("Error: connection to github api timed out {}".format(commit_url))
        return None
    parents = commit.parents
    if len(parents) in (1, 2):
        base_parent = parents[0]
    else:
        log.error("Error: unexpected number of parents in commit {}".format(commit_url))
        base_parent = None
    if base_parent:
        return base_parent.html_url
    return None

def get_logged_user():
    """Get Github user that is logged in."""
    return _get_github_api().get_user()

def git_fork(user, project):
    """Fork Github project."""
    repo = get_repo(user, project)
    logged_user = get_logged_user()
    forked_repo = get_repo(logged_user.login, project)
    if forked_repo is None:
        logged_user.create_fork(repo)
        forked_repo = get_repo(logged_user.login, project)
    return forked_repo


@retry(GithubException, tries=3)
def set_default_branch(repo, branch_name):
    """Set default branch of Github repository."""
    try:
        repo.edit(default_branch=branch_name)
    except GithubException:
        log.error("Could not change default branch of {} to {}".format(repo, branch_name))
        raise

def get_default_branch(repo):
    """Get default branch of Github repository."""
    return repo.default_branch

def get_branch(repo, branch_name):
    """Try to get branch from repo."""
    try:
        return repo.get_branch(branch_name)
    except GithubException:
        return None

def paginated_list(repo):
    return repo.get_commits()

def get_commits(paginated_list, page):
    return paginated_list.get_page(page)

class GithubCloneRepoPersistent:
    """Context manager for github clones that will be kept in local storage."""
    def __init__(self, user, project, local_dir):
        self.user = user
        self.project = project
        self.local_dir = os.path.expanduser(local_dir)
        self.previous_path = None

    def __enter__(self):
        gitutils.clone_full(self._get_repo_url(), self._get_clone_dir())
        self.previous_path = os.getcwd()
        os.chdir(self._get_clone_dir())
        return self._get_clone_dir()

    def __exit__(self, etype, value, traceback):
        os.chdir(self.previous_path)

    def _get_clone_dir(self):
        return os.path.join(self.local_dir, f"{self.user}___{self.project}")

    def _get_repo_url(self):
        return get_repo_url(self.user, self.project)
