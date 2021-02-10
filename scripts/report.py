import argparse
from os import listdir
from os.path import isfile, join
from math import sqrt

import csv
import collections
import pandas as pd
import numpy as np
import matplotlib
import seaborn as sns
import matplotlib.pyplot as plt
from collections import OrderedDict

import maintainability.better_code_hub as bch
import stats.chart as chart



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
        
def main_calculation_by_db(db, results, cache, dataset, baseline=""):
    df = pd.read_csv(db)
    if dataset == 'regular':
        path = '{}/maintainability_release_{}_regular_changes.csv'.format(results, baseline)
    else:
        path = '{}/maintainability_release_security_changes.csv'.format(results)

    df = main_calculation(df, cache, dataset)
    return df, path

def export(secdb, regdb, results, cache_path, baseline):
    
    cache = bch.BCHCache(cache_path)
    
    # df_sec, sec_res_path = main_calculation_by_db(secdb, results, cache, 'security')
    # df_sec.to_csv(sec_res_path, index=False)
    
    df_reg, reg_res_path = main_calculation_by_db(regdb, results, cache, 'regular', baseline=baseline)
    df_reg.to_csv(reg_res_path, index=False)
        
def language(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_per_language_chart(reports, df_sec)

def severity(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_per_severity(reports, df_sec)

def guideline(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_per_guideline_chart(reports, df_sec)

def cwe(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_per_cwe_chart(reports, df_sec)
    
def cwe_spec(secdb, reports, cwe):
    df_sec = pd.read_csv(secdb)
    chart.main_per_cwe_spec_chart(reports, cwe, df_sec)

def comparison(results, reports):
    files = [f for f in listdir(results) if isfile(join(results, f)) and '.csv' in f]
    dfs = {f.split('_')[2]:pd.read_csv("{}{}".format(results, f)) for f in files}
    chart.main_comparison_chart(reports, dfs)
    
def guideline_swarm(secdb, reports):
    df_sec = pd.read_csv(secdb)
    chart.main_guideline_swarm_plot(reports, df_sec)
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description='Report results')    
    parser.add_argument('--report', dest='goal', choices=['export', 'comparison', 'severity', 'guideline', 'language', 'cwe', 'cwe-spec'],
                        help='choose a report goal')
                        
    parser.add_argument('-results', type=str, metavar='folder path', help='results folder path')  
    parser.add_argument('-reports', type=str, metavar='folder path', help='reports folder path')      
    parser.add_argument('-secdb', type=str, metavar='file path', help='security dataset path')    
    parser.add_argument('-regdb', type=str, metavar='file path', help='regular dataset path')    
    parser.add_argument('-cache', type=str, metavar='file path', help='cache path')   
    parser.add_argument('-cwe', type=str, metavar='file path', help='cache path')    
    parser.add_argument('-baseline', type=str, metavar='baseline name', help='baseline name')    
     
    args = parser.parse_args()

    if args.goal == 'export':  
        if args.secdb != None and args.regdb != None \
            and args.results != None and args.cache != None \
            and (args.baseline == "random" or args.baseline == "size"):
            export(secdb=args.secdb, regdb=args.regdb, results=args.results, cache_path=args.cache, baseline=args.baseline)
    elif args.goal == 'comparison':
        if args.results != None \
            and args.reports != None:
            comparison(results=args.results, reports=args.reports)
    elif args.goal == 'guideline':
        if args.secdb != None and args.reports != None:
            guideline_swarm(secdb=args.secdb, reports=args.reports)
    elif args.goal == 'language':
        if args.secdb != None and args.reports != None:
            language(secdb=args.secdb, reports=args.reports)
    elif args.goal == 'severity':
        if args.secdb != None and args.reports != None:
            severity(secdb=args.secdb, reports=args.reports)
    elif args.goal == 'cwe':
        if args.secdb != None and args.reports != None:
            cwe(secdb=args.secdb, reports=args.reports)
    elif args.goal == 'cwe-spec':
        if args.secdb != None and args.reports != None and args.cwe != None:
            cwe_spec(secdb=args.secdb, reports=args.reports, cwe=args.cwe)
    else:
        print('Something is wrong. Verify your parameters')
