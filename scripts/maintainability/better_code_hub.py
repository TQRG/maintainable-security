"""Module to interact with BetterCodeHub.com."""

from time import sleep
from statistics import mean
import os

import requests
from retry import retry
import click

from maintainability import log
from maintainability import config
from maintainability import ghutils
from maintainability import gitutils
from maintainability.cache import BCHCache

ERROR_REPORT = {
    "error": True
}

SCRIPT_DIR = os.path.dirname(__file__)
CACHE = BCHCache(os.path.join(SCRIPT_DIR, "./bch_cache.zip"))

RETRY_ATTEMPTS = 10

@retry(tries=RETRY_ATTEMPTS, delay=5, backoff=10, max_delay=500)
def robust_analyze_commit(user, project, commit_sha):
    """Analyze any commit without failing."""
    log.info(f"Analyzing {user}/{project}...")
    try:
        report = external_analyze_commit_cached(
            user, project, commit_sha
        )
        if report.get('error'):
            log.warning(f"Commit {commit_sha} in {user}/{project} is out...")
        else:
            log.success(f'Maintainability: {compute_maintainability_score(report)}')
        return
    except WrongSessionDetails as error:
        log.error("Your BCH credentials are outdated.")
        click.pause("Update your config file and press any key to continue...")
        raise error
    except StillProcessing as error:
        log.warning(f"BCH is not ready: still processing our projects.")
        raise error
    except WrongCommitReports:
        pass
    except Exception as err:
        log.error(err)
        import pdb; pdb.set_trace()
    log.error(f"Skipping {user}/{project}.")

def external_analyze_commit_cached(user, project, commit_sha):
    """Analyze project commit without write privileges and cache results."""
    report = CACHE.get_stored_commit_analysis(user, project, commit_sha)
    if report:
        return report
    report = external_analyze_commit(user, project, commit_sha)
    CACHE.store_commit_analysis(user, project, commit_sha, report)
    return report

def external_analyze_commit(user, project, commit_sha):
    """Analyze project commit without write privileges."""
    try:
        forked_repo = ghutils.git_fork(user, project)
        result = analyze_commit(forked_repo.owner.login, project, commit_sha)
    except ProjectNotSupported:
        log.error(f"Project {user}/{project} is not supported by BCH. Skipping.")
        result = ERROR_REPORT
    return result

def analyze_commit(user, project, commit_sha):
    """Trigger a BCH scan for a specific commit of a GH project."""
    repo = ghutils.get_repo(user, project)
    temp_branch = _create_branch_for_commit(repo, commit_sha)
    if temp_branch is None:
        log.error(f"Could not create new branch in repo {repo} for commit {commit_sha}.")
        return ERROR_REPORT
    report = analyze_project_in_branch(repo, temp_branch)
    if report and report.get('sha') != commit_sha:
        log.error("BCH returned reports for a different commit.")
        raise WrongCommitReports
    return report

def analyze_project_in_branch(repo, branch):
    """Trigger a BCH scan of specific branch of a GH project."""
    default_branch_original = ghutils.get_default_branch(repo)
    ghutils.set_default_branch(repo, branch)
    sleep(5) #give time for this to take effect
    result = analyze_project(repo.owner.login, repo.name)
    ghutils.set_default_branch(repo, default_branch_original)
    return result

def _create_branch_for_commit(gh_repo, commit_sha):
    branch_name = _get_temporary_branch_name(commit_sha)
    branch = ghutils.get_branch(gh_repo, branch_name)
    if branch:
        log.warning(f"Using existing branch {branch_name} in {gh_repo.clone_url}.")
        return branch_name
    try:
        gitutils.create_branch_from_commit(gh_repo.clone_url, branch_name, commit_sha)
        return branch_name
    except gitutils.BranchAlreadyExists:
        log.error(
            f"Unexpected: branch {branch_name} in {gh_repo.clone_url} already exists."
            " Using it anyway"
        )
        return branch_name
    except gitutils.CommitNotFound:
        log.error("Commit cannot be reached. Leaving it permanently out of study.")
    return None

@retry(tries=5, delay=30, backoff=5, max_delay=300)
def collect_report(user, project):
    """Collect BCH report from last scan."""
    response = requests.get(
        "https://bettercodehub.com/edge/report/{}/{}".format(user, project),
        headers={
            "Accept":"application/json, text/plain, */*",
            "Accept-Language":"en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection":"keep-alive",
            "Content-Type":"application/json;charset=UTF-8",
            "Origin":"https://bettercodehub.com",
            "Pragma":"no-cache",
            "Referer":"https://bettercodehub.com/repositories",
            "X-XSRF-TOKEN":config.get("bettercodehub_xsrf_token"),
            "X-Requested-With":"XMLHttpRequest"
        },
        cookies={
            "SESSION":config.get("bettercodehub_session"),
            "XSRF-TOKEN":config.get("bettercodehub_xsrf_token"),
            "_ga":"GA1.2.1122828571.1537145587",
            "_gid":"GA1.2.23643035.1537950088",
        },
    )
    if response.ok:
        report = response.json()
        if 'analysisResults' not in report.keys():
            raise IncompleteCommitReports
        return report
    log.error("Could not collect BCH report from {}/{}".format(user, project))
    log.error("Tried to reach: "+response.url)
    log.error("BCH returned {}".format(response.status_code))
    log.error(response.content)
    if response.status_code == 400:
        log.warning("Results are not ready yet.")
        raise StillProcessing
    raise BetterCodeHubException

def compute_maintainability_score_old(report):
    """Compute maintainability score."""
    guidelines_scores = [
        1 - guideline.get('percentageOfNonCompliantCode')
        for guideline in report.get("analysisResults")
    ]
    return sum(guidelines_scores)/len(guidelines_scores)

def compute_maintainability_score(report):
    """Compute maintainability score."""
    total_loc = get_project_loc(report)
    guideline_results = []
    for guideline in report.get("analysisResults"):
        guideline_results.append(
            _compute_maintainability_for_guideline(guideline, total_loc)
        )
    return mean(guideline_results)


def _compute_maintainability_for_guideline(guideline, total_loc):
    """Computes maintainability for a guideline."""
    if guideline['guideline'] == "Automate Tests":
        return 0
    volumes = guideline.get('qualityProfileVolume')
    if guideline['guideline'] == "Keep Architecture Components Balanced":
        total_compoments = sum(volumes)
        volumes = [
            volume*total_loc/total_compoments
            for volume in volumes
        ]

    bad_thresholds = guideline['qualityProfileComplianceThresholds'][1:]
    print(bad_thresholds)
    return _compute_distance_to_thresholds(volumes, bad_thresholds)

def _compute_distance_to_thresholds(volumes, bad_thresholds):
    results = []
    for index, threshold in enumerate(bad_thresholds):
        print('threshold=', threshold)
        good_code_loc = sum(volumes[:index+1])
        print('good_code_loc', good_code_loc)
        bad_code_loc = sum(volumes[index+1:])
        print('bad_code_loc', bad_code_loc)
        granularity = 0.01 # thresholds have a minimum of 0.01
        bad_code_factor = ((1-threshold)/(threshold+granularity))
        print('bad_code_factor', bad_code_factor)
        results.append(good_code_loc - bad_code_factor*bad_code_loc)
    return mean(results)

def get_project_loc(report):
    """Get number of lines of code of the project."""
    first_guideline = report.get("analysisResults")[0]
    return sum(first_guideline['qualityProfileVolume'])

def analyze_project(user, project):
    "Scan and collect results from project."
    log.info("Adding project {}/{} to BetterCodeHub...".format(user, project))
    scan_project(user, project)
    log.success("Successfully added project to BCH!")
    log.info("Giving time for BCH to start analysis.")
    sleep(20)
    report = collect_report(user, project)
    return report

def scan_project(user, project):
    """Analyze GitHub project with BetterCodeHub."""
    response = _bch_request_post(
        "https://bettercodehub.com/edge/schedule/scan",
        {"repositoryName":f"{user}/{project}"}
    )
    if response.ok:
        return response
    log.error(f"BCH could not scan {user}/{project}")
    log.error("Tried to reach: "+response.url)
    log.error(f"BCH returned {response.status_code}")
    log.error(response.content)
    if response.status_code == 412:
        message = response.json().get('message')
        log.warning(f"Project {user}/{project} "
                    f"cannot be analyzed by BCH: {message}")
        if "default branch exceeds the limit" in message:
            raise ProjectExceedsLOCLimit
        if "contains no supported technologies" in message:
            raise ProjectNotSupported
    elif response.status_code == 405:
        log.error(
            "Please update session details in your config file."
        )
        raise WrongSessionDetails
    elif response.status_code == 429:
        log.error("Scan Project: still busy with another project")
        _reset_bch()
        raise StillProcessing
    else:
        log.error(f"Unknown failure with BCH in project {user}/{project}: "
                  f"status {response.status_code}")
        log.error(response.content)
        raise BetterCodeHubException
    return response

def _reset_bch():
    "Fetch BCH main page in case it is behaving unexpectedly."
    requests.get(
        "https://bettercodehub.com/repositories",
        cookies={
            "SESSION":config.get("bettercodehub_session"),
            "XSRF-TOKEN":config.get("bettercodehub_xsrf_token"),
            "_ga":"GA1.2.1122828571.1537145587",
            "_gid":"GA1.2.23643035.1537950088",
        },
    )

def _bch_request_post(url, data=None):
    return requests.post(
        url,
        json=data,
        cookies={
            "SESSION":config.get("bettercodehub_session"),
            "XSRF-TOKEN":config.get("bettercodehub_xsrf_token"),
            "_ga":"GA1.2.1122828571.1537145587",
            "_gid":"GA1.2.23643035.1537950088",
        },
        headers={
            "Accept":"application/json, text/plain, */*",
            "Accept-Language":"en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection":"keep-alive",
            "Content-Type":"application/json;charset=UTF-8",
            "Origin":"https://bettercodehub.com",
            "Pragma":"no-cache",
            "Referer":"https://bettercodehub.com/repositories",
            "X-XSRF-TOKEN":config.get("bettercodehub_xsrf_token"),
            "X-Requested-With":"XMLHttpRequest"
        }
    )

def _get_temporary_branch_name(commit_sha):
    return "energy_test_{}".format(commit_sha[:7])

class BetterCodeHubException(Exception):
    """Base Class for BCH exceptions."""

class ProjectNotSupported(BetterCodeHubException):
    """Exception raised when the project is not supported by BCH."""

class ProjectExceedsLOCLimit(ProjectNotSupported):
    """Exception raised when BCH does not accept the project due to its size."""

class StillProcessing(BetterCodeHubException):
    """Exception raised when BCH blocks access for too many requests."""

class WrongSessionDetails(BetterCodeHubException):
    """Exception Raised when session details in config are outdated."""

class WrongCommitReports(BetterCodeHubException):
    """Exception Raised when BCH reports are from an unexpected commit."""

class IncompleteCommitReports(BetterCodeHubException):
    """Exception Raised when BCH reports are incomplete."""

if __name__ == '__main__':
    pass
