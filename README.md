# security-maintainability

Instal requirements:

```
virtualenv --python=python3.7 venv
source venv/bin/activate
pip install -r requirements.txt
```


Merge different caches in `scripts/maintainability/caches/` folder:
```
source venv/bin/activate
cd scripts
python -m maintainability.merge_cache -cache maintainability/cache -output maintainability/bch_cache.zip
``` 

How to collect maintainability results from BCH cache:

```
source venv/bin/activate
cd scripts
python report.py --report export -secdb ../dataset/db_security_changes.csv -regdb ../dataset/db_regular_changes_random.csv -baseline random -results ../results -cache maintainability/bch_cache.zip
``` 

Comparison between security and regular commits:

```
source venv/bin/activate
cd scripts
python report.py --report comparison -results ../results/ -reports ../reports
``` 

Get security maintainability report per guideline:

```
source venv/bin/activate
cd scripts
python report.py --report guideline -secdb ../results/maintainability_release_security_fixes.csv -reports ../reports
``` 

Get security maintainability report per language:

```
source venv/bin/activate
cd scripts
python report.py --report language -secdb ../results/maintainability_release_security_fixes.csv -reports ../reports
``` 

Get security maintainability report per severity:

```
source venv/bin/activate
cd scripts
python report.py --report severity -secdb ../results/maintainability_release_security_fixes.csv -reports ../reports
``` 

Get security maintainability report per cwe:

```
source venv/bin/activate
cd scripts
python report.py --report cwe -secdb ../results/maintainability_release_security_fixes.csv -reports ../reports
``` 

Get security maintainability report per specific cwe (available for CWE_664 and CWE_707):

```
source venv/bin/activate
cd scripts
python report.py --report cwe-spec -secdb ../results/maintainability_release_security_fixes.csv -cwe CWE_664 -reports ../reports
``` 




### Experiments

How to collect maintainability reports from BCH:

Create a config file in `scripts/maintainability/config.json` based on the example in `scripts/maintainability/config-template.json`.

```
virtualenv --python=python3.7 venv
source venv/bin/activate
pip install -r requirements.txt
cd scripts
python -m maintainability.eval_maintainability
```
