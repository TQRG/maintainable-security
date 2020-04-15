import maintainability.better_code_hub as bch
import stats.chart as chart
import argparse
import csv
import collections
import pandas as pd
import numpy as np
import matplotlib
import seaborn as sns

matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['mathtext.fontset'] = 'cm'

import matplotlib.pyplot as plt
from math import sqrt
import pandas as pd
from collections import OrderedDict

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
        
def main_calculation_by_db(db, results, cache, dataset):
    df = pd.read_csv(db)
    path = '{}/maintainability_release_{}_fixes.csv'.format(results, dataset)
    df = main_calculation(df, cache, dataset)
    return df, path

def export(secdb, regdb, results, cache_path):
    
    cache = bch.BCHCache(cache_path)
    
    df_sec, sec_res_path = main_calculation_by_db(secdb, results, cache, 'security')
    df_reg, reg_res_path = main_calculation_by_db(regdb, results, cache, 'regular')
    
    ids = df_reg[~df_reg['diff'].notnull()].index
    
    df_reg = df_reg.drop(ids) 
    df_sec = df_sec.drop(ids)
        
    df_sec.to_csv(sec_res_path, index=False)
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

def comparison(secdb, regdb, reports):
    df_sec = pd.read_csv(secdb)
    df_reg = pd.read_csv(regdb)
    chart.main_comparison_chart(reports, df_sec, df_reg)
    
    
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
     
    
    args = parser.parse_args()

    if args.goal == 'export':  
        if args.secdb != None and args.regdb != None and args.results != None and args.cache != None:
            export(secdb=args.secdb, regdb=args.regdb, results=args.results, cache_path=args.cache)
    elif args.goal == 'comparison':
        if args.secdb != None and args.regdb != None and args.reports != None:
            comparison(secdb=args.secdb, regdb=args.regdb, reports=args.reports)
    elif args.goal == 'guideline':
        if args.secdb != None and args.reports != None:
            guideline(secdb=args.secdb, reports=args.reports)
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
