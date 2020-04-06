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


guidelines = {'Write Short Units of Code':'WShortUC', 'Write Simple Units of Code':'WSimpleUC', 'Write Code Once':'WCO', 'Keep Unit Interfaces Small':'KUIS', 'Separate Concerns in Modules':'SCM',
                'Couple Architecture Components Loosely':'CACL', 'Keep Architecture Components Balanced':'KACB', 'Write Clean Code':'WCC'}

def readBCHCache(path):
    return bch.BCHCache(path)
    
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

def hypothesis_test(differences):
    """Paired Wilcoxon signed-rank test (N should be > 20)"""
    _, pvalue = shapiro(differences)
    test, pvalue = _hypothesis_test(differences)
    stats = {'test': [test], 'med':[pd.DataFrame({'diff': differences})['diff'].median()],'pvalue': [pvalue], 
                'mean':[pd.DataFrame({'diff': differences})['diff'].mean()]}
    df = pd.DataFrame(stats)
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
    
def main_calculation_by_db(db, results, cache, dataset):
    df = pd.read_csv(db)
    path = '{}/maintainability_release_{}_fixes.csv'.format(results, dataset)
    assert len(df) == 1037
    df = main_calculation(df, cache, dataset)
    return df, path

def export(secdb, regdb, results, cache):
    
    cache = readBCHCache(cache)
    
    df_sec, sec_res_path = main_calculation_by_db(secdb, results, cache, 'security')
    df_reg, reg_res_path = main_calculation_by_db(regdb, results, cache, 'regular')
    
    ids = df_reg[~df_reg['diff'].notnull()].index
    
    for i in ids:
        df_reg = df_reg.drop(i)
        df_sec = df_sec.drop(i)
        
    assert len(df_reg) == 1027
    df_sec.to_csv(sec_res_path, index=False)
    
    assert len(df_sec) == 1027
    df_reg.to_csv(reg_res_path, index=False)

def init_res():
    return {'neg': 0, 'pos': 0, 'nul': 0}

def filter_results(df):
    df_res = init_res()
    df_res['neg'] = df[df['diff'] < 0].shape[0]
    df_res['pos'] = df[df['diff'] > 0].shape[0]
    df_res['nul'] = df[df['diff'] == 0].shape[0]
    return df_res

def main_comparison_chart(reports, df_sec, df_reg):    

        result = (hypothesis_test(df_sec['diff']), hypothesis_test(df_reg['diff']))

        total_sec = filter_results(df_sec)
        total_reg = filter_results(df_reg)

        sec = sum([value for key,value in total_sec.items()])
        reg = sum([value for key,value in total_reg.items()])

        d = {'neg' : pd.Series([total_reg['neg']/reg, total_sec['neg']/sec]),
            'pos' : pd.Series([total_reg['pos']/reg, total_sec['pos']/sec]),
            'none' : pd.Series([total_reg['nul']/reg, total_sec['nul']/sec]),
            'type' : pd.Series(['Regular Change','Security Change'])}

        index = np.arange(len(d['type']))
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

        y = 1.2
        for l in result:
            if float('{:.{}f}'.format(l['pvalue'][0], 3)) <= 0.000:
                p = '<0.001'
            else:
                p = '={:.{}f}'.format(l['pvalue'][0], 3)
            
            box_text = '$\overline{x}$='+ '{:.{}f}'.format(l['mean'][0], 2) + '\nM=' + '{:.{}f}'.format(l['med'][0], 2) + '\np' + p
            ax.text(0.43, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':4}, fontsize=9)
            y -= 1.1

        plt.gca().xaxis.grid(True, linestyle='--')

        plt.tight_layout()
        plt.savefig('{}/main_comparison.pdf'.format(reports))

def comparison(secdb, regdb, reports):
    
    df_sec = pd.read_csv(secdb)
    assert len(df_sec) == 1027
    
    df_reg = pd.read_csv(regdb)
    assert len(df_reg) == 1027
        
    main_comparison_chart(reports, df_sec, df_reg)

def main_per_guideline_chart(reports, df, wilcoxon = True, boxes_start=7, text_start=0.62, delta=1, left_padding=0.25, f_size=9):
    
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

def guideline(secdb, reports):
    
    df_sec = pd.read_csv(secdb)
    assert len(df_sec) == 1027
    
    guideline_chart()

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
            export(secdb=args.secdb, regdb=args.regdb, results=args.results, cache=args.cache)
    elif args.goal == 'comparison':
        if args.secdb != None and args.regdb != None and args.reports != None:
            comparison(secdb=args.secdb, regdb=args.regdb, reports=args.reports)
    elif args.goal == 'guideline':
        if args.secdb != None and args.report != None:
            guideline(secdb=args.secdb, reports=args.reports)
    else:
        print('Something is wrong. Verify your parameters')
