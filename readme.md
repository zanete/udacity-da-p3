# OpenStreetMap Data Wrangling Project
## Zanete Ence

This directory contains a set of scripts that audit and clean open street map XML data and turn it into a json format for MongoDB
It contains the following files:
* **map.txt**: contains the URL to the full download of OpenStreetMap XML for the area of Crawley, West Sussex, United Kingdom
* **crawley.osm**: a random sample of the original dataset
* Python scripts:
  * **audit.py**: Initial pass at the data set to confirm schema assumptions and produce an overview report
  * **audit_tags.py**: Secondary pass at the data with focus on contents of the tag elements, produces a csv with all key value pairs encountered
  * **clean.py**: Script that cleans and shapes the original XML data and transforms into json file containing list of map entities
If CODE RUN:
* **tag_audit_report.csv**: an export of all the key value pairs encountered and their count (_produced by audit_tags.py_)
* **clean_data.json**: an export of map entities in json format (_produced by clean.py_)



### Libraries used:
* xml
* pprint
* pandas
