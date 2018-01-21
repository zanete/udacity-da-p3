#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import pprint
import pandas as pd

DATA_FILE = 'crawley.osm'
SUPPORTED_ELEMS = ['node', 'way', 'relation']

def main():
    """
    Produces a report of all keys and values encountered by parent element and how often
    """
    tag_data = []
    for _, element in ET.iterparse(DATA_FILE):
        if element.tag in SUPPORTED_ELEMS:
            for tag in [child for child in element if child.tag == 'tag']:
                tag_data.append({
                    'parent': element.tag,
                    'parent_id': element.get('id'),
                    'key': tag.get('k').encode('utf8'),
                    'value': tag.get('v').encode('utf8')
                })
    # create a data frame of all key values
    tag_data_df = pd.DataFrame(tag_data)

    # how many unique keys
    key_grouping_df = (
        tag_data_df
        .groupby(by='key')
        .agg({'value': 'count'})
        .sort_values(by='value', ascending=False)
    )
    
    print "Unique keys: " + str(len(key_grouping_df))
    print "Most Frequent Key: " + str(key_grouping_df.iloc[0].name)
    pprint.pprint(key_grouping_df.head(10))

    # key value pairs
    key_value_grouping_df = (
        tag_data_df
        .groupby(by=['parent', 'key', 'value'])
        .count()
        .sort_values(by='parent_id', ascending=False)
        .rename(columns={'parent_id': 'count'})
    )

    print "Unique key-value pairs: " + str(len(key_value_grouping_df))
    print "Most Frequent Key-value pair: " + str(key_value_grouping_df.iloc[0].name)
    pprint.pprint(key_value_grouping_df.head(10))

    print "Total count: " + str(len(tag_data))

    key_value_grouping_df.to_csv("tag_audit_report.csv")

if "__main__" == __name__:
    main()