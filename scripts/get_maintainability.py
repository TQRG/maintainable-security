import maintainability.better_code_hub as bch
import argparse
import csv

def main(cache, results):

    CACHE = bch.BCHCache('maintainability/'+cache)

    with open(results,'w') as out:
    
        fields = ['owner', 'project', 'sha', 'sha-p', 'main(sha)', 'main(sha-p)', 'main(diff)']
        writer = csv.DictWriter(out, fieldnames=fields)    
        writer.writeheader()

        neg = 0; pos = 0; nul = 0; keys = CACHE.data.keys()
        
        # fix problem of incomplete evaluation
        if len(keys) % 2 == 0:
            len_eval = len(keys)
        else:
            len_eval = len(keys) - 1

        for i in range(0, len_eval,2):
 
            owner, proj, sha = list(keys)[i].split('/')
            owner_p, proj_p, sha_p = list(keys)[i+1].split('/')

            info_f = CACHE.get_stored_commit_analysis(owner, proj, sha)
            info_p = CACHE.get_stored_commit_analysis(owner_p, proj_p, sha_p)
            
            if info_f.get('error') or info_p.get('error'):
                continue
            main = bch.compute_maintainability_score(info_f)
            main_p = bch.compute_maintainability_score(info_p)
            main_d = main - main_p

            if main_d < 0:
                neg += 1
            elif main_d > 0:
                pos += 1
            else:
                nul += 1

            writer.writerow({'owner' : owner,
                            'project': proj,
                            'sha': sha,
                            'sha-p': sha_p,
                            'main(sha)': main,
                            'main(sha-p)': main_p,
                            'main(diff)': main_d
                            })
        
        print('neg=', neg, '; pos=', pos, '; nul=', nul, "; total=", sum([neg,pos,nul]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--bch-cache',metavar='bch-cache',required=True,help='the bch cache filename')
    parser.add_argument('--results-file',metavar='results-file',required=True,help='the path to save the results')

    args = parser.parse_args()
    main(cache=args.bch_cache, results=args.results_file)