
def filter_results_per_field(df, t, field):
    return [df[(df['diff'] < 0) & (df[field] == t)].shape[0],
                df[(df['diff'] > 0) & (df[field] == t)].shape[0],
                df[(df['diff'] == 0) & (df[field] == t)].shape[0]]

def filter_results(df):
    return {'neg':df[df['diff'] < 0].shape[0],
                'pos':df[df['diff'] > 0].shape[0],
                'nul':df[df['diff'] == 0].shape[0]}

def filter_results_per_guideline(df, g):
    f = g+'-diff' if 'diff' not in g else g
    return [df[df[f] < 0].shape[0],
                df[df[f] > 0].shape[0],
                df[df[f] == 0].shape[0]]

def add_others_group(df, group, key, label):
    for i, r in df.iterrows():
        if r[key] not in group:
            df.at[i, key] = label
    return [label] + group
    

    
    