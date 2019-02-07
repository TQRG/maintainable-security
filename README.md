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
python get_maintainability.py --bch-cache maintainability/bch_cache.json --results-file ../results/sec-main-results.csv --graphics-path ../results/ --dataset ../dataset/commits_patterns_sec.csv
``` 

Reports:

```
source venv/bin/activate
cd scripts
python histogram.py --projects-csv final_projects.csv --commits-csv final_results.csv
```
