import maintainability.better_code_hub as bch
import argparse
import csv
import collections
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

    
    

def main(projects):    
    df = pd.read_csv(projects)
    
    lang_trans = {'objc':'Objective-C', 'php':'PHP', 'ruby':'Ruby', 'c':'C', 'c++':'C++', 'groovy':'Groovy', 'javascript':'JavaScript',
                    'python':'Python', 'java':'Java', 'objc++':'Objective-C++', 'scala':'scala', 'swift':'Swift', 'smarty':'Smarty'}
    
    
    dic = {}
    for i in df['language']:
        if i not in dic:
            dic[i] = 1
        else:
            dic[i] += 1
    
    dic_lang = {'lang':[], 'no':[]}
    for i in dic:
        if i == 'others':
            no = dic['others']
        else:
            dic_lang['lang'].append(lang_trans[i])
            dic_lang['no'].append(dic[i]/len(df['language']))
    
    dic_lang['lang'].append('Others')
    dic_lang['no'].append(dic['others']/len(df['language']))
    
    lang = pd.DataFrame(dic_lang)
    
    ax = lang['no'].plot(kind='bar', title ="Language Distribution", figsize=(10, 7), fontsize=11, color="#2541F0")
    ax.set_xlabel("Language", fontsize=11)
    ax.set_ylabel("", fontsize=11)
    vals = ax.get_yticks()
    ax.set_yticklabels(['{:,.0%}'.format(x) for x in vals])
    ax.set_xticklabels(dic_lang['lang'], minor=False)
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.3)
    plt.gca().yaxis.grid(True, linestyle='--')
    
    plt.savefig('../paper/ICPC19/figures/language_dist.pdf')
    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--projects-csv',metavar='projects-csv',required=True,help='the projects filename')

    args = parser.parse_args()
    main(projects=args.projects_csv)