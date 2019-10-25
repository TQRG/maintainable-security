# security-maintainability

**3rd submission @ICPC20**

https://conf.researchr.org/home/icpc-2020

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
python3 get_maintainability.py --bch-cache maintainability/bch_cache.json --results-filename ../results/maintainability-results.csv  --reports ../reports/
``` 

Reports:

```
source venv/bin/activate
cd scripts
python histogram.py --projects-csv ../results/final_projects.csv --commits-csv ../results/final_results.csv --output ../reports
```
