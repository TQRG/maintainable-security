"""Utils to manipulate local git repos."""

import tempfile

from git import Repo
from git.exc import GitCommandError

from maintainability import log

def git_clone(url, repo_dir):
    """Clone repo into a directory directory."""
    try:
        return Repo.clone_from(url, repo_dir)
    except GitCommandError:
        repo = Repo(repo_dir)
        if repo.bare:
            raise Exception(f"Could not clone '{url}'.")
        return repo

# def _git_head_to_commit(repo, commit_sha):
#     repo.head.reference = repo.commit(commit_sha)

def _reset_to_commit(repo, commit_sha):
    repo.git.reset('--hard', commit_sha)

def _force_push(repo):
    repo.git.push('-f')

def _fetch_all(repo):
    for remote in repo.remotes:
        remote.fetch()

class GitUtilsExeption(Exception):
    """Base Class for gitutils exceptions."""

class CommitNotFound(GitUtilsExeption):
    """Exception raised when commit is not found.

    Attributes:
        repo -- identification of the repo (e.g., url)
        commit_sha -- identification of commit (e.g., sha)
    """

    def __init__(self, repo, commit_sha):
        self.repo = repo
        self.commit_sha = commit_sha
        super().__init__()

class BranchAlreadyExists(GitUtilsExeption):
    """Exception raised when commit is not found.

    Attributes:
        repo -- identification of the repo (e.g., url)
        commit_sha -- identification of commit (e.g., sha)
    """

    def __init__(self, repo, commit_sha):
        self.repo = repo
        self.commit_sha = commit_sha
        super().__init__()

def create_branch_from_commit(repo_url, branch_name, commit_sha):
    """Create a new branch to push commit."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        log.info(commit_sha)
        log.info(tmpdirname)
        repo = git_clone(repo_url, tmpdirname)
        try:
            repo.git.branch(branch_name, commit_sha)
        except GitCommandError as git_error:
            log.error('create_branch_from_commit')
            log.error(git_error)
            _, _, error_message, *_ = git_error.args
            if "Not a valid branch point" in error_message.decode():
                log.error("Commit {} does not exist for {}".format(commit_sha, repo))
                raise CommitNotFound(repo_url, commit_sha)
            if "fatal: A branch named " in error_message.decode():
                raise BranchAlreadyExists(repo_url, commit_sha)
        repo.git.push("-f", repo.remote().name, branch_name)

def clone_full(repo_url, tmpdirname):
    """Clone and fetch all content."""
    repo = git_clone(repo_url, tmpdirname)
    _fetch_all(repo)
    return repo


def git_push_commit(repo_url, commit_sha):
    """Force a Github repo to HEAD to an old commit."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        log.info(commit_sha)
        log.info(tmpdirname)
        repo = clone_full(repo_url, tmpdirname)
        _reset_to_commit(repo, commit_sha)
        _force_push(repo)

def get_commit_message(repo_dir, commit_sha):
    """Get commit message."""
    repo = Repo(repo_dir)
    return repo.commit(commit_sha).message

def get_all_commits(repo_dir):
    """Return list of all commits in repo."""
    repo = Repo(repo_dir)
    return [commit.hexsha for commit in repo.iter_commits()]

def get_commit_timestamp(repo_dir, commit_sha):
    """Get commit timestamp."""
    commit = Repo(repo_dir).commit(commit_sha)
    return commit.authored_datetime

def get_time_between_commits(repo_dir, commit_a, commit_b):
    """Get time passed in seconds between commits a and b."""
    date_a = get_commit_timestamp(repo_dir, commit_a)
    date_b = get_commit_timestamp(repo_dir, commit_b)
    return (date_b - date_a).total_seconds()

def resolve_commit(repo_dir, commit_sha_expression):
    """Resolve commit sha with ^~expressions"""
    repo = Repo(repo_dir)
    return repo.commit(commit_sha_expression).hexsha
