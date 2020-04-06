import maintainability.better_code_hub as bch
import argparse
import csv
import collections
import pandas as pd
import numpy as np
import matplotlib
matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['mathtext.fontset'] = 'cm'
import matplotlib.pyplot as plt


def language_dist(commits, output):
    
    df = pd.read_csv(commits)
    
    lang_trans = {'objc':'Objective-C', 'php':'PHP', 'ruby':'Ruby', 'c':'C', 'c++':'C++', 'groovy':'Groovy', 'javascript':'JavaScript',
                    'python':'Python', 'java':'Java', 'objc++':'Objective-C++', 'scala':'Scala', 'swift':'Swift', 'smarty':'Smarty'}
    
    dic = {}
    for i in df['language']:
        if i not in dic:
            dic[i] = 1
        else:
            dic[i] += 1
    
    dic_lang = {'lang':[], 'no':[]}
    
    dic_lang['lang'].append('Others')
    dic_lang['no'].append(dic['others']/len(df['language']))
    
    for i in dic:
        if i not in ('others','php','ruby','c','python','java'): 
            dic_lang['lang'].append(lang_trans[i])
            dic_lang['no'].append(dic[i]/len(df['language']))
    
    for i in ('php','ruby','c','python','java'):
        dic_lang['lang'].append(lang_trans[i])
        dic_lang['no'].append(dic[i]/len(df['language']))
    
    lang = pd.DataFrame(dic_lang)
    print(lang)
    

    fig, ax = plt.subplots(figsize=(10, 8))
    ax = lang['no'].plot(kind='barh', fontsize=16, color="#3F86DB", ax=ax)
    vals = ax.get_xticks()
    ax.set_xticklabels(['{:,.0%}'.format(x) for x in vals])
    ax.set_yticklabels(dic_lang['lang'], minor=False)
    ax.xaxis.grid(True, linestyle='--')
    fig.tight_layout()
    fig.savefig('{}/language_dist.pdf'.format(output))

def type_dist(projects, output):
    
    df = pd.read_csv(projects)
    
    dic = {}
    for i in df['domain']:
        if i not in dic:
            dic[i] = 1
        else:
            dic[i] += 1
    
    dic_type = {'type':[], 'no':[]}   
    
    for i in dic:
        dic_type['type'].append(i)
        dic_type['no'].append(dic[i]) 
                
    app_type = pd.DataFrame(dic_type)
    print(app_type)
    
    fig, ax = plt.subplots()
    app_type['no'].plot(kind='barh', figsize=(10, 4), fontsize=16, color="#3F86DB", ax=ax)
    vals = ax.get_xticks()
    ax.set_xticklabels(['{}'.format(int(x)) for x in vals])
    ax.set_yticklabels(app_type['type'], minor=False)
    ax.xaxis.grid(True, linestyle='--')
    fig.tight_layout()
    fig.savefig('{}/type_dist.pdf'.format(output))

def main(projects, commits, output):    
    
    language_dist(commits, output)
    plt.clf()
    type_dist(projects, output)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--projects-csv',metavar='projects-csv',required=True,help='the projects filename path')
    parser.add_argument('--commits-csv',metavar='commits-csv',required=True,help='the commits filename path')
    parser.add_argument('--output',metavar='output',required=True,help='the ouput folder')
    
    args = parser.parse_args()
    main(projects=args.projects_csv, commits=args.commits_csv, output=args.output)