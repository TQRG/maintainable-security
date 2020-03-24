import maintainability.better_code_hub as bch
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
from scipy.stats import wilcoxon, shapiro
from statistics import mean, stdev
from math import sqrt
import pandas as pd
from collections import OrderedDict

# 'Keep Your Codebase Small',

guidelines = {'Write Short Units of Code':'WShortUC', 'Write Simple Units of Code':'WSimpleUC', 'Write Code Once':'WCO', 'Keep Unit Interfaces Small':'KUIS', 'Separate Concerns in Modules':'SCM',
                'Couple Architecture Components Loosely':'CACL', 'Keep Architecture Components Balanced':'KACB', 'Write Clean Code':'WCC'}

def readBCHCache(path):
    return bch.BCHCache(path)
    
def analysis(database, results, CACHE):
    
    none = 0; error = 0
            
    df = pd.read_csv(database)
    
    for i, r in df.iterrows():

        if r['sha-reg'] is np.nan or r['sha-reg-p'] is np.nan:
            continue
            
        info_f = CACHE.get_stored_commit_analysis(r['owner'], r['project'], r['sha-reg'])
        info_p = CACHE.get_stored_commit_analysis(r['owner'], r['project'], r['sha-reg-p'])
            
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
        
    df.to_csv(results, index=False)

def export_results_csv(database, filename, cache):
    analysis(database, filename, readBCHCache(cache))
    
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
    
def report_maintainability_per_guideline(reports, df, wilcoxon = True, boxes_start=7, text_start=0.62, delta=1, left_padding=0.25, f_size=9):
    
    results = {}
    
    for g in guidelines:
        impact = [0, 0, 0]
        impact[0] = df[df[g+'-diff'] < 0].shape[0]
        impact[1] = df[df[g+'-diff'] > 0].shape[0]
        impact[2] = df[df[g+'-diff'] == 0].shape[0]
        results[g] = impact 
    
    keys = results.keys()
    print('results_per_guideline', results)
        
    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in keys]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in keys]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in keys]),
        'N': pd.Series([sum(results[i]) for i in keys if wilcoxon]),
        'test': pd.Series([_print_hypothesis_test(df[i+'-diff'])['test'][0] for i in keys if wilcoxon]),
        
        'mean': pd.Series([_print_hypothesis_test(df[i+'-diff'])['mean'][0] for i in keys if wilcoxon]),
        'med': pd.Series([_print_hypothesis_test(df[i+'-diff'])['med'][0] for i in keys if wilcoxon]),
        'p': pd.Series([_print_hypothesis_test(df[i+'-diff'])['pvalue'][0] for i in keys if wilcoxon]),
        'type': pd.Series([guidelines[i] for i in keys])}
    print(d)
    absoluto = {'neg': pd.Series([results[i][0] for i in keys]),
        'pos': pd.Series([results[i][1] for i in keys]),
        'nul': pd.Series([results[i][2] for i in keys]),
        'type': pd.Series([guidelines[i] for i in keys]),
        'p': pd.Series([_print_hypothesis_test(df[i+'-diff'])['pvalue'][0] for i in keys if wilcoxon])}

    df = pd.DataFrame(d)
    abso = pd.DataFrame(absoluto)
    print(d['type'])
    index = np.arange(len(d['type']))

    fig = plt.figure(figsize=(8,9))
    ax = fig.add_subplot(111)

    bar_width = 0.25
    pos = plt.barh(index, df['pos'], bar_width, alpha=0.7, align='center', color='green', label='Positive')
    nul = plt.barh(index + bar_width, df['nul'], bar_width, alpha=0.7, align='center', color='orange', label='None')
    neg = plt.barh(index + 2*bar_width, df['neg'], bar_width, alpha=0.7, align='center', color='red', label='Negative')

    plt.yticks(index + bar_width, df['type'], fontsize=6.5)
    plt.xticks(fontsize=7)
    plt.gca().set_xticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_xticks()])
    plt.subplots_adjust(left=left_padding, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=7)
    
    if wilcoxon:
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
    plt.savefig('{}/{}'.format(reports, 'maintainability_per_guideline.pdf'))

def report_maintainability_sec_vs_reg(reports, df_sec, df_reg):    

        stats1 = _print_hypothesis_test(df_sec['diff'])
        stats = _print_hypothesis_test(df_reg['diff'])
    
        result = stats.append([stats1])
        print(result)
    
        total_sec, total_reg = {'neg': 0, 'pos': 0, 'nul': 0}, {'neg': 0, 'pos': 0, 'nul': 0}
    
        total_sec['neg'] = df_sec[df_sec['diff'] < 0].shape[0]
        total_sec['pos'] = df_sec[df_sec['diff'] > 0].shape[0]
        total_sec['nul'] = df_sec[df_sec['diff'] == 0].shape[0]
        print('security_patches', total_sec)
        
        total_reg['neg'] = df_reg[df_reg['diff'] < 0].shape[0]
        total_reg['pos'] = df_reg[df_reg['diff'] > 0].shape[0]
        total_reg['nul'] = df_reg[df_reg['diff'] == 0].shape[0]
        print('reg_patches',total_reg)
        
    
        sec = sum([value for key,value in total_sec.items()])
        reg = sum([value for key,value in total_reg.items()])
    
        d = {'neg' : pd.Series([total_reg['neg']/reg, total_sec['neg']/sec]),
        'pos' : pd.Series([total_reg['pos']/reg, total_sec['pos']/sec]),
        'none' : pd.Series([total_reg['nul']/reg, total_sec['nul']/sec]),
        'type' : pd.Series(['Regular Change','Security Change'])}
    
        index = np.arange(len(d['type']))
        print(len(d['type']))
    
        df = pd.DataFrame(d)
    
        fig = plt.figure()
        ax = fig.add_subplot(111)
    
        bar_width = 0.25
        pos = plt.barh(index, df['pos'], bar_width, alpha=0.7, align='center', color='green', label='Positive')
        nul = plt.barh(index + bar_width, df['none'], bar_width, alpha=0.7, align='center', color='orange', label='None')
        neg = plt.barh(index + 2 * bar_width, df['neg'], bar_width, alpha=0.7, align='center', color='red', label='Negative')
    
        plt.yticks(index + bar_width, df['type'], fontsize=9)
        plt.gca().set_xticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_xticks()]) 
        plt.subplots_adjust(left=0.2, right=0.85, top=0.9, bottom=0.1)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), fancybox=True, ncol=3, fontsize=9)

        y = 1.3
        for l in result[::-1].iterrows():
            if float('{:.{}f}'.format(l[1]['pvalue'], 3)) <= 0.000:
                p = '<0.001'
            else:
                p = '={:.{}f}'.format(l[1]['pvalue'], 3)
            box_text = '$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
            ax.text(0.49, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':4}, fontsize=9)
            y -= 1.1
    
        plt.gca().xaxis.grid(True, linestyle='--')
    
        plt.tight_layout()
        plt.savefig('{}/maintainability_general.pdf'.format(reports))
 

def report_maintainability_severity(reports, df, wilcoxon = True, boxes_start=3, text_start=0.55, delta=1, left_padding=0.05, f_size=7.5):
    
    results = {};
    severity = ['LOW', 'MEDIUM', 'HIGH']
    
    for i, r in df.iterrows():
        if r['Severity'] not in severity:
            df.at[i, 'Severity'] = 'Other'
    severity = ['Other'] + severity
    
    for s in severity:
        impact = [0, 0, 0]
        impact[0] = df[(df['diff'] < 0) & (df['Severity'] == s)].shape[0]
        impact[1] = df[(df['diff'] > 0) & (df['Severity'] == s)].shape[0]
        impact[2] = df[(df['diff'] == 0) & (df['Severity'] == s)].shape[0]
        results[s] = impact 
    
    print('severity results', results)
    
    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in severity]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in severity]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in severity]),
        'N': pd.Series([sum(results[i]) for i in severity if wilcoxon]),
        'mean': pd.Series([_print_hypothesis_test(df[df['Severity'] == i]['diff'])['mean'][0] for i in severity if wilcoxon]),
        'med': pd.Series([_print_hypothesis_test(df[df['Severity'] == i]['diff'])['med'][0] for i in severity if wilcoxon]),
        'p': pd.Series([_print_hypothesis_test(df[df['Severity'] == i]['diff'])['pvalue'][0] for i in severity if wilcoxon]),
        'type': pd.Series([i for i in severity])}

    
    absoluto = {'neg': pd.Series([results[i][0] for i in severity]),
        'pos': pd.Series([results[i][1] for i in severity]),
        'nul': pd.Series([results[i][2] for i in severity]),
        'type': pd.Series([i for i in severity]),
        'p': pd.Series([_print_hypothesis_test(df[df['Severity'] == i]['diff'])['pvalue'][0] for i in severity if wilcoxon])}

    df = pd.DataFrame(d)
    abso = pd.DataFrame(absoluto)
    index = np.arange(len(d['type']))

    fig = plt.figure()
    ax = fig.add_subplot(111)

    bar_width = 0.25
    pos = plt.barh(index, df['pos'], bar_width, alpha=0.7, align='center', color='green', label='Positive')
    nul = plt.barh(index + bar_width, df['nul'], bar_width, alpha=0.7, align='center', color='orange', label='None')
    neg = plt.barh(index + 2*bar_width, df['neg'], bar_width, alpha=0.7, align='center', color='red', label='Negative')

    plt.yticks(index + bar_width, df['type'], fontsize=6.5)
    plt.xticks(fontsize=7)
    plt.gca().set_xticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_xticks()])
    plt.subplots_adjust(left=left_padding, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), fancybox=True, ncol=3, fontsize=7)
    
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
    plt.savefig('{}/{}'.format(reports, 'maintainability_severity.pdf'))

def _print_hypothesis_test(differences):
    """Paired Wilcoxon signed-rank test (N should be > 20)"""
    _, pvalue = shapiro(differences)
    #print("Shapiro-Wilk test for normality: {}".format(pvalue))
    test, pvalue = _hypothesis_test(differences)
    stats = {'test': [test], 'med':[pd.DataFrame({'diff': differences})['diff'].median()],'pvalue': [pvalue], 
                'mean':[pd.DataFrame({'diff': differences})['diff'].mean()]}
    df = pd.DataFrame(stats)
    #print("Wilcoxon signed-rank test {}, p-value: {}".format(test,pvalue))
    return df

def _hypothesis_test(differences):
    return wilcoxon(x=differences, zero_method="pratt")

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

def get_language(key):
    language_map = {'Java': ['java', 'scala'], 'Python': ['py'], 'Groovy': ['groovy'], 'JavaScript': ['js'] , 'PHP': ['ctp', 'php', 'inc', 'tpl'], 'Objective-C/C++': ['m', 'mm'], 'Ruby': ['rb'], 'C/C++': ['cpp', 'cc', 'h', 'c'], 'Config. Files': ['template', 'gemspec', 'VERSION', 'Gemfile', 'classpath', 'gradle', 'json', 'xml', 'bash', 'lock']}
    for k, v in language_map.items():
        if key in language_map[k]:
            return k
    return None

def report_maintainability_lang(reports, df, wilcoxon=True, boxes_start=6, text_start=0.67, delta=1, left_padding=0.25, f_size=9):
                
    for i, r in df.iterrows():
        lang = get_language(r['Language'])
        if lang != None:
            df.at[i, 'Language'] = lang
        
    langs = [i for i in df['Language'].unique() if len(df[df['Language'] == i]) > 19]
    
    for i, r in df.iterrows():
        if r['Language'] not in langs:
            df.at[i, 'Language'] = 'Others'
            
    langs = ['Others'] + langs   
    results = {}
    for s in langs:
        impact = [0, 0, 0]
        impact[0] = df[(df['diff'] < 0) & (df['Language'] == s)].shape[0]
        impact[1] = df[(df['diff'] > 0) & (df['Language'] == s)].shape[0]
        impact[2] = df[(df['diff'] == 0) & (df['Language'] == s)].shape[0]
        results[s] = impact

    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in langs]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in langs]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in langs]),
        'N': pd.Series([sum(results[i]) for i in langs if wilcoxon]),
        'test': pd.Series([_print_hypothesis_test(df[df['Language'] == i]['diff'])['test'][0] for i in langs if wilcoxon]),
        'mean': pd.Series([_print_hypothesis_test(df[df['Language'] == i]['diff'])['mean'][0] for i in langs if wilcoxon]),
        'med': pd.Series([_print_hypothesis_test(df[df['Language'] == i]['diff'])['med'][0] for i in langs if wilcoxon]),
        'p': pd.Series([_print_hypothesis_test(df[df['Language'] == i]['diff'])['pvalue'][0] for i in langs if wilcoxon]),
        'type': pd.Series([i for i in langs])}

    absoluto = {'neg': pd.Series([results[i][0] for i in langs]),
        'pos': pd.Series([results[i][1] for i in langs]),
        'nul': pd.Series([results[i][2] for i in langs]),
        'type': pd.Series([i for i in langs]),
        'p': pd.Series([_print_hypothesis_test(df[df['Language'] == i]['diff'])['pvalue'][0] for i in langs if wilcoxon])}

    df = pd.DataFrame(d)
    print(d)
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
    plt.savefig('{}/{}'.format(reports, 'maintainability_language.pdf'))

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

def main(cache, filename, reports, database):
    
    
    # df1 = pd.read_csv('../dataset/db_icpc20_release_reg_tmp_1.csv')
    # df2 = pd.read_csv('../dataset/db_icpc20_release_reg_tmp_2.csv')
    #
    # df = df2.loc[(df2['sha'] == 'd4184aa26cfa4e99b6e36502aee7f685e122facc') & (df2['owner'] == 'realm')]
    # df2 = df2.drop([df.index[0]], axis=0)
    #
    # df3 = df1.append(df2)
    #
    # df3.to_csv('../dataset/db_icpc20_release_reg_final_jan_31.csv', index=False)
    
    # sec vs reg - delete d4184aa26cfa4e99b6e36502aee7f685e122facc realm-cocoa dup
    # df_reg = pd.read_csv('../dataset/db_icpc20_release_reg_final.csv')
    # df_sec = pd.read_csv('../dataset/maintainability_results_sec_icpc20.csv')
    #
    # for i, r in df_reg.iterrows():
    #     df = df_sec.loc[(r['sha'] == df_sec['sha']) & (r['sha-p'] == df_sec['sha-p']) & (r['owner'] == df_sec['owner']) & (r['project'] == df_sec['project'])]
    #     if len(df) < 1:
    #         print(r)
    
    
    # cache = readBCHCache('maintainability/bch_cache.json')
    # print(len(cache.get_data()))
    
    # cache = merge_cache('maintainability/bch_cache.json', 'maintainability/bch_cache_reg.json')
    # print('Length cache 1: {}'.format(len(cache.get_data())))
    # cache.save_data()
    # print(cache.storage_path)
    # analysis('../dataset/db_icpc20_release_reg_final.csv', '../dataset/maintainability_results_reg_icpc20.csv', cache)
    
    # df = pd.read_csv('../dataset/maintainability_results_sec_icpc20.csv')
    # print(len(df[df['CWE'].str.contains('CWE', na=False)]))
    # df_reg = pd.read_csv('../dataset/maintainability_results_reg_icpc20.csv')
    
    #export_results_csv(database, filename, cache)
    
    # print('results: {} fixes'.format(len(df)))
#
    # report_maintainability_cwe(reports, df)
    # report_maintainability_severity(reports, df)
    # report_maintainability_lang(reports, df)

    # report_maintainability_per_guideline(reports, df)
    # report_maintainability_sec_vs_reg(reports, df, df_reg)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--bch-cache',metavar='bch-cache',required=True,help='the bch cache filename')
    parser.add_argument('--results-filename',metavar='results',required=True,help='the filename to save the maintainability results')
    parser.add_argument('--reports',metavar='reports',required=True,help='the reports path')   
    parser.add_argument('--database',metavar='database',required=True,help='the database path')    
     

    args = parser.parse_args()
    main(cache=args.bch_cache, filename=args.results_filename, reports=args.reports, database=args.database)