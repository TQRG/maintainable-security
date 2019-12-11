"""Module to evalutate maintainability."""

import csv
import logging

import click
from contexttimer import timer

from maintainability import log
import maintainability.better_code_hub as bch

RETRY_ATTEMPTS = 10

@click.command()
@click.option('--dataset', prompt=True, default="../dataset/db_icpc20_single_fix.csv",
              help="Dataset with commits for comparison.")
def tool(dataset):
    """CLI to evaluate maintainability."""
    log.info('Starting dataset analysis!')
    logging.basicConfig(level='INFO')
    with open(dataset, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        rows = list(csv_reader)
        collect_maintainability(rows)

@timer()
def collect_maintainability(rows):
    """Collect maintainability of regular/random commits"""
    for row in rows:
        user = row['owner']
        project = row['project']
        # if user == 'torvalds' and project == 'linux':
        #     continue
        commit_sha = row['sha']
        parent_commit_sha = row['sha-p']
        try:
            bch.robust_analyze_commit(user, project, commit_sha)
            bch.robust_analyze_commit(user, project, parent_commit_sha)
        except Exception as error:
            log.error(error)
            log.error("Exception not expected")
            if not isinstance(error, bch.BetterCodeHubException):
                import pdb; pdb.set_trace()
            log.error(f"Skipping {user}/{project}.")


if __name__ == '__main__':
    tool() # pylint: disable=no-value-for-parameter
