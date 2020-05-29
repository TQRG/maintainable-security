import pandas as pd
from scipy.stats import wilcoxon

def hypothesis_test(diff, i):
    test, pvalue = wilcoxon(x=diff, zero_method="pratt")
    return pd.DataFrame({'guideline':[i], 'test': [test], 
                        'med':[pd.DataFrame({'diff': diff})['diff'].median()],
                        'pvalue': [pvalue], 
                        'mean':[pd.DataFrame({'diff': diff})['diff'].mean()]})

def filter_small_sample_groups(df, key):
    return [i for i in df[key].unique() if len(df[df[key] == i]) > 19]

def filter_small_cwe_groups(df):
    return [i for i in df['CWE'].unique() if str(i) != 'nan' and (len(df[df['CWE'] == i]) > 19) and 'CWE' in i]

def filter_cwe_groups(df):
    return [i for i in df['CWE'].unique() if str(i) != 'nan' and 'CWE' in i]
