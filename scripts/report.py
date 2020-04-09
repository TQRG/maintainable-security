import maintainability.better_code_hub as bch
import stats.chart as chart
import argparse
import csv
import collections
import pandas as pd
import numpy as np
import matplotlib
import seaborn as sns

matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['mathtext.fontset'] = 'cm'

import matplotlib.pyplot as plt
from scipy.stats import wilcoxon
from statistics import mean, stdev
from math import sqrt
import pandas as pd
from collections import OrderedDict

    
def report_guidelines_violin_plot(reports, filename):
    
    df = pd.read_csv(filename)
    
    stats = {'value':[], 'fix': [], 'guideline':[]}
    for i, r in df.iterrows():
        for g in guidelines:
            stats['guideline'].append(g)
            stats['guideline'].append(g)
            stats['value'].append(r[g+'-prev'])
            stats['fix'].append('before')
            stats['value'].append(r[g+'-fix'])
            stats['fix'].append('after')
    
    f = pd.DataFrame.from_dict(stats)
    print(f)
    
    g = sns.violinplot(x="guideline", y="value", hue="fix", data=f, palette="Set2", split=True)
    #g.set_yscale("symlog")
    plt.ylim(-9000000,9000000) 
    plt.xticks(rotation=90)
    
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(18.5, 10.5, forward=True)
    fig.tight_layout()
    fig.savefig('{}/{}'.format(reports, "maintainability_per_guideline_sns.pdf"))



def read_cwe_composites(file):
    composites = dict()
    with open(file, 'r') as i:
        f = i.readlines()
        for group in f:
            cwes = group.strip().split('\t')
            if cwes[0] not in composites:
                composites[cwes[0]] = cwes[1::]
        return composites

def check_if_belongs_to_cwe(key):
    composites = read_cwe_composites('cwe')
    if key in composites.keys():
        return key
    for i in composites:
        if key in composites[i]:
            return i
    return None

def report_maintainability_cwe(reports, df, wilcoxon=True, boxes_start=9, text_start=0.55, delta=1, left_padding=0.25, f_size=9):
                
    for i, r in df.iterrows():
        if r['CWE'] is not np.nan:
            cwe = check_if_belongs_to_cwe(r['CWE'])
            if cwe != None:
                df.at[i, 'CWE'] = cwe
    
    cwes = [i for i in df['CWE'].unique() if str(i) != 'nan' and (len(df[df['CWE'] == i]) > 19) and 'CWE' in i]
    print(cwes)
    for i, r in df.iterrows():
        if r['CWE'] not in cwes:
            df.at[i, 'CWE'] = 'MISC'
    
    cwes = ['MISC'] + cwes
    
    print(df[df['CWE'] == 'MISC'])
    
    results = {}
    for s in cwes:
        print(s)
        impact = [0, 0, 0]
        impact[0] = df[(df['diff'] < 0) & (df['CWE'] == s)].shape[0]
        impact[1] = df[(df['diff'] > 0) & (df['CWE'] == s)].shape[0]
        impact[2] = df[(df['diff'] == 0) & (df['CWE'] == s)].shape[0]
        results[s] = impact
    print(results)

    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in cwes]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in cwes]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in cwes]),
        'N': pd.Series([sum(results[i]) for i in cwes if wilcoxon]),
        'mean': pd.Series([_print_hypothesis_test(df[df['CWE'] == i]['diff'])['mean'][0] for i in cwes if wilcoxon]),
        'med': pd.Series([_print_hypothesis_test(df[df['CWE'] == i]['diff'])['med'][0] for i in cwes if wilcoxon]),
        'p': pd.Series([_print_hypothesis_test(df[df['CWE'] == i]['diff'])['pvalue'][0] for i in cwes if wilcoxon]),
        'type': pd.Series([i for i in cwes])}

    absoluto = {'neg': pd.Series([results[i][0] for i in cwes]),
        'pos': pd.Series([results[i][1] for i in cwes]),
        'nul': pd.Series([results[i][2] for i in cwes]),
        'type': pd.Series([i for i in cwes]),
        'p': pd.Series([_print_hypothesis_test(df[df['CWE'] == i]['diff'])['pvalue'][0] for i in cwes if wilcoxon])}

    df = pd.DataFrame(d)
    abso = pd.DataFrame(absoluto)
    index = np.arange(len(d['type']))

    fig = plt.figure(figsize=(5,10))
    ax = fig.add_subplot(111)

    bar_width = 0.25
    pos = plt.barh(index, df['pos'], bar_width, alpha=0.7, align='center', color='green', label='Positive')
    nul = plt.barh(index + bar_width, df['nul'], bar_width, alpha=0.7, align='center', color='orange', label='None')
    neg = plt.barh(index + 2*bar_width, df['neg'], bar_width, alpha=0.7, align='center', color='red', label='Negative')

    plt.yticks(index + bar_width, df['type'], fontsize=9)
    plt.xticks(fontsize=7)
    plt.gca().set_xticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_xticks()])
    plt.subplots_adjust(left=left_padding, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=9)

    for l in df[::-1].iterrows():
        if float('{:.{}f}'.format(l[1]['p'], 3)) <= 0.000:
            p = '<0.001'
        else:
            p = '={:.{}f}'.format(l[1]['p'], 3)
        box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p

        ax.text(text_start, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=f_size)
        boxes_start -= delta

    plt.gca().xaxis.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig('{}/{}'.format(reports, 'maintainability_cwe.pdf'))

def merge_cache(cache_1_filename, cache_2_filename):
    cache_1 = readBCHCache(cache_1_filename)
    print('Length cache 1: {}'.format(len(cache_1.get_data())))
    
    cache_2 = readBCHCache(cache_2_filename)
    print('Length cache 2: {}'.format(len(cache_2.get_data())))
    
    cache = {**cache_1.get_data(), **cache_2.get_data()}
    cache_1.set_data(cache)
    return cache_1

        
    # cache = merge_cache('maintainability/bch_cache.json', 'maintainability/bch_cache_reg.json')
    # print('Length cache 1: {}'.format(len(cache.get_data())))
    # cache.save_data()
    # print(cache.storage_path)
    # analysis('../dataset/db_icpc20_release_reg_final.csv', '../dataset/maintainability_results_reg_icpc20.csv', cache)
    
    # df = pd.read_csv('../dataset/maintainability_results_sec_icpc20.csv')
    # print(len(df[df['CWE'].str.contains('CWE', na=False)]))
    # df_reg = pd.read_csv('../dataset/maintainability_results_reg_icpc20.csv')

def main_calculation(df, cache, dataset):
    
    none = 0; error = 0    

    if dataset == 'regular':
        sha_key = 'sha-reg'
        sha_p_key = 'sha-reg-p'
    else:
        sha_key = 'sha'
        sha_p_key = 'sha-p'
    
    for i, r in df.iterrows():

        if r[sha_key] is np.nan or r[sha_p_key] is np.nan:
            continue
            
        info_f = cache.get_stored_commit_analysis(r['owner'], r['project'], r[sha_key])
        info_p = cache.get_stored_commit_analysis(r['owner'], r['project'], r[sha_p_key])
            
        if info_f is None or info_p is None:
            none+=1
            df.at[i, 'diff'] = np.nan
            continue
            
        if info_f.get('error') or info_p.get('error'):
            error+=1
            df.at[i, 'diff'] = np.nan
            continue
        
        try:
            main_f = bch.compute_maintainability_score_per_guideline(info_f)
            main_p = bch.compute_maintainability_score_per_guideline(info_p)
            
            score_f = bch.compute_maintainability_score(info_f)
            score_p = bch.compute_maintainability_score(info_p)

            df.at[i, 'main_fix'] = score_f
            df.at[i, 'main_prev'] = score_p
            df.at[i, 'diff'] = score_f - score_p
            
            for k in main_f.keys():
                df.at[i, k+'-fix'] = main_f[k]
                df.at[i, k+'-prev'] = main_p[k]
                df.at[i, k+'-diff'] = main_f[k] - main_p[k]
                
        except ZeroDivisionError as e:
            df.at[i, 'diff'] = np.nan
            error+=1
    
    return df    
        
def main_calculation_by_db(db, results, cache, dataset):
    df = pd.read_csv(db)
    path = '{}/maintainability_release_{}_fixes.csv'.format(results, dataset)
    df = main_calculation(df, cache, dataset)
    return df, path

def export(secdb, regdb, results, cache_path):
    
    cache = bch.BCHCache(cache_path)
    
    df_sec, sec_res_path = main_calculation_by_db(secdb, results, cache, 'security')
    df_reg, reg_res_path = main_calculation_by_db(regdb, results, cache, 'regular')
    
    ids = df_reg[~df_reg['diff'].notnull()].index
    
    df_reg = df_reg.drop(ids) 
    df_sec = df_sec.drop(ids)
        
    df_sec.to_csv(sec_res_path, index=False)
    df_reg.to_csv(reg_res_path, index=False)
        
def language(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_per_language_chart(reports, df_sec)

def severity(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_per_severity(reports, df_sec)

def guideline(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_per_guideline_chart(reports, df_sec)

def comparison(secdb, regdb, reports):
    df_sec = pd.read_csv(secdb)
    df_reg = pd.read_csv(regdb)
    chart.main_comparison_chart(reports, df_sec, df_reg)
    
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Report results')    
    parser.add_argument('--report', dest='goal', choices=['export', 'comparison', 'severity', 'guideline', 'language', 'cwe'],
                        help='choose a report goal')
                        
    parser.add_argument('-results', type=str, metavar='folder path', help='results folder path')  
    parser.add_argument('-reports', type=str, metavar='folder path', help='reports folder path')      
    parser.add_argument('-secdb', type=str, metavar='file path', help='security dataset path')    
    parser.add_argument('-regdb', type=str, metavar='file path', help='regular dataset path')    
    parser.add_argument('-cache', type=str, metavar='file path', help='cache path')    
    
    args = parser.parse_args()
    print(args.goal)
    if args.goal == 'export':  
        if args.secdb != None and args.regdb != None and args.results != None and args.cache != None:
            export(secdb=args.secdb, regdb=args.regdb, results=args.results, cache_path=args.cache)
    elif args.goal == 'comparison':
        if args.secdb != None and args.regdb != None and args.reports != None:
            comparison(secdb=args.secdb, regdb=args.regdb, reports=args.reports)
    elif args.goal == 'guideline':
        if args.secdb != None and args.reports != None:
            guideline(secdb=args.secdb, reports=args.reports)
    elif args.goal == 'language':
        if args.secdb != None and args.reports != None:
            language(secdb=args.secdb, reports=args.reports)
    elif args.goal == 'severity':
        if args.secdb != None and args.reports != None:
            severity(secdb=args.secdb, reports=args.reports)
    else:
        print('Something is wrong. Verify your parameters')
