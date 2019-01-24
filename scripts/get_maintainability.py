import maintainability.better_code_hub as bch
import argparse
import csv
import collections
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import wilcoxon

def _print_hypothesis_test(differences):
    """Paired Wilcoxon signed-rank test (N should be > 20)"""
    test, pvalue = _hypothesis_test(differences)
    stats = {'test': [test], 'med':[pd.DataFrame({'diff': differences})['diff'].median()],'pvalue': [pvalue]}
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
def count(t_id, id, total, lang, pattern, year, l, p, y):
    total[t_id] += 1
    lang[l][id] += 1
    pattern[p][id] += 1
    year[y][id] += 1

def total_main_barchart(total_sec, total_reg, graphics, result):
    
    sec = sum([value for key,value in total_sec.items()])
    reg = sum([value for key,value in total_reg.items()]) 
    
    d = {'neg' : pd.Series([total_reg['neg']/reg, total_sec['neg']/sec]),
        'pos' : pd.Series([total_reg['pos']/reg, total_sec['pos']/sec]),
        'none' : pd.Series([total_reg['nul']/reg, total_sec['nul']/sec]),
        'type' : pd.Series(['Regular Change','Security Change'])}

    # d = {'neg' : pd.Series([total_reg['neg'], total_sec['neg']]),
    #     'pos' : pd.Series([total_reg['pos'], total_sec['pos']]),
    #     'none' : pd.Series([total_reg['nul'], total_sec['nul']]),
    #     'type' : pd.Series(['Regular Change','Security Change'])}
    
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
    
    y = 1.3
    for l in result.iterrows():
        if float('{:.{}f}'.format(l[1]['pvalue'], 3)) <= 0.000:
            p = '<0.001'
        else:
            p = '={:.{}f}'.format(l[1]['pvalue'], 3)
        box_text = '$Z$='+ '{:.{}f}'.format(l[1]['test'], 2) + '\n$\widetilde{x}$=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
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
        total = {'neg': 0, 'pos': 0, 'nul': 0}

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
            
                langs = check_if_in(lang, langs)
                patterns = check_if_in(pattern, patterns)
                years = check_if_in(year, years)

                if main_d < 0:
                    count('neg', 0, total, langs, patterns, years, lang, pattern, year)
                elif main_d > 0:
                    count('pos', 1, total, langs, patterns, years, lang, pattern, year)
                else:
                    count('nul', 2, total, langs, patterns, years, lang, pattern, year)

                differences.append(main_d)
                if pattern not in diff_by_pat:
                    diff_by_pat[pattern] = [main_d]
                else:
                    diff_by_pat[pattern].append(main_d)
                    
            return patterns, none, error, total, diff_by_pat 

def sec_vs_rg_commits(CACHE, graphics, dataset):
    
    _, none_sec, error_sec, total_sec, _ = analysis('../dataset/commits_patterns_sec.csv', '../results/sec-main-results.csv', CACHE)
    _, none_reg, error_reg, total_reg, _ = analysis('../dataset/commits_regular.csv', '../results/sec-reg-results.csv', CACHE)
    
    df_sec = pd.read_csv('../results/sec-main-results.csv')
    df_reg = pd.read_csv('../results/sec-reg-results.csv')
    
    df = df_sec.join(df_reg,lsuffix='_sec',rsuffix='_reg')
    
    
    fil = df[(df['main(diff)_reg'] != 'error') & (df['main(diff)_sec'] != 'error')]
    
    
    stats1 = _print_hypothesis_test(fil['main(diff)_sec'].astype('float64'))
    print(total_sec, 'total=', sum([value for key,value in total_sec.items()]), ', none=', none_sec, ', error=', error_sec)
    stats = _print_hypothesis_test(fil['main(diff)_reg'].astype('float64'))
    print(total_reg, 'total=', sum([value for key,value in total_reg.items()]), ', none=', none_reg, ', error=', error_reg)

    result = stats.append([stats1])
    result.to_csv('../results/statistical_test.csv')
    
    total_sec, total_reg = {'neg': 0, 'pos': 0, 'nul': 0}, {'neg': 0, 'pos': 0, 'nul': 0}
    
    for i in fil.iterrows():
        print(i[1]['main(diff)_sec'], i[1]['main(diff)_reg'])
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

    df = pd.DataFrame(d)

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
    plt.subplots_adjust(left=0.25, right=0.9, top=0.9, bottom=0.06)
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), fancybox=True, ncol=3, fontsize=7)

    y = 8
    for l in df.iterrows():
        if float('{:.{}f}'.format(l[1]['p'], 3)) <= 0.000:
            p = '<0.001'
        else:
            p = '={:.{}f}'.format(l[1]['p'], 3)
        box_text = 'N='+str(l[1]['N'])+'\n$Z$='+ '{:.{}f}'.format(l[1]['mean'], 2) + '\n$\widetilde{x}$=' + '{:.{}f}'.format(l[1]['med'], 2) + '\np' + p
        ax.text(0.68, y, box_text , bbox={'facecolor':'white', 'alpha':0.8, 'pad':3}, fontsize=5)
        y -= 1.02
        
    plt.gca().xaxis.grid(True, linestyle='--')

    plt.savefig('../paper/ICPC19/figures/category.pdf')

def sec_by_type(CACHE):
    
    patterns, none, error, total_sec, diff_by_path = analysis('../dataset/commits_patterns_sec.csv', '../results/sec-main-results.csv', CACHE)
    
    assert len(diff_by_path['ml']) == sum(patterns['ml'])
    assert len(diff_by_path['xss']) == sum(patterns['xss'])
    assert len(diff_by_path['misc']) == sum(patterns['misc'])
    
    keys = patterns.keys()
    to_del = []
    
    for i in keys:
        if sum(patterns[i]) < 21:
            diff_by_path['misc'] += diff_by_path[i]
            patterns['misc'][0] += patterns[i][0]
            patterns['misc'][1] += patterns[i][1]
            patterns['misc'][2] += patterns[i][2]
            to_del.append(i)
    
    for i in to_del:
        del patterns[i]
        del diff_by_path[i]

    main_by_type_barchart(patterns, diff_by_path)
    

def main(cache, results, graphics, dataset):

    CACHE = readBCHCache(cache)
    
    # Figure 1
    sec_vs_rg_commits(CACHE, graphics, dataset)
    
    # Figure 2
    sec_by_type(CACHE)


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--bch-cache',metavar='bch-cache',required=True,help='the bch cache filename')
    parser.add_argument('--results-file',metavar='results-file',required=True,help='the path to save the results')
    parser.add_argument('--graphics-path',metavar='graphics-path',required=True,help='the graphics path')
    parser.add_argument('--dataset',metavar='dataset',required=True,help='the dataset path')

    args = parser.parse_args()
    main(cache=args.bch_cache, results=args.results_file, graphics=args.graphics_path, dataset=args.dataset)