#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
from collections import defaultdict
import pprint

"""
Initial pass at the data set to confirm the following assumptions:

- There are 3 types of main elements: *nodes*, *ways* and *relations*
- All of these have a set of mandatory attributes, for brevity I’ll focus on a set of these:
    *id* - always numeric, int, e.g. 527862206
    *uid* - always numeric, e.g 19799
    *user* - text, e.g. tilsch
    *timestamp* - timestamp "2008-02-09T11:34:42Z"
- *nodes* have an additional couple of mandatory attributes:
    *lat* - always numeric, float, e.g. 51.1323794
    *lon* - always numeric, float, e.g. -0.1598410
- All main elements have a child element *tag* with two mandatory attributes:
    *k* - any value, e.g. highway
    *v* - any value, e.g. crossing
- *ways* must have at least a couple of child nd elements with one mandatory attribute:
    *ref* - always numeric, reference to an existing node, e.g. 4214523323
- *relations* must have at least a couple of child member elements with three mandatory attributes:
    *ref* - always numeric, reference to an existing node, e.g. 4350382290
    *role* - text, can be blank, e.g. stop
    *type* - text, one of [node, way, relation], e.g. way

Compiles a report of any instances where the above is not the case
Also returns the number of elements by type
"""

DATA_FILE = 'crawley.osm'
SUPPORTED_ELEMS = ['node', 'way', 'relation']
SUPPORTED_SUBELEMS = ['tag', 'nd', 'member']

# initialise audit report
audit_report = { tag_name: { 'count':0, 'errors':[] } for tag_name in (SUPPORTED_ELEMS + SUPPORTED_SUBELEMS)}
audit_report["unsuported_elements"] = defaultdict(lambda: 0)

def is_node_valid(element):
    """
    Checks that nodes have an additional couple of mandatory attributes:
    *lat* - always numeric, float, e.g. 51.1323794
    *lon* - always numeric, float, e.g. -0.1598410

    returns a list of error messages
    """
    res = []
    lat = element.get('lat')
    if not lat:
        res.append("No lat attribute in node " + str(element.get('id')))
    else:
        try:
            float(lat)
        except ValueError:
            res.append("Non-numeric lat: " + lat + " in node " + str(element.get('id')))

    lon = element.get('lon')
    if not lon:
        res.append("No lon attribute in node " + str(element.get('id')))
    else:
        try:
            float(lon)
        except ValueError:
            res.append("Non-numeric lon: " + lon + " in node " + str(element.get('id')))
    return res

def is_way_valid(element):

    """
    Check that at least a couple of child nd elements with one mandatory *ref* - always numeric, reference to an existing node, e.g. 4214523323

    returns a list of error messages
    """
    res = []

    #get all nd elems
    children = [child for child in element if child.tag == 'nd']
    
    # check that at least 2 are present
    if len(children) < 2:
        res.append("Not enough nd elements within way " + str(element.get('id')))

    # check that all have a valid ref
    for child in children:
        if not child.get('ref'):
            res.append("No ref attribute in way " + str(element.get('id')))
        elif not child.get('ref').isdigit():
            res.append("Non-numeric ref attribute for nd in way " + str(element.get('id')))

    return res

def is_relation_valid(element):
    """
    at least a couple of child member elements with three mandatory attributes:
    *ref* - always numeric, reference to an existing node, e.g. 4350382290
    *role* - text, can be blank, e.g. stop
    *type* - text, one of [node, way, relation], e.g. way

    returns a list of error messages
    """
    res = []

    children = [child for child in element if child.tag == 'member']

    # check that at least 2 are present
    if len(children) < 2:
        res.append("Not enough member elements within relation " + str(element.get('id')))

    for child in children:
        # check that all have a valid ref
        if not child.get('ref'):
            res.append("No ref attribute in relation")
        elif not child.get('ref').isdigit():
            res.append("Non-numeric ref attribute for member in relation " + str(element.get('id')))

        # check that all have a role
        if child.get('role') == None:
            res.append("No role attribute in relation " + str(element.get('id')))

        # check that all have a valid type
        if not child.get('type'):
            res.append("No type attribute in relation " + str(element.get('id')))
        elif child.get('type') not in SUPPORTED_ELEMS:
            res.append("Member type unrecognised value: " + child.get('type') + " in relation " + str(element.get('id')))

    return res

def is_tag_valid(element):
    """
    check that tag has two mandatory attributes:
    *k* - any value, e.g. highway
    *v* - any value, e.g. crossing

    returns a list of error messages 
    """
    res = []
    if not element.get('k'):
        res.append("No k attribute for tag")

    if not element.get('v'):
        res.append("No v attribute for tag")

    return res

def are_main_attributes_valid(element):
    """
    Check that top elements have valid main attributes
    *id* - always numeric, int, e.g. 527862206
    *uid* - always numeric, e.g 19799
    *user* - text, e.g. tilsch
    *timestamp* - timestamp "2008-02-09T11:34:42Z"

    return a list of error messages
    """
    res = []
    attrib_dict = { attribk:attribv for (attribk, attribv) in element.items()}

    if 'id' not in attrib_dict:
        res.append("No id attribute in " + element.tag)
    elif not attrib_dict['id'].isdigit():
        res.append("Non-numeric id:" + attrib_dict['id'])

    if 'uid' not in attrib_dict:
        res.append("No uid attribute in " + element.tag)
    elif not attrib_dict['uid'].isdigit():
        res.append("Non-numeric uid:" + attrib_dict['uid'])

    if 'user' not in attrib_dict:
        res.append("No user attribute in " + element.tag)
    elif not attrib_dict['user']:
        res.append("No value for user attribute in " + element.tag)

    if 'timestamp' not in attrib_dict:
        res.append("No timestamp attribute in " + element.tag)
    elif not attrib_dict['timestamp']:
        # todo - check valid timestamp
        res.append("No value for timestamp attribute in " + element.tag)

    return res

def audit_element(element):
    global audit_report
    tag_name = element.tag
    
    if tag_name in SUPPORTED_ELEMS:
        audit_report[tag_name]['errors'].extend(are_main_attributes_valid(element))
        exec("errors = is_"+tag_name+"_valid(element)")
        audit_report[tag_name]['errors'].extend(errors)
        audit_report[tag_name]['count']+=1
    elif tag_name in SUPPORTED_SUBELEMS:
        try:
            exec("errors = is_"+tag_name+"_valid(element)")
            audit_report[tag_name]['errors'].extend(errors)
        except:
            pass
        audit_report[tag_name]['count']+=1
    else:
        audit_report['unsuported_elements'][tag_name] +=1

def main():
    global audit_report
    counter = 0
    for _, element in ET.iterparse(DATA_FILE):
        audit_element(element)
        counter += 1

    pprint.pprint(audit_report)
    print "Total count: " + str(counter)

if "__main__" == __name__:
    main()