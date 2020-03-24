from github import Github
from bs4 import BeautifulSoup
import requests
from github.GithubException import UnknownObjectException, GithubException
from tqdm import tqdm
from collections import OrderedDict

import pandas as pd
import numpy as np
import datetime
import sys
import re
import time

import config


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
    
def get_repo_owner(df):
    df['owner'] = df['Project'].map(lambda x: x.split('/')[-2])
    return df

def get_repo_name(df):
    df['project']  = df['Project'].map(lambda x: x.split('/')[-1])
    return df

# get Date, Message and Sha Parent of each commit
def get_commits_info(df): 
    # iterating all dataframe rows
    for idx, row in tqdm(df.iterrows()):
        if row['Dataset'] == 'SECBENCH' and row['Date'] is np.nan:
            repo = g.get_repo('{}/{}'.format(row['owner'], row['project']))
            c = repo.get_commit(sha=row['sha'])
    
            commit_info = c.commit
            parents_info = c.parents
    
            df.at[idx,'Date'] = commit_info.author.date
            df.at[idx, 'Message'] = commit_info.message.strip()
    
            if len(parents_info) == 1:
                df.at[idx, 'sha-p'] = parents_info[0].sha
            else:
                df.at[idx, 'sha-p'] = ':'.join([p.sha for p in parents_info])
            
    return df

def convert_col_to_datetime(df):
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def get_first_and_last_fix_commits(df):
    for u in df['Code'].unique():
        print('============= {} ============='.format(u))
        first_fix, last_fix = df[df['Code'] == u]['Date'].min(), df[df['Code'] == u]['Date'].max()
        for i, r in df[df['Code'] == u].iterrows():
            if r['Date'] == last_fix:
                df.at[i, 'Type'] = 'LAST'
            if r['Date'] == first_fix:
                df.at[i, 'Type'] = 'FIRST'
    return df

def filter_non_last_or_first(df):
    return df[(df['Type'] == 'LAST') | (df['Type'] == 'FIRST')]

def delete_dups(df):
    return df[df['Duplicate'] == 0]

def adjust_multiple_fixes_data(df):
    final = pd.DataFrame()
    for u in df['Code'].unique():
        commits = df[df['Code'] == u]
        if len(commits) > 1:
            commits['sha-p'][commits['Type'] == 'LAST'] = commits[commits['Type'] == 'FIRST']['sha-p'].values[0]
            final = final.append(commits[commits['Type'] == 'LAST'], 
                                    ignore_index = True)
        else:
            final = final.append(commits, ignore_index = True)
    return final
    
def get_cve_from_commit_msg(df):
    expr = 'CVE-\d{4}-\d{4,7}'
    for i, r in tqdm(df.iterrows()):
        if r['Dataset'] == 'SECBENCH':
            df.at[i, 'Code'] = ','.join(re.findall(expr, r['Message']))
    return df
            

def get_score(soup):
    score_calc = soup.find(id='p_lt_WebPartZone1_zoneCenter_pageplaceholder_p_lt_WebPartZone1_zoneCenter_VulnerabilityDetail_VulnFormView_Cvss2CalculatorAnchor')
    if score_calc != None:
        return score_calc.getText().strip().split(' ') 
    else:
        return [0, None]
    
def get_cwe(soup):
    cwe_table = soup.find(id='p_lt_WebPartZone1_zoneCenter_pageplaceholder_p_lt_WebPartZone1_zoneCenter_VulnerabilityDetail_VulnFormView_VulnTechnicalDetailsDiv')
    if cwe_table != None:
        cwe_tds = cwe_table.find_all('td')
        if len(cwe_tds) > 0:
            return cwe_tds[0].getText()
        else:
            return None
    else:
        return None
    
def get_cve_details_from_nvd(df, dataset, out):
    nvd_url = 'https://nvd.nist.gov/vuln/detail/'
    df['Severity'] = df['Severity'].astype(str)
    
    for i, r in tqdm(df.iterrows()):
        if r['Dataset'] == dataset and r['Code'] is not np.nan:
            if 'CVE' in r['Code'] and r['CWE'] is np.nan:
                print(r['Code'])
                time.sleep(2)
                results = requests.get('{}{}'.format(nvd_url, r['Code']))
                soup = BeautifulSoup(results.content, 'html.parser')
    
                df.at[i, 'Score'], df.at[i, 'Severity'] = get_score(soup)
                df.at[i, 'CWE'] = get_cwe(soup)
                
            df.to_csv(out, index=False)
            print('Saving...')
        
    return df
    
df = pd.read_csv(sys.argv[1])
g = _get_github_api()
out = sys.argv[2]

#df.to_csv(out, index=False)
print(df)

count = 0; 
for i, row in tqdm(df.iterrows()):
    
    langs = OrderedDict()
    
    if row['Language'] != 'EMPTY':
        continue
        
    user = row['owner']
    project = row['project']
    if user == 'torvalds' or user == 'chineking':
        continue
    print(user, project)
    
    try:
        repo = g.get_user(user).get_repo(project)
    except:
        pass
    
    diff_files = repo.compare(row['sha-p'], row['sha']).files
    files_ext = [i.filename.split('.')[-1] for i in diff_files]
    
    for j in files_ext:
        if j not in ('STATUS'):
            if j not in langs:
                langs[j] = 1
            else:
                langs[j] += 1

    if len(files_ext) > 1: 
        df.at[i, 'Language'] = str(list(langs))
    elif len(files_ext) == 0:
        df.at[i, 'Language'] = 'ERROR'
    else:
        df.at[i, 'Language'] = list(langs)[0]

    count +=1
    
    if count == 20:
        df.to_csv(out, index=False)
        print('Saving...')
        count = 0
    
df.to_csv(out, index=False)



