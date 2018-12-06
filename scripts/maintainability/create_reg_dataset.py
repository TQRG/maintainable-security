"""Module with all the instrumentation used for SZZ.
"""

import csv
import random

from contexttimer import timer
import click

from maintainability import ghutils, gitutils, log

CLONAGE_DIR = "./tmp"

@click.command()
@click.option('--security-dataset', prompt=True, default="../dataset/commits_patterns_sec.csv",
              help="Input dataset of security commits.")
@click.option('--regular-dataset', prompt=True, default="../dataset/commits_regular.csv",
              help="Output dataset with regular commits.")
def tool(security_dataset, regular_dataset):
    """CLI to collect random commits and analyze maintainability."""
    rows = _collect_rows(security_dataset)
    add_random_regular_commits(rows)
    _save_dataset(rows, regular_dataset)

@timer()
def add_random_regular_commits(rows):
    """Add refactoring commits in the dataset."""
    log.info(f"Will analyze {len(rows)} commits.")
    for row in rows:
        if 'random_commit' not in row.keys():
            user = row['owner']
            project = row['project']
            with ghutils.GithubCloneRepoPersistent(user, project, CLONAGE_DIR):
                try:
                    commits = gitutils.get_all_commits('.')
                    regular_commit = random.choice(commits)
                    row['sha'] = regular_commit
                    row['sha_p'] = gitutils.resolve_commit('.', f"{regular_commit}^1")
                except:
                    row['sha'] = 'Error'
                    row['sha_p'] = 'Error'
                    import pdb; pdb.set_trace()
    return rows


def _collect_rows(dataset):
    with open(dataset, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        rows = list(csv_reader)
    return rows

def _save_dataset(rows, output_file):
    """Save dataset in a csv format file."""
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, rows[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(rows)
    click.secho("Saved {} refactoring commits to {}.".format(len(rows), output_file, fg='green'))

if __name__ == '__main__':
    tool() # pylint: disable=no-value-for-parameter
