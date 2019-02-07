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


def language_dist(commits):
    
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
        if i != 'others': 
            dic_lang['lang'].append(lang_trans[i])
            dic_lang['no'].append(dic[i]/len(df['language']))
    
    lang = pd.DataFrame(dic_lang)
    
    ax = lang['no'].plot(kind='barh', figsize=(10, 11), fontsize=12, color="#3F86DB")
    vals = ax.get_xticks()
    ax.set_xticklabels(['{:,.0%}'.format(x) for x in vals])
    ax.set_yticklabels(dic_lang['lang'], minor=False)
    plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.05)
    plt.gca().xaxis.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig('../paper/ICPC19/figures/language_dist.pdf')

def type_dist(projects):
    
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
    
    ax = app_type['no'].plot(kind='barh', figsize=(10, 7), fontsize=12, color="#3F86DB")
    vals = ax.get_xticks()
    ax.set_xticklabels(['{}'.format(int(x)) for x in vals])
    ax.set_yticklabels(app_type['type'], minor=False)
    plt.subplots_adjust(left=0.31, right=0.9, top=0.9, bottom=0.05)
    plt.gca().xaxis.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig('../paper/ICPC19/figures/type_dist.pdf')

def main(projects, commits):    
    
    language_dist(commits)
    plt.clf()
    type_dist(projects)
    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--projects-csv',metavar='projects-csv',required=True,help='the projects filename')
    parser.add_argument('--commits-csv',metavar='commits-csv',required=True,help='the commits filename')
    
    args = parser.parse_args()
    main(projects=args.projects_csv, commits=args.commits_csv)