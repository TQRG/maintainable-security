# security-maintainability

How to collect maintainability reports from BCH:

Create a config file in `scripts/maintainability/config.json` based on the example in `scripts/maintainability/config-template.json`.

```
virtualenv --python=python3.7 venv
source venv/bin/activate
pip install -r requirements.txt
cd scripts
python -m maintainability.eval_maintainability
```

How to collect maintainability results from BCH:

```
cd scripts
python3 get_maintainability.py --bch-cache bch_cache.json --results-file ../results/sec-main-results.csv
``` 

