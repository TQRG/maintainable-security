import json

# load json config file
def load_cf_file(cf_filename):
    with open(cf_filename) as cf:
        data = json.load(cf)
    return data