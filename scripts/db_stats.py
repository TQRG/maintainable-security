import maintainability.better_code_hub as bch
import argparse
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main(projects):    
    df = pd.read_csv(projects)
    stats = df[['forks','stars', 'watchers', 'contributors', 'commits', 'branches', 'releases', 'size', 't_issues', 't_prs']].describe()
    stats.to_csv('dataset_statistics.csv')    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--projects-csv',metavar='projects-csv',required=True,help='the projects filename')

    args = parser.parse_args()
    main(projects=args.projects_csv)