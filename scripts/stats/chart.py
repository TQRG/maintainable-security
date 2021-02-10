import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib import rcParams

import pandas as pd
import seaborn as sns


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

def main_comparison_chart(reports, dfs):   
        
        df_sec, df_rand_reg, df_size_reg = dfs['security'], dfs['random'], dfs['size']

        test = pd.concat((tests.hypothesis_test(df_rand_reg['diff'], 'random-reg'), 
                            tests.hypothesis_test(df_size_reg['diff'], 'size-reg'),
                            tests.hypothesis_test(df_sec['diff'], 'security')),
                            ignore_index=True)
                        
        total_sec, total_rand_reg, total_size_reg = data.filter_results(df_sec), \
                                                    data.filter_results(df_rand_reg[pd.notnull(df_rand_reg['diff'])]),  \
                                                    data.filter_results(df_size_reg)    
        db_size = len(df_sec)  
        db_rand_size = len(df_rand_reg[pd.notnull(df_rand_reg['diff'])])

        rep = {'neg' : pd.Series([total_rand_reg['neg']/db_rand_size, total_size_reg['neg']/db_size , total_sec['neg']/db_size]),
                'neg_abs' : pd.Series([total_rand_reg['neg'],  total_size_reg['neg'], total_sec['neg']]),
                'pos' : pd.Series([total_rand_reg['pos']/db_rand_size, total_size_reg['pos']/db_size , total_sec['pos']/db_size]),
                'pos_abs' : pd.Series([total_rand_reg['pos'],  total_size_reg['pos'], total_sec['pos']]),
                'nul' : pd.Series([total_rand_reg['nul']/db_rand_size, total_size_reg['nul']/db_size , total_sec['nul']/db_size]),
                'nul_abs' : pd.Series([total_rand_reg['nul'],  total_size_reg['nul'], total_sec['nul']]),
                'type' : pd.Series(['Regular Changes\n(random-baseline)', 'Regular Changes\n(size-baseline)', 'Security Patches'])}
        
        df, idx, fig, ax = config_report(rep, len(rep['type']), 7, 5, 111)
        
        set_bars(df, idx)
        set_ticks(df, idx, fontsize=12) 
        
        plt.subplots_adjust(left=0.2, right=0.85, top=0.9, bottom=0.1)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), fancybox=True, ncol=3, fontsize=11)

        y = 2.2
        for i, r in test[::-1].iterrows():
            p = format_p_value(r['pvalue'])
            box_text = '$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
            ax.text(0.4, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':4}, fontsize=10)
            y -= 1.1
        
        save_report(reports, 'baseline.pdf')
        test.join(df).to_csv(reports+'/baseline_stats_report.csv', index=False)

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
    
    langs = tests.filter_small_sample_groups(df, 'Language')
        
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
    
    boxes_start = 5
    for i, r in test.join(df)[::-1].iterrows():
        p = format_p_value(r['pvalue'])
        box_text = 'N='+str(sum([r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
        ax.text(0.5, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
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
        'type': pd.Series(['Unknown', 'Low', 'Medium', 'High'])}

    df, idx, fig, ax = config_report(rep, len(rep['type']), 6, 6, 111)
    
    set_bars(df, idx)
    set_ticks(df, idx, 9)
    
    plt.subplots_adjust(left=0.05, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05), fancybox=True, ncol=3, fontsize=8)
    
    boxes_start = 3
    for i, r in test.join(df)[::-1].iterrows():
        p = format_p_value(r['pvalue'])
        box_text = 'N='+str(sum([r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
        ax.text(0.54, boxes_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=9)
        boxes_start -= 1
        
    save_report(reports, 'main_per_severity.pdf')
    test.join(df).to_csv(reports+'/severity_test_report.csv', index=False)
    
def main_guideline_swarm_plot(reports, df):
    
    swarm_data = {'m': [], 'guideline': [], 'impact': []}
    
    x_axis_values = dict(enum.guidelines, **{'diff': '$M (v)$'})
        
    test = pd.concat([tests.hypothesis_test(df[i+'-diff'], i) 
                            if i != 'diff' 
                            else tests.hypothesis_test(df['diff'], 'diff')
                            for i in x_axis_values],
                            ignore_index=True)
    
    results = {i:data.filter_results_per_guideline(df, i) 
                for i in x_axis_values}    
    
    keys = results.keys()
    rep = pd.DataFrame({'neg': pd.Series([results[i][0]/sum(results[i]) for i in keys]),
        'neg_abs': pd.Series([results[i][0] for i in keys]),
        'pos': pd.Series([results[i][1]/sum(results[i]) for i in keys]),
        'pos_abs': pd.Series([results[i][1] for i in keys]),
        'nul': pd.Series([results[i][2]/sum(results[i]) for i in keys]),
        'nul_abs': pd.Series([results[i][2] for i in keys]),
        'N': pd.Series([sum(results[i]) for i in keys]),
        'type': pd.Series([x_axis_values[i] for i in keys])})
    
    for v in x_axis_values.keys():
        f = v+'-diff' if 'diff' not in v else v
        for i in df[f]:
            swarm_data['m'].append(i)
            swarm_data['guideline'].append(x_axis_values[v])
            if i > 0:
                swarm_data['impact'].append('Positive')
            elif i < 0:
                swarm_data['impact'].append('Negative')
            else:
                swarm_data['impact'].append('None')
                
    palette ={"Positive":"green","None":"orange","Negative":"red"}
    swarm_data = pd.DataFrame(swarm_data)
    
    f, ax = plt.subplots(figsize=(9, 18))
    ax.set_xscale("symlog")

    sns.swarmplot(x="m", y="guideline", hue='impact', data=swarm_data, alpha=0.7, ax=ax, size=4.3, palette=palette, lw=2, edgecolor='k')
    swarm_cols = ax.collections
    
    sns.boxplot(x="m", y="guideline", data=swarm_data,
                     showcaps=True,boxprops=dict(facecolor='None', zorder=10),
                     showfliers=False,whiskerprops={"zorder":10}, ax=ax, zorder=10)
    
    ax.legend(swarm_cols[-3:],np.unique(swarm_data.impact), loc='upper center', bbox_to_anchor=(0.5, 1.025), ncol=3)
    ax.set_ylabel('')
    ax.set_xlabel("$\\Delta M (v_{s-1}, v{s})$")

    stats_start, cases_start = 8.1, 7.53
    for i, r in test.join(rep)[::-1].iterrows():
        p = format_p_value(r['pvalue'])
        box_text = 'N='+str(sum( [r['pos_abs'], r['neg_abs'], r['nul_abs']]))+'\n$\overline{x}$='+ '{:.{}f}'.format(r['mean'], 2) + '\nM=' + '{:.{}f}'.format(r['med'], 2) + '\np' + p
        ax.text(11000, stats_start, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=10)
        ax.text(-30, cases_start, '{} (${:.2f}\%$)'.format(r['neg_abs'], r['neg']*100), bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=8)
        ax.text(-1, cases_start, '{} (${:.2f}\%$)'.format(r['nul_abs'], r['nul']*100), bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=8)
        ax.text(2, cases_start, '{} (${:.2f}\%$)'.format(r['pos_abs'], r['pos']*100), bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=8)
        
        stats_start -= 1
        cases_start -= 1
    
    save_report(reports, 'main_guideline_plot.pdf')    
    test.join(df).to_csv(reports+'/guideline_test_report.csv', index=False)
    


