from connect import connect_to_db
import argparse
import csv

def get_patterns(conn, key):
    pip = conn.pipeline()
    pip.lrange(key, 0, -1)
    return pip.execute()[0]

def get_keys(conn, key):
    pip = conn.pipeline()
    pip.keys(pattern=key)
    return pip.execute()

def main(config, filepath):
    
    r = connect_to_db(config)
    
    vulns = get_patterns(r, 'vulns_class')
    commits = get_keys(r,'commit:*:*:*:*')

    with open(filepath,'w') as out:
        
        fields = ['owner', 'project', 'sha', 'sha-p', 'language', 'pattern', 'year','reported']
        writer = csv.DictWriter(out, fieldnames=fields)    
        writer.writeheader()
        count = 0
        for c in commits[0]:

            _, owner, project, _, _ = c.split(':')
            
            # improve this
            pip = r.pipeline()
            pip.hget(c,'vuln?')
            pip.hget(c,'sha')
            pip.hget(c,'sha-p')
            pip.hget(c,'repo_owner')
            pip.hget(c,'repo_name')
            pip.hget('repo:%s:%s:n'%(owner, project), 'report')
            pip.hget(c,'lang')
            pip.hget(c,'class')
            pip.hget(c,'change_to')
            pip.hget(c,'year')

            ver, sha, sha_p, repo_owner, repo_name, rep, lang, pattern, change_to, year = pip.execute()

            # samples verified
            if ver == 'Y':
                # samples reported in IJSSE
                if rep == 'Y':
                    reported = 1
                else:
                    reported = 0
                if change_to is not None and change_to in vulns:
                    pattern = change_to

                writer.writerow({'owner' : repo_owner,
                                'project': repo_name,
                                'sha': sha,
                                'sha-p': sha_p,
                                'language': lang,
                                'pattern': pattern,
                                'year': year,
                                'reported': reported
                                })

                count+=1

    print(count, ' vulnerabilities verified and reported.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-config',metavar='config',required=True,help='the config to redis')
    parser.add_argument('--ofilepath',metavar='filepath',required=True,help='the path to save the dataset')

    args = parser.parse_args()
    main(config=args.redis_config, filepath=args.ofilepath)