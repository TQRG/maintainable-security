import matplotlib.pyplot as plt
import pandas as pd

from scipy.stats import wilcoxon
import numpy as np

from . import enum
from . import tests
from . import data


_BAR_WIDTH = 0.25


def set_bars(df, idx):
    plt.barh(idx, df['pos'], _BAR_WIDTH, alpha=0.7, align='center', color='green', label='Positive')
    plt.barh(idx + _BAR_WIDTH, df['nul'], _BAR_WIDTH, alpha=0.7, align='center', color='orange', label='None')
    plt.barh(idx + 2*_BAR_WIDTH, df['neg'], _BAR_WIDTH, alpha=0.7, align='center', color='red', label='Negative')

def format_p_value(p):
    return '<0.001' if float('{:.{}f}'.format(p, 3)) <= 0.000 else '={:.{}f}'.format(p, 3)

def set_ticks(df, idx, fontsize=7):
    plt.yticks(idx + _BAR_WIDTH, df['type'], fontsize=fontsize)
    plt.xticks(fontsize=fontsize)
    plt.gca().set_xticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_xticks()])

def config_report(data, yaxs_size, x, y, plt_config):
    fig = plt.figure(figsize=(x,y))
    return pd.DataFrame(data), np.arange(yaxs_size), fig, fig.add_subplot(plt_config)

def save_report(path, name):
    plt.gca().xaxis.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig('{}/{}'.format(path, name))

# comparison chart
def main_comparison_chart(reports, df_sec, df_reg):    

        test = (tests.hypothesis_test(df_sec['diff']), tests.hypothesis_test(df_reg['diff']))
        total_sec, total_reg = data.filter_results(df_sec), data.filter_results(df_reg)
        
        db_size = len(df_sec)        

        d = {'neg' : pd.Series([total_reg['neg']/db_size, total_sec['neg']/db_size]),
            'pos' : pd.Series([total_reg['pos']/db_size, total_sec['pos']/db_size]),
            'nul' : pd.Series([total_reg['nul']/db_size, total_sec['nul']/db_size]),
            'type' : pd.Series(['Regular Change','Security Change'])}
        
        df, idx, fig, ax = config_report(d, len(d['type']), 7, 6, 111)
        
        set_bars(df, idx)
        set_ticks(df, idx, 9)
        
        plt.subplots_adjust(left=0.2, right=0.85, top=0.9, bottom=0.1)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), fancybox=True, ncol=3, fontsize=9)

        y = 1.2
        for l in test:
            p = format_p_value(l['pvalue'][0])
            box_text = '$\overline{x}$='+ '{:.{}f}'.format(l['mean'][0], 2) + '\nM=' + '{:.{}f}'.format(l['med'][0], 2) + '\np' + p
            ax.text(0.43, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':4}, fontsize=9)
            y -= 1.1
        
        save_report(reports, 'main_comparison.pdf')

def main_per_guideline_chart(reports, df, wilcoxon = True):
    
    results = {g:data.filter_results_per_guideline(df, g) for g in enum.guidelines}
    keys = results.keys() 
    test_g = [tests.hypothesis_test(df[i+'-diff']) for i in keys]
    
    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in keys]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in keys]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in keys]),
        'N': pd.Series([sum(results[i]) for i in keys if wilcoxon]),
        'mean': pd.Series([i['mean'][0] for i in test_g if wilcoxon]),
        'med': pd.Series([i['med'][0] for i in test_g if wilcoxon]),
        'p': pd.Series([i['pvalue'][0] for i in test_g if wilcoxon]),
        'type': pd.Series([enum.guidelines[i] for i in keys])}
        
        
    df, idx, fig, ax = config_report(d, len(d['type']), 5, 7, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 7)
    
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=7)
    
    if wilcoxon:
        boxes_start = 7
        for l in df[::-1].iterrows():    
            p = format_p_value(l[1]['p'])
            box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
            ax.text(0.57, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=7)
            boxes_start -= 1
    
    save_report(reports, 'main_per_guideline.pdf')

def main_per_language_chart(reports, df, wilcoxon=True):
    
    for i, r in df.iterrows():
        lang = enum.get_language(r['Language'])
        if lang != None:
            df.at[i, 'Language'] = lang
    
    langs = tests.filter_small_sample_groups(df, 'Language')
    langs = data.add_others_group(df, langs, 'Language')
        
    results = {l:data.filter_results_per_field(df, l, 'Language') for l in langs}
    test_lang = [tests.hypothesis_test(df[df['Language'] == i]['diff']) for i in langs]
    
    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in langs]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in langs]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in langs]),
        'N': pd.Series([sum(results[i]) for i in langs if wilcoxon]),
        'mean': pd.Series([i['mean'][0] for i in test_lang if wilcoxon]),
        'med': pd.Series([i['med'][0] for i in test_lang if wilcoxon]),
        'p': pd.Series([i['pvalue'][0] for i in test_lang if wilcoxon]),
        'type': pd.Series([i for i in langs])}
    
    df, idx, fig, ax = config_report(d, len(d['type']), 6, 8, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 7)    
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=8)

    boxes_start = 6
    for l in df[::-1].iterrows():
        p = format_p_value(l[1]['p'])
        box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.67, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=8)
        boxes_start -= 1
        
    save_report(reports, 'main_per_language.pdf') 

def main_per_severity(reports, df, wilcoxon = True):
    
    y_axis = data.add_others_group(df, enum.severity, 'Severity')
    
    results = {s:data.filter_results_per_field(df, s, 'Severity') for s in y_axis}        
    test_sev = [tests.hypothesis_test(df[df['Severity'] == i]['diff']) for i in y_axis]
        
    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in y_axis]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in y_axis]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in y_axis]),
        'N': pd.Series([sum(results[i]) for i in y_axis if wilcoxon]),
        'mean': pd.Series([i['mean'][0] for i in test_sev if wilcoxon]),
        'med': pd.Series([i['med'][0] for i in test_sev if wilcoxon]),
        'p': pd.Series([i['pvalue'][0] for i in test_sev if wilcoxon]),
        'type': pd.Series([i for i in y_axis])}

    df, idx, fig, ax = config_report(d, len(d['type']), 6, 6, 111)
    
    set_bars(df, idx)
    
    set_ticks(df, idx, 7)
    plt.subplots_adjust(left=0.05, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), fancybox=True, ncol=3, fontsize=7)
    
    boxes_start = 3
    for l in df[::-1].iterrows():
        p = format_p_value(l[1]['p'])
        box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=8)
        boxes_start -= 1
        
    save_report(reports, 'main_per_severity.pdf')

