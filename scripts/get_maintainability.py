import maintainability.better_code_hub as bch
import argparse
import csv
import collections
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon, shapiro
from statistics import mean, stdev
from math import sqrt

def _print_hypothesis_test(differences):
    """Paired Wilcoxon signed-rank test (N should be > 20)"""
    _, pvalue = shapiro(differences)
    print("Shapiro-Wilk test for normality: {}".format(pvalue))
    test, pvalue = _hypothesis_test(differences)
    stats = {'test': [test], 'med':[pd.DataFrame({'diff': differences})['diff'].median()],'pvalue': [pvalue], 
                'mean':[pd.DataFrame({'diff': differences})['diff'].mean()]}
    df = pd.DataFrame(stats)
    print("Wilcoxon signed-rank test {}, p-value: {}".format(test,pvalue))
    return df

def _hypothesis_test(differences):
    return wilcoxon(x=differences, zero_method="pratt")

def readBCHCache(path):
    return bch.BCHCache(path)

def set_key(owner, project, sha, sha_p):
    return '{}:{}:{}:{}'.format(owner, project, sha, sha_p)

def get_key(keys, i):
    return list(keys)[i]

def pair_info(file):
    info = {}
    with open(file, 'r') as f:
        for lines in f.readlines()[1:]:
            owner, project, sha, sha_p, lang, pattern, year, _ = lines.split(',')
            key = set_key(owner, project, sha, sha_p)
            if key not in info:
                info[key] = [lang, pattern, year]
    return info

def clean_plot():
    plt.gcf().clear()

# TODO: IMPROVE
def count(id, pattern, p):
    pattern[p][id] += 1

def total_main_barchart(total_sec, total_reg, graphics, result):
    
    sec = sum([value for key,value in total_sec.items()])
    reg = sum([value for key,value in total_reg.items()])
    
    d = {'neg' : pd.Series([total_reg['neg']/reg, total_sec['neg']/sec]),
        'pos' : pd.Series([total_reg['pos']/reg, total_sec['pos']/sec]),
        'none' : pd.Series([total_reg['nul']/reg, total_sec['nul']/sec]),
        'type' : pd.Series(['Regular Change','Security Change'])}
    
    index = np.arange(len(d['type']))
    
    df = pd.DataFrame(d)
    print(df[['neg','pos','none']])
    
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
        box_text = '$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\n$\widetilde{x}$=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.46, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':4}, fontsize=9)
        y -= 1.1
    
    plt.gca().xaxis.grid(True, linestyle='--')
    

    plt.savefig('../paper/ICPC19/figures/maintainability.pdf')

def dic_barchart(dic, graphics, title, file_name):
    d = {'neg' : pd.Series([dic[key][0] for key in dic]),
        'pos' : pd.Series([dic[key][1] for key in dic]),
        'nul' : pd.Series([dic[key][2] for key in dic]),
        'type' : pd.Series([key for key in dic])}
    index = np.arange(len(d['type']))
    df = pd.DataFrame(d)
    bar_width = 0.3
    neg = plt.bar(index, df['neg'], bar_width, alpha=0.9, align='center', color='red', label='neg')
    pos = plt.bar(index + bar_width, df['pos'], bar_width, alpha=0.9, align='center', color='green', label='pos')
    nul = plt.bar(index + 2 * bar_width, df['nul'], bar_width, alpha=0.9, align='center', color='orange', label='nul')
    plt.title(title)
    plt.ylabel("# samples")
    plt.xticks(index + bar_width, df['type'], fontsize=8, rotation='vertical')
    plt.legend()
    plt.subplots_adjust(bottom=0.2)
    plt.savefig(graphics+file_name)

def check_if_in(key, dic):
    if key not in dic:
        dic[key] = [0,0,0]
    return dic
    
def analysis(dataset, results, CACHE):
    
    with open(results,'w') as out:
        
        fields = ['owner', 'project', 'sha', 'sha-p', 'main(sha)', 'main(sha-p)', 'main(diff)']
        writer = csv.DictWriter(out, fieldnames=fields)    
        writer.writeheader()

        langs, patterns, years, differences, diff_by_pat = {}, {}, {}, [], {}
        none = 0; error = 0
    
        with open(dataset) as ds:
            lines = ds.readlines()[1:]
            for l in lines:
                data = l.split(',')
                owner, proj, sha, sha_p, lang, pattern, year = l.split(',')[0:7]
                       
                info_f = CACHE.get_stored_commit_analysis(owner, proj, sha)
                info_p = CACHE.get_stored_commit_analysis(owner, proj, sha_p)

                if info_f is None or info_p is None:
                    none+=1
                    writer.writerow({'owner' : owner, 'project': proj,
                                    'sha': sha, 'sha-p': sha_p,
                                    'main(sha)': 'error',
                                    'main(sha-p)': 'error',
                                    'main(diff)': 'error'
                                    })
                    continue
                if info_f.get('error') or info_p.get('error'):
                    error+=1
                    writer.writerow({'owner' : owner, 'project': proj,
                                    'sha': sha, 'sha-p': sha_p,
                                    'main(sha)': 'error',
                                    'main(sha-p)': 'error',
                                    'main(diff)': 'error'
                                    })
                    continue
                
                try:
                    main = bch.compute_maintainability_score(info_f)
                    main_p = bch.compute_maintainability_score(info_p)
                except ZeroDivisionError as e:
                    writer.writerow({'owner' : owner, 'project': proj,
                                    'sha': sha, 'sha-p': sha_p,
                                    'main(sha)': 'error',
                                    'main(sha-p)': 'error',
                                    'main(diff)': 'error'
                                    })
                    error+=1
                    continue
                
                main_d = main - main_p
                
                writer.writerow({'owner' : owner, 'project': proj,
                                'sha': sha, 'sha-p': sha_p,
                                'main(sha)': main,
                                'main(sha-p)': main_p,
                                'main(diff)': main_d
                                })          
            
                patterns = check_if_in(pattern, patterns)
                
                if main_d < 0:
                    count(0, patterns, pattern)
                elif main_d > 0:
                    count(1, patterns, pattern)
                else:
                    count(2, patterns, pattern)

                differences.append(main_d)
                if pattern not in diff_by_pat:
                    diff_by_pat[pattern] = [main_d]
                else:
                    diff_by_pat[pattern].append(main_d)
                    
            return patterns, none, error, diff_by_pat 

def sec_vs_rg_commits(CACHE, graphics, dataset):
    
    _, none_sec, error_sec, _ = analysis('../dataset/commits_patterns_sec.csv', '../results/sec-main-results.csv', CACHE)
    _, none_reg, error_reg, _ = analysis('../dataset/commits_regular.csv', '../results/sec-reg-results.csv', CACHE)
    
    df_sec = pd.read_csv('../results/sec-main-results.csv')
    df_reg = pd.read_csv('../results/sec-reg-results.csv')
    df_aux = pd.read_csv('../dataset/commits_patterns_sec.csv')
    df_pat = df_aux[['pattern','language']]
    
    df = df_sec.join(df_reg,lsuffix='_sec',rsuffix='_reg')
    df = df.join(df_pat)
        
    fil = df[(df['main(diff)_reg'] != 'error') & (df['main(diff)_sec'] != 'error')]
    
    cohens_d = (fil['main(diff)_reg'].astype('float64').mean() - fil['main(diff)_sec'].astype('float64').mean()) / (sqrt((stdev(fil['main(diff)_reg'].astype('float64')) ** 2 + stdev(fil['main(diff)_sec'].astype('float64')) ** 2) / 2))
    print('coehns', cohens_d)
    
    stats1 = _print_hypothesis_test(fil['main(diff)_sec'].astype('float64'))
    stats = _print_hypothesis_test(fil['main(diff)_reg'].astype('float64'))

    result = stats.append([stats1])
    print(result)
    result.to_csv('../results/statistical_test.csv')
    
    total_sec, total_reg = {'neg': 0, 'pos': 0, 'nul': 0}, {'neg': 0, 'pos': 0, 'nul': 0}
    
    for i in fil.iterrows():
        if float(i[1]['main(diff)_sec']) < 0:
            total_sec['neg'] += 1
        elif float(i[1]['main(diff)_sec']) > 0:
            total_sec['pos'] += 1
        else:
            total_sec['nul'] += 1
            
        if float(i[1]['main(diff)_reg']) < 0:
            total_reg['neg'] += 1
        elif float(i[1]['main(diff)_reg']) > 0:
            total_reg['pos'] += 1
        else:
            total_reg['nul'] += 1
    
    total_main_barchart(total_sec, total_reg, graphics, result)
    clean_plot()
    print(total_sec, 'total=', sum([value for key,value in total_sec.items()]), ', none=', none_sec, ', error=', error_sec)
    print(total_reg, 'total=', sum([value for key,value in total_reg.items()]), ', none=', none_reg, ', error=', error_reg)
    
    return fil
    
    
    
def main_by_type_barchart(patterns, diff):

    keys = {'ml':'Memory Leak', 'misc': 'Miscellaneous', 'injec': 'Injection', 'xss':'Cross-Site Scripting','dos':'Denial-of-Service', 
            'csrf':'Cross-Site Request Forgery', 'auth': 'Broken Authentication', 'ucwkv':'Components with Known Vuln(s)',
            'rl': 'Resource Leak'}
    
    d = {'neg': pd.Series([patterns[i][0]/sum(patterns[i]) for i in patterns]),
        'pos': pd.Series([patterns[i][1]/sum(patterns[i]) for i in patterns]),
        'nul': pd.Series([patterns[i][2]/sum(patterns[i]) for i in patterns]),
        'N': pd.Series([len(diff[i]) for i in patterns]),
        'mean': pd.Series([_print_hypothesis_test(diff[i])['test'][0] for i in patterns]),
        'med': pd.Series([_print_hypothesis_test(diff[i])['med'][0] for i in patterns]),
        'p': pd.Series([_print_hypothesis_test(diff[i])['pvalue'][0] for i in patterns]),
        'type': pd.Series([keys[i] for i in patterns])}
        
    e = {'neg': pd.Series([patterns[i][0] for i in patterns]),
        'pos': pd.Series([patterns[i][1] for i in patterns]),
        'nul': pd.Series([patterns[i][2] for i in patterns])}
    
    ef = pd.DataFrame(e)
    print(ef)

    df = pd.DataFrame(d)
    print(df[['neg','pos','nul']])

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
    plt.subplots_adjust(left=0.25, right=0.85, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), fancybox=True, ncol=3, fontsize=7)

    y = 7
    for l in df[::-1].iterrows():
        print(l[1]['p'])
        if float('{:.{}f}'.format(l[1]['p'], 3)) <= 0.000:
            p = '<0.001'
        else:
            p = '={:.{}f}'.format(l[1]['p'], 3)
        box_text = 'N='+str(l[1]['N'])+'\n$\overline{x}$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\n$\widetilde{x}$=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.75, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=5)
        y -= 1.02
        
    plt.gca().xaxis.grid(True, linestyle='--')

    plt.savefig('../paper/ICPC19/figures/category.pdf')

def sec_by_type(CACHE, fil):
    
    keys = fil['pattern'].unique()    
    patterns, diff_by_pattern = {}, {}
     
    for i in keys:
        res, diff = [0,0,0], []

        df = fil[fil['pattern'] == i]
        for i in df.iterrows():
            if float(i[1]['main(diff)_sec']) < 0:
                res[0] += 1
            elif float(i[1]['main(diff)_sec']) > 0:
                res[1] += 1
            else:
                res[2] += 1
        
        if len(df) < 21:
            if 'misc' in patterns:
                patterns['misc'][0] += res[0]
                patterns['misc'][1] += res[1]
                patterns['misc'][2] += res[2]
            else:
                patterns['misc'] = res
                
            if 'misc' in diff_by_pattern:
                diff_by_pattern['misc'] += [float(i[1]['main(diff)_sec']) for i in df.iterrows()]
            else:
                diff_by_pattern['misc'] = [float(i[1]['main(diff)_sec']) for i in df.iterrows()]
        else:
            patterns[i[1]['pattern']] = res
            
            if i[1]['pattern'] in diff_by_pattern:
                diff_by_pattern[i[1]['pattern']] += [float(i[1]['main(diff)_sec']) for i in df.iterrows()]
            else:
                diff_by_pattern[i[1]['pattern']] = [float(i[1]['main(diff)_sec']) for i in df.iterrows()]


    count = 0
    for i in diff_by_pattern:
        count += len(diff_by_pattern[i])
    print('Count=', count)
        
    count = 0
    for i in patterns:
        count += sum(patterns[i])
    print('Count=', count)

    main_by_type_barchart(patterns, diff_by_pattern)
    

def main(cache, results, graphics, dataset):

    CACHE = readBCHCache(cache)
    
    # Figure 1
    fil = sec_vs_rg_commits(CACHE, graphics, dataset)
    plt.clf()
    # Figure 2
    sec_by_type(CACHE, fil)

    fil.to_csv('final_results.csv')


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--bch-cache',metavar='bch-cache',required=True,help='the bch cache filename')
    parser.add_argument('--results-file',metavar='results-file',required=True,help='the path to save the results')
    parser.add_argument('--graphics-path',metavar='graphics-path',required=True,help='the graphics path')
    parser.add_argument('--dataset',metavar='dataset',required=True,help='the dataset path')

    args = parser.parse_args()
    main(cache=args.bch_cache, results=args.results_file, graphics=args.graphics_path, dataset=args.dataset)