import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib import rcParams

import pandas as pd


from scipy.stats import wilcoxon
import numpy as np

from . import enum
from . import tests
from . import data

rc('text', usetex=True)
rcParams['font.family'] = 'serif'
rcParams['mathtext.fontset'] = 'cm'

BAR_WIDTH = 0.25

def set_bars(df, idx):
    plt.barh(idx, df['pos'], BAR_WIDTH, alpha=0.7, align='center', color='green', label='Positive')
    plt.barh(idx + BAR_WIDTH, df['nul'], BAR_WIDTH, alpha=0.7, align='center', color='orange', label='None')
    plt.barh(idx + 2*BAR_WIDTH, df['neg'], BAR_WIDTH, alpha=0.7, align='center', color='red', label='Negative')

def format_p_value(p):
    return '$<$0.001' if float('{:.{}f}'.format(p, 3)) <= 0.000 else '={:.{}f}'.format(p, 3)

def set_ticks(df, idx, fontsize=7):
    plt.yticks(idx + BAR_WIDTH, df['type'], fontsize=fontsize)
    plt.xticks(fontsize=fontsize)
    plt.gca().set_xticklabels(['{:.0f}$\%$'.format(x*100) for x in plt.gca().get_xticks()])

def config_report(data, yaxs_size, x, y, plt_config):
    fig = plt.figure(figsize=(x,y))
    return pd.DataFrame(data), np.arange(yaxs_size), fig, fig.add_subplot(plt_config)

def save_report(path, name):
    plt.gca().xaxis.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig('{}/{}'.format(path, name))

def main_comparison_chart(reports, df_sec, df_reg):    

        test = pd.concat((tests.hypothesis_test(df_reg['diff'], 'reg'), 
                            tests.hypothesis_test(df_sec['diff'], 'sec')),
                            ignore_index=True)
                        
        total_sec, total_reg = data.filter_results(df_sec), data.filter_results(df_reg)        
        db_size = len(df_sec)  

        rep = {'neg' : pd.Series([total_reg['neg']/db_size, total_sec['neg']/db_size]),
                'neg_abs' : pd.Series([total_reg['neg'], total_sec['neg']]),
                'pos' : pd.Series([total_reg['pos']/db_size, total_sec['pos']/db_size]),
                'pos_abs' : pd.Series([total_reg['pos'], total_sec['pos']]),
                'nul' : pd.Series([total_reg['nul']/db_size, total_sec['nul']/db_size]),
                'nul_abs' : pd.Series([total_reg['nul'], total_sec['nul']]),
                'type' : pd.Series(['Regular Change','Security Change'])}
        
        df, idx, fig, ax = config_report(rep, len(rep['type']), 7, 6, 111)
        
        set_bars(df, idx)
        set_ticks(df, idx, 9) 
        
        plt.subplots_adjust(left=0.2, right=0.85, top=0.9, bottom=0.1)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07), fancybox=True, ncol=3, fontsize=8)

        y = 1.2
        for i, r in test[::-1].iterrows():
            p = format_p_value(r['pvalue'])
            box_text = '$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
            ax.text(0.4, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':4}, fontsize=10)
            y -= 1.1
        
        save_report(reports, 'main_comparison.pdf')
        test.join(df).to_csv(reports+'/comparison_stats_report.csv', index=False)

def main_per_cwe_spec_chart(reports, cwe, df, wilcoxon = True):
    
    composites = enum.read_cwe_composites('stats/{}'.format(cwe))
    
    for i, r in df.iterrows():
        if not enum.check_if_belongs_to_cwe(composites, r['CWE']):
            df = df.drop(i)

    cwes = data.add_others_group(df, tests.filter_small_cwe_groups(df), 'CWE', 'MISC')
    results = {c:data.filter_results_per_field(df, c, 'CWE') for c in cwes}
    test = pd.concat([tests.hypothesis_test(df[df['CWE'] == c]['diff'], c) for c in cwes], ignore_index=True)
    
    rep = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in cwes]),
        'neg_abs': pd.Series([results[i][0] for i in cwes]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in cwes]),
        'pos_abs': pd.Series([results[i][1] for i in cwes]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in cwes]),
        'nul_abs': pd.Series([results[i][2] for i in cwes]),
        'N': pd.Series([sum(results[i]) for i in cwes]),
        'type': pd.Series(cwes)}

    df, idx, fig, ax = config_report(rep, len(rep['type']), 5, 8, 111)

    set_bars(df, idx)
    set_ticks(df, idx, 9)
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=8)
    
    if wilcoxon:
        boxes_start=len(idx)-1
        for i, r in test.join(df)[::-1].iterrows():
            p = format_p_value(r['pvalue'])
            box_text = 'N='+str(sum([r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
            ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
            boxes_start -= 1.0 

    save_report(reports, 'main_per_cwe_spec.pdf')
    test.join(df).to_csv(reports+'/cwe_spec_test_report.csv', index=False)
    
def main_per_cwe_chart(reports, df, wilcoxon = True):
    
    composites = enum.read_cwe_composites('stats/CWE')
    
    for i, r in df.iterrows():
        if r['CWE'] is not np.nan:
            cwe = enum.check_if_belongs_to_cwe(composites, r['CWE'])
            if cwe != None:
                df.at[i, 'CWE'] = cwe
        else:
            df.at[i, 'CWE'] = 'MISC'
    
    cwes = data.add_others_group(df, tests.filter_small_cwe_groups(df), 'CWE', 'MISC') 
    results = {c:data.filter_results_per_field(df, c, 'CWE') for c in cwes}          
    test = pd.concat([tests.hypothesis_test(df[df['CWE'] == c]['diff'], c) for c in cwes], ignore_index=True)
        
    rep = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in cwes]),
        'neg_abs': pd.Series([results[i][0] for i in cwes]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in cwes]),
        'pos_abs': pd.Series([results[i][1] for i in cwes]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in cwes]),
        'nul_abs': pd.Series([results[i][2] for i in cwes]),
        'N': pd.Series([sum(results[i]) for i in cwes]),
        'type': pd.Series(cwes)}

    df, idx, fig, ax = config_report(rep, len(rep['type']), 5, 8, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 9)
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=8)

    boxes_start=6
    for i, r in test.join(df)[::-1].iterrows():
        p = format_p_value(r['pvalue'])
        box_text = 'N='+str(sum([r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
        ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
        boxes_start -= 1
    
    save_report(reports, 'main_per_cwe.pdf')
    test.join(df).to_csv(reports+'/cwe_test_report.csv', index=False)

def main_per_guideline_chart(reports, df, wilcoxon = True):
    
    results = {g:data.filter_results_per_guideline(df, g) 
                for g in enum.guidelines}    
    
    keys = results.keys() 
    
    test = pd.concat([tests.hypothesis_test(df[i+'-diff'], i) 
                            for i in keys],
                            ignore_index=True)
    
    rep = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in keys]),
        'neg_abs': pd.Series([results[i][0] for i in keys]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in keys]),
        'pos_abs': pd.Series([results[i][1] for i in keys]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in keys]),
        'nul_abs': pd.Series([results[i][2] for i in keys]),
        'N': pd.Series([sum(results[i]) for i in keys]),
        'type': pd.Series([enum.guidelines[i] for i in keys])}
        
    df, idx, fig, ax = config_report(rep, len(rep['type']), 5, 7, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 9)
    
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, ncol=3, fontsize=8)
    
    if wilcoxon:
        boxes_start = 7
        for i, r in test.join(df)[::-1].iterrows():    
            p = format_p_value(r['pvalue'])
            box_text = 'N='+str(sum([r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
            ax.text(0.56, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=8)
            boxes_start -= 1
    
    save_report(reports, 'main_per_guideline.pdf')
    test.join(df).to_csv(reports+'/guidelines_test_report.csv', index=False)

def main_per_language_chart(reports, df, wilcoxon = True):
    
    for i, r in df.iterrows():
        lang = enum.get_language(r['Language'])
        if lang != None:
            df.at[i, 'Language'] = lang
    
    langs = data.add_others_group(df,
                                tests.filter_small_sample_groups(df, 'Language'), 
                                'Language', 
                                'Other')
        
    results = {l:data.filter_results_per_field(df, l, 'Language') for l in langs}
    test = pd.concat([tests.hypothesis_test(df[df['Language'] == i]['diff'], i) 
                            for i in langs],
                            ignore_index=True)
                                
    rep = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in langs]),
        'neg_abs': pd.Series([results[i][0] for i in langs]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in langs]),
        'pos_abs': pd.Series([results[i][1] for i in langs]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in langs]),
        'nul_abs': pd.Series([results[i][2] for i in langs]),
        'N': pd.Series([sum(results[i]) for i in langs]),
        'type': pd.Series(langs)}
    
    df, idx, fig, ax = config_report(rep, len(rep['type']), 6, 8, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 9)    
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=8)
    
    boxes_start = 6
    for i, r in test.join(df)[::-1].iterrows():
        p = format_p_value(r['pvalue'])
        box_text = 'N='+str(sum([r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
        ax.text(0.67, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
        boxes_start -= 1
        
    save_report(reports, 'main_per_language.pdf') 
    test.join(df).to_csv(reports+'/language_test_report.csv', index=False)
    
def main_per_severity(reports, df, wilcoxon = True):
    
    y_axis = data.add_others_group(df, enum.severity, 'Severity', 'UNKNOWN')
    
    results = {s:data.filter_results_per_field(df, s, 'Severity') for s in y_axis}        
    test = pd.concat([tests.hypothesis_test(df[df['Severity'] == i]['diff'], i) for i in y_axis], ignore_index=True)
        
    rep = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in y_axis]),
        'neg_abs': pd.Series([results[i][0] for i in y_axis]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in y_axis]),
        'pos_abs': pd.Series([results[i][1] for i in y_axis]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in y_axis]),
        'nul_abs': pd.Series([results[i][2] for i in y_axis]),
        'N': pd.Series([sum(results[i]) for i in y_axis]),
        'type': pd.Series(y_axis)}

    df, idx, fig, ax = config_report(rep, len(rep['type']), 6, 6, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 9)
    
    plt.subplots_adjust(left=0.05, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), fancybox=True, ncol=3, fontsize=8)
    
    boxes_start = 3
    for i, r in test.join(df)[::-1].iterrows():
        p = format_p_value(r['pvalue'])
        box_text = 'N='+str(sum([r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
        ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
        boxes_start -= 1
        
    save_report(reports, 'main_per_severity.pdf')
    test.join(df).to_csv(reports+'/severity_test_report.csv', index=False)
    
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


