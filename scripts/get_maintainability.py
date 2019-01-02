import maintainability.better_code_hub as bch
import argparse
import csv
import collections
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

def total_main_barchart(total, graphics):
    d = {'count' : pd.Series([total['neg'], total['pos'], total['nul']]),
        'type' : pd.Series(['neg', 'pos', 'nul'])}
    df = pd.DataFrame(d)
    plt.bar(df['type'], df['count'], align='center', width=0.5, color=['red', 'green', 'orange'])
    plt.title("Secbench")
    plt.xlabel("Maintainability")
    plt.ylabel("# samples")
    plt.savefig(graphics+'total_main.png')

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

def main(cache, results, graphics, dataset):

    CACHE = readBCHCache(cache)
    data = pair_info(dataset)

    with open(results,'w') as out:
        
        fields = ['owner', 'project', 'sha', 'sha-p', 'main(sha)', 'main(sha-p)', 'main(diff)']
        writer = csv.DictWriter(out, fieldnames=fields)    
        writer.writeheader()

        total = {'neg': 0, 'pos': 0, 'nul': 0}
        keys = CACHE.data.keys()

        langs = {}
        patterns = {}
        years = {}
        with open('../dataset/commits_patterns_sec.csv') as dataset:
            lines = dataset.readlines()[1:]
            for l in lines:
                data = l.split(',')
                owner, proj, sha, sha_p, lang, pattern, year = l.split(',')[0:7]
            
                info_f = CACHE.get_stored_commit_analysis(owner, proj, sha)
                info_p = CACHE.get_stored_commit_analysis(owner, proj, sha_p)

                if info_f is None or info_p is None:
                    print('{},{},{},{},None'.format(owner, proj, sha, sha_p))
                    continue
                if info_f.get('error') or info_p.get('error'):
                    print('{},{},{},{},Error'.format(owner, proj, sha, sha_p))
                    continue

                main = bch.compute_maintainability_score(info_f)
                main_p = bch.compute_maintainability_score(info_p)
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

        total_main_barchart(total, graphics)
        clean_plot()
        dic_barchart(patterns, graphics, 'Maintainability per pattern', 'patterns.png')
        clean_plot()
        dic_barchart(langs, graphics, 'Maintainability per language', 'lang.png')
        clean_plot()
        year_ord = collections.OrderedDict(sorted(years.items()))
        dic_barchart(year_ord, graphics, 'Maintainability per year', 'year.png')

        print(total, 'total=', sum([value for key,value in total.items()]))

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--bch-cache',metavar='bch-cache',required=True,help='the bch cache filename')
    parser.add_argument('--results-file',metavar='results-file',required=True,help='the path to save the results')
    parser.add_argument('--graphics-path',metavar='graphics-path',required=True,help='the graphics path')
    parser.add_argument('--dataset',metavar='dataset',required=True,help='the dataset path')

    args = parser.parse_args()
    main(cache=args.bch_cache, results=args.results_file, graphics=args.graphics_path, dataset=args.dataset)