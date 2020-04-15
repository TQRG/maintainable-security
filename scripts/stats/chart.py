import matplotlib.pyplot as plt
import pandas as pd

from scipy.stats import wilcoxon
import numpy as np

from . import enum
from . import tests
from . import data


BAR_WIDTH = 0.25

def set_bars(df, idx):
    plt.barh(idx, df['pos'], BAR_WIDTH, alpha=0.7, align='center', color='green', label='Positive')
    plt.barh(idx + BAR_WIDTH, df['nul'], BAR_WIDTH, alpha=0.7, align='center', color='orange', label='None')
    plt.barh(idx + 2*BAR_WIDTH, df['neg'], BAR_WIDTH, alpha=0.7, align='center', color='red', label='Negative')

def format_p_value(p):
    return '<0.001' if float('{:.{}f}'.format(p, 3)) <= 0.000 else '={:.{}f}'.format(p, 3)

def set_ticks(df, idx, fontsize=7):
    plt.yticks(idx + BAR_WIDTH, df['type'], fontsize=fontsize)
    plt.xticks(fontsize=fontsize)
    plt.gca().set_xticklabels(['{:.0f}%'.format(x*100) for x in plt.gca().get_xticks()])

def config_report(data, yaxs_size, x, y, plt_config):
    fig = plt.figure(figsize=(x,y))
    return pd.DataFrame(data), np.arange(yaxs_size), fig, fig.add_subplot(plt_config)

def save_report(path, name):
    plt.gca().xaxis.grid(True, linestyle='--')
    plt.tight_layout()
    plt.savefig('{}/{}'.format(path, name))

def main_comparison_chart(reports, df_sec, df_reg):    

        test = (tests.hypothesis_test(df_sec['diff']), tests.hypothesis_test(df_reg['diff']))
        print(test)
        total_sec, total_reg = data.filter_results(df_sec), data.filter_results(df_reg)
        print(total_sec)
        print(total_reg)
        
        db_size = len(df_sec)        

        d = {'neg' : pd.Series([total_reg['neg']/db_size, total_sec['neg']/db_size]),
            'pos' : pd.Series([total_reg['pos']/db_size, total_sec['pos']/db_size]),
            'nul' : pd.Series([total_reg['nul']/db_size, total_sec['nul']/db_size]),
            'type' : pd.Series(['Regular Change','Security Change'])}
        
        df, idx, fig, ax = config_report(d, len(d['type']), 7, 6, 111)
        
        set_bars(df, idx)
        set_ticks(df, idx, 9)
        
        plt.subplots_adjust(left=0.2, right=0.85, top=0.9, bottom=0.1)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07), fancybox=True, ncol=3, fontsize=8)

        y = 1.2
        for l in test:
            p = format_p_value(l['pvalue'][0])
            box_text = '$\overline{x}$='+ '{:.{}f}'.format(l['mean'][0], 2) + '\nM=' + '{:.{}f}'.format(l['med'][0], 2) + '\np' + p
            ax.text(0.4, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':4}, fontsize=10)
            y -= 1.1
        
        save_report(reports, 'main_comparison.pdf')


def main_per_cwe_spec_chart(reports, cwe, df, wilcoxon = True):
    
    composites = enum.read_cwe_composites('stats/{}'.format(cwe))
    
    for i, r in df.iterrows():
        if not enum.check_if_belongs_to_cwe(composites, r['CWE']):
            df = df.drop(i)

    cwes = data.add_others_group(df, tests.filter_small_cwe_groups(df), 'CWE', 'MISC')
    results = {c:data.filter_results_per_field(df, c, 'CWE') for c in cwes}
    print(results)
    test_cwe = [tests.hypothesis_test(df[df['CWE'] == c]['diff']) for c in cwes if wilcoxon]

    d = {'neg': pd.Series([results[i][0]/sum(results[i]) if sum(results[i]) != 0 else 0 for i in cwes]),
        'pos': pd.Series([results[i][1]/sum(results[i]) if sum(results[i]) != 0 else 0 for i in cwes]),
        'nul': pd.Series([results[i][2]/sum(results[i]) if sum(results[i]) != 0 else 0 for i in cwes]),
        'N': pd.Series([sum(results[i]) for i in cwes if wilcoxon]),
        'mean': pd.Series([i['mean'][0] for i in test_cwe if wilcoxon]),
        'med': pd.Series([i['med'][0] for i in test_cwe if wilcoxon]),
        'p': pd.Series([i['pvalue'][0] for i in test_cwe if wilcoxon]),
        'type': pd.Series([i for i in cwes])}

    df, idx, fig, ax = config_report(d, len(d['type']), 5, 10, 111)

    set_bars(df, idx)
    set_ticks(df, idx, 9)
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=8)
    
    if wilcoxon:
        boxes_start=5 
        for l in df[::-1].iterrows():
            p = format_p_value(l[1]['p'])
            box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
            ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
            boxes_start -= 1.0 

    save_report(reports, 'main_per_cwe_spec.pdf')


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
    test_cwe = [tests.hypothesis_test(df[df['CWE'] == c]['diff']) for c in cwes]
    
    d = {'neg': pd.Series([results[i][0]/sum(results[i]) for i in cwes]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in cwes]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in cwes]),
        'N': pd.Series([sum(results[i]) for i in cwes if wilcoxon]),
        'mean': pd.Series([i['mean'][0] for i in test_cwe if wilcoxon]),
        'med': pd.Series([i['med'][0] for i in test_cwe if wilcoxon]),
        'p': pd.Series([i['pvalue'][0] for i in test_cwe if wilcoxon]),
        'type': pd.Series([i for i in cwes])}

    df, idx, fig, ax = config_report(d, len(d['type']), 5, 10, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 9)
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=8)

    boxes_start=7.1
    for l in df[::-1].iterrows():
        p = format_p_value(l[1]['p'])
        box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
        boxes_start -= 1
    
    save_report(reports, 'main_per_cwe.pdf')

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
    set_ticks(df, idx, 9)
    
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, ncol=3, fontsize=8)
    
    if wilcoxon:
        boxes_start = 7
        for l in df[::-1].iterrows():    
            p = format_p_value(l[1]['p'])
            box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
            ax.text(0.57, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=8)
            boxes_start -= 1
    
    save_report(reports, 'main_per_guideline.pdf')

def main_per_language_chart(reports, df, wilcoxon = True):
    
    for i, r in df.iterrows():
        lang = enum.get_language(r['Language'])
        if lang != None:
            df.at[i, 'Language'] = lang
    
    langs = tests.filter_small_sample_groups(df, 'Language')
    langs = data.add_others_group(df, langs, 'Language', 'Other')
        
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
    set_ticks(df, idx, 9)    
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.04), fancybox=True, ncol=3, fontsize=8)

    boxes_start = 6
    for l in df[::-1].iterrows():
        p = format_p_value(l[1]['p'])
        box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.67, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
        boxes_start -= 1
        
    save_report(reports, 'main_per_language.pdf') 

def main_per_severity(reports, df, wilcoxon = True):
    
    y_axis = data.add_others_group(df, enum.severity, 'Severity', 'UNKNOWN')
    
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
    
    set_ticks(df, idx, 9)
    plt.subplots_adjust(left=0.05, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), fancybox=True, ncol=3, fontsize=8)
    
    boxes_start = 3
    for l in df[::-1].iterrows():
        p = format_p_value(l[1]['p'])
        box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\nM=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
        boxes_start -= 1
        
    save_report(reports, 'main_per_severity.pdf')

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


