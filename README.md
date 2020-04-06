# security-maintainability

**New submission @ICSME20**

Abstract Submission: May 22, 2020

Paper Submission: May 28, 2020

https://icsme2020.github.io/

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
source venv/bin/activate
cd scripts
python3 report.py --report export -secdb ../dataset/db_release_security_fixes.csv -regdb ../dataset/db_release_regular_fixes.csv -results ../results -cache maintainability/bch_cache.json
``` 

Comparison between security and regular commits:

```
source venv/bin/activate
cd scripts
python3 report.py --report comparison -secdb ../results/maintainability_release_security_fixes.csv -regdb ../results/maintainability_release_regular_fixes.csv -reports ../reports
``` 

Get security maintainability report per guideline:

```
source venv/bin/activate
cd scripts
python3 report.py --report guideline -secdb ../results/maintainability_release_security_fixes.csv -reports ../reports
``` 


Get security maintainability report per language:

```
source venv/bin/activate
cd scripts
python3 report.py --report language -secdb ../results/maintainability_release_security_fixes.csv -reports ../reports
``` 


