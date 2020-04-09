import pandas as pd
from scipy.stats import wilcoxon

def hypothesis_test(diff):
    test, pvalue = wilcoxon(x=diff, zero_method="pratt")
    return pd.DataFrame({'test': [test], 
                        'med':[pd.DataFrame({'diff': diff})['diff'].median()],
                        'pvalue': [pvalue], 
                        'mean':[pd.DataFrame({'diff': diff})['diff'].mean()]})

def filter_small_sample_groups(df, key):
    return [i for i in df[key].unique() if len(df[df[key] == i]) > 19]
