"""Module to evalutate maintainability."""

import csv
import logging

import click
from contexttimer import timer
import pandas as pd

from maintainability import log
import maintainability.better_code_hub as bch

RETRY_ATTEMPTS = 10

@click.command()
@click.option('--dataset', prompt=True, default="../dataset/db_release_security_fixes.csv",
              help="Dataset with commits for comparison.")
@click.option('--commit', prompt=True, default="security",
              help="type of dataset")
def tool(dataset, commit):
    """CLI to evaluate maintainability."""
    log.info('Starting dataset analysis!')
    logging.basicConfig(level='INFO')
    df = pd.read_csv(dataset)
    collect_maintainability(df, commit, dataset)

@timer()
def collect_maintainability(rows, commit, dataset):
    """Collect maintainability of regular/random commits"""
    for i, row in rows[::-1].iterrows():        
        user = row['owner']
        project = row['project']
        
        if commit == 'regular':            
            commit_sha = row['sha-reg']
            parent_commit_sha = row['sha-reg-p']
        else:
            commit_sha = row['sha']
            parent_commit_sha = row['sha-p']
               
        try:
            bch.robust_analyze_commit(user, project, commit_sha)
            bch.robust_analyze_commit(user, project, parent_commit_sha)
        except Exception as error:
            log.error(error)
            rows.at[i, 'ERROR'] = 'YES'
            log.error("Exception not expected")
            if not isinstance(error, bch.BetterCodeHubException):
                import pdb; pdb.set_trace()
            log.error(f"Skipping {user}/{project}.")
        
        rows.to_csv(dataset, index=False)

if __name__ == '__main__':
    tool() # pylint: disable=no-value-for-parameter
