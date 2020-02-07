"""Module with all the instrumentation used for SZZ.
"""

import csv
import random
import requests

from contexttimer import timer
import click
import time
import pandas as pd

from maintainability import ghutils, gitutils, log

CLONAGE_DIR = "./tmp"

@click.command()
@click.option('--security-dataset', prompt=True, default="../dataset/db_icpc20_release_reg_final.csv",
              help="Input dataset of security commits.")
@click.option('--regular-dataset', prompt=True, default="../dataset/db_icpc20_release_reg_final.csv",
              help="Output dataset with regular commits.")
def tool(security_dataset, regular_dataset):
    """CLI to collect random commits and analyze maintainability."""
    df = pd.read_csv(security_dataset)
    rows = add_random_regular_commits(df)

@timer()
def add_random_regular_commits(rows, regular_dataset):
    """Add refactoring commits in the dataset."""
    log.info(f"Will analyze {len(rows)} commits.")

    for i, row in rows.iterrows():        
        if 'random_commit' not in row.keys() and row['reg'] != 'FOUND':
            user = row['owner']
            project = row['project']
            sha = row['sha']
            sha_p = row['sha-p']

            repo = ghutils.get_repo(user, project)
            print(user, project, sha, sha_p)
            diff_files = repo.compare(sha_p, sha).files
            size = len(diff_files)
            adds = sum([i.additions for i in diff_files])
            dels = sum([i.deletions for i in diff_files])
            print(user, project, sha, sha_p, adds, dels)

            with ghutils.GithubCloneRepoPersistent(user, project, CLONAGE_DIR):

                commits = gitutils.get_all_commits('.')
                
                count = 0; step = 1; limit = 301
                while count < limit:

                    regular_commit = random.choice(commits)
                    regular_commit_parent = gitutils.resolve_commit('.', f"{regular_commit}^1")

                    if regular_commit_parent == None:
                        continue

                    diff_files_reg = repo.compare(regular_commit_parent, regular_commit).files

                    size_reg = len(diff_files_reg)
                    adds_reg = sum([i.additions for i in diff_files_reg])
                    dels_reg = sum([i.deletions for i in diff_files_reg])

                    adds_reg_n = [adds+i for i in range(-step, 1+step, 1) if adds+i > 0]
                    dels_reg_n = [dels+i for i in range(-step, 1+step, 1) if dels+i > 0]

                    if adds_reg in adds_reg_n and dels_reg in dels_reg_n and sha != regular_commit:
                        print('match')
                        print(user, project, regular_commit, regular_commit_parent, adds_reg, dels_reg)
                        rows.at[i, 'sha-reg'] = regular_commit
                        rows.at[i, 'sha-reg-p'] = regular_commit_parent
                        rows.at[i, 'reg'] = 'FOUND'
                        break
                    else:
                        print('no match', adds_reg, dels_reg)

                    count+=1

                    if count % 5 == 0:
                        step+=1
                        print('Step growth. step =', step)

                    if count == limit:
                        rows.at[i, 'reg'] = 'REPEAT'

        rows.to_csv(regular_dataset, index=False)
                
    return rows
    
if __name__ == '__main__':
    tool() # pylint: disable=no-value-for-parameter
