"""Module with all the instrumentation used for SZZ.
"""

import csv
import random

from contexttimer import timer
import pandas as pd
import click

from maintainability import ghutils, gitutils, log

CLONAGE_DIR = "./tmp"

@click.command()
@click.option('--security-dataset', prompt=True, default="../baselines/db_regular_changes_random.csv",
              help="Input dataset of security commits.")
@click.option('--regular-dataset', prompt=True, default="../baselines/db_regular_changes_random.csv",
              help="Output dataset with regular commits.")
def tool(security_dataset, regular_dataset):
    """CLI to collect random commits and analyze maintainability."""
    df = pd.read_csv(security_dataset)
    add_random_regular_commits(df, regular_dataset)

@timer()
def add_random_regular_commits(rows, regular_dataset):
    """Add refactoring commits in the dataset."""
    log.info(f"Will analyze {len(rows)} commits.")
    for i, row in rows[~pd.notnull(rows['sha-reg'])][::-1].iterrows():        
        if 'random_commit' not in row.keys():
            user = row['owner']
            project = row['project']
            with ghutils.GithubCloneRepoPersistent(user, project, CLONAGE_DIR):
                try:
                    commits = gitutils.get_all_commits('.')
                    regular_commit = random.choice(commits)
                    rows.at[i, 'sha-reg'] = regular_commit
                    rows.at[i, 'sha-reg-p'] = gitutils.resolve_commit('.', f"{regular_commit}^1")
                except:
                    rows.at[i, 'sha-reg'] = 'Error'
                    rows.at[i, 'sha-reg-p'] = 'Error'
                    import pdb; pdb.set_trace()
        rows.to_csv(regular_dataset, index=False)

if __name__ == '__main__':
    tool() # pylint: disable=no-value-for-parameter
