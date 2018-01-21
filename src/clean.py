#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.cElementTree as ET
import re
import datetime
import pprint
import json

DATA_FILE = 'crawley.osm'
SUPPORTED_ELEMS = ['node', 'way', 'relation']

# when encountered - cast value to number
NUMBERS = ['admin_level', 'building:levels', 'building:min_level', 'cables', 'capacity', 'capacity:disabled', 'circuits', 'cyclestreets_id',
    'frequency', 'interval', 'lanes', 'layer', 'level', 'max_age', 'min_age', 'passenger_lines', 'rooms', 'seats', 'step_count', 'voltage']

# when encountered - convert to corresponding unit and cast as number
LENGTHS = ['width', 'maxwidth', 'est_width', 'circumference', 'height', 'maxheight', 'maxheight:physical', 'length'] # km, cm, m or inches - convert to m, if none, assume m
WEIGHTS = ['maxweight'] # T - if none - assume T
SPEEDS = ['maxspeed'] # mph or kmh - convert to mph, if none - assume mph

#when encountered - 
TIMES = ['opening_date', 'survey:date','start_date']

# when encountered - rename
KEY_MAPPINGS = {
    'addr:door': 'address:door',
    'addr:unit': 'address:unit',
    'addr:unitnumber': 'address:unit',
    'addr:alternate': 'address:alternate',
    'addr:place': 'address:place',
    'addr:street_1': 'address:place',
    'rooms': 'address:rooms',
    'addr:flats': 'address:flats',
    'addr:flat': 'address:flats',
    'addr:flatnumber': 'address:flats',
    'addr:floor': 'address:floor',
    'addr:housename' : 'address:housename',
    'housenumber': 'address:housenumber',
    'addr:housenumber' :'address:housenumber',
    'addr:buildingnumber': 'address:housenumber',
    'addr:street' : 'address:street',
    'street' : 'address:street',
    'addr:district' : 'address:district',
    'is_in': 'address:city', # needs removing West Sussex, England, UK
    'is_in:district': 'address:district',
    'addr:suburb': 'address:suburb',
    'is_in:city': 'address:city',
    'addr:city': 'address:city', 
    'addr:state': 'address:county',
    'addr:postcode': 'address:postcode',
    'postal_code': 'address:postcode',
    'addr:postcode_alt':'address:postcode',
    'addr:postcode:alt': 'address:postcode',
    'addr:country': 'address:country', #should all be GB!
    'addr:interpolation': 'address:interpolation',
    'addr:inclusion': 'address:inclusion',
    'addr:in': 'address:in',
    'addr:accessvia': 'address: accessvia',
    'addr:full': 'address:full',

    'contact:email': 'contact:email',
    'email': 'contact:email',
    'contact:phone': 'contact:phone',
    'phone':'contact:phone',
    'address:phone': 'contact:phone',
    'fax': 'contact:fax',
    'contact:fax': 'contact:fax',
    'contact:website': 'contact:website',
    'website': 'contact:website',
    'url': 'contact:website',
    'uri': 'contact:website',
    'contact:google_plus': 'contact:google_plus',
    'facebook': 'contact:facebook',
    'flickr': 'contact:flickr',
    'twitter': 'contact:twitter'
}

NAMESPACED = re.compile(r'^([a-zA-Z]|_)*:([a-zA-Z:]|_)*$')

def get_number(raw_val):
    """
    Transform a numeric string value into number
    """
    ret_val = raw_val.strip()
    # remove thousand separator
    if ',' in ret_val:
        ret_val = ret_val.replace(',', '')
    try:
        ret_val = int(ret_val)
    except:
        try:
            ret_val = float(ret_val)
        except Exception as e:
            print e
    return ret_val

def get_length_in_meters(raw_val):
    """
    Transform a length measurement into numeric meter value
    """
    ret_val = raw_val.strip()
    imperical = False
    if '"' in ret_val:
        imperical = True
        ret_val = raw_val.replace('"', '').strip()
    elif 'ft' in ret_val:
        imperical = True
        ret_val = raw_val.replace('ft', '').strip()
    elif 'feet' in ret_val:
        imperical = True
        ret_val = raw_val.replace('feet', '').strip()
    elif "'" in ret_val:
        imperical = True
        #if ends with ', add 0, e.g. 10', 7' etc
        if "'" == ret_val[-1]:
            ret_val = ret_val + '0'
    
    if imperical:
        if "'" in ret_val: # convert from inches to meters!
            height_parts = ret_val.split("'")
            if 2 == len(height_parts):
                try:
                    foot_part = int(height_parts[0])
                    inch_part = int(height_parts[1])
                    # 1 foot = 0.3048 metres
                    # 1 inch = 0.0254 metres
                    ret_val = inch_part * 0.0254 + foot_part * 0.3048
                except Exception as e:
                    print e
                    print raw_val
        elif '.' in ret_val:
            try:
                ret_val = float(ret_val) * 0.3048
            except Exception as e:
                print e
                print raw_val

    else:
        # replace any ',' with '.'
        if ',' in raw_val:
            raw_val = raw_val.replace(',', '.')

        if 'cm' in raw_val:
            ret_val_in_cm = raw_val.replace('cm', '').strip()
            try:
                ret_val_in_cm = float(ret_val_in_cm)
                ret_val = ret_val_in_cm / 100
            except Exception as e:
                print e
                print raw_val
        if 'km' in raw_val:
            ret_val_in_km = raw_val.replace('km', '').strip()
            try:
                ret_val_in_km = float(ret_val_in_km)
                ret_val = ret_val_in_km * 1000
            except Exception as e:
                print e
                print raw_val
        elif 'm' in raw_val:
            ret_val = raw_val.replace('m', '').strip()

        try:
            ret_val = float(ret_val)
        except Exception as e:
            print e
            print raw_val

    return ret_val

def get_weight_in_tons(raw_val):
    """
    Transform a weight measurement into numeric ton value
    """
    ret_val = raw_val.strip()
    if 'T' in raw_val:
        ret_val = raw_val.replace('T', '').strip()
    try:
        ret_val = float(ret_val)
    except Exception as e:
        print e
    return ret_val

def get_speed_in_mph(raw_val):
    """
    Transform a speed measurement into numeric mph value
    """
    ret_val = raw_val.strip()
    if 'mph' in raw_val:
        ret_val = raw_val.replace('mph', '').strip()
    try:
        ret_val = float(ret_val)
    except Exception as e:
        print e
    return ret_val

def get_time(raw_val):
    """
    Transform a date or time string into datetime value
    """
    ret_val = raw_val.strip()
    val_length = len(ret_val)
    if 4 == val_length: # just year
        try:
            ret_val_year = int(ret_val)
            ret_val = datetime.datetime(ret_val_year, 1, 1)
        except Exception as e:
            print e

    elif 7 == val_length:
        date_parts = ret_val.split('-')
        if 2 == len(date_parts):
            if 4 == len(date_parts[0]): # yyyy first
                try:
                    ret_val = datetime.datetime.strptime(ret_val, '%Y-%m')
                except Exception as e:
                    print e
            elif 2 == len(date_parts[0]): # dd first
                try:
                    ret_val = datetime.datetime.strptime(ret_val, '%m-%Y')
                except Exception as e:
                    print e
    elif 10 == val_length: # yyyy-mm-dd or dd-mm-yyyy
        date_parts = raw_val.split('-')
        if 3 == len(date_parts):
            if 4 == len(date_parts[0]): # yyyy first
                try:
                    ret_val = datetime.datetime.strptime(ret_val, '%Y-%m-%d')
                except Exception as e:
                    print e
            elif 2 == len(date_parts[0]): # dd first
                try:
                    ret_val = datetime.datetime.strptime(ret_val, '%d-%m-%Y')
                except Exception as e:
                    print e
        else:
            # try //
            try:
                ret_val = datetime.datetime.strptime(ret_val, '%d/%m/%Y')
            except Exception as e:
                print e

    else:
        # try full months
        try:
            ret_val = datetime.datetime.strptime(ret_val, '%d %B %Y')
        except Exception as e:
            print e
            try:
                ret_val = datetime.datetime.strptime(raw_val, '%B %Y')
            except Exception as e:
                print e

    return ret_val.isoformat()

def shape_element(element):
    """
    Handle main map XML element tranformation to json object
    Returns a json representation of the element
    """

    # main attributes
    json_el = {
        "element_type": element.tag,
        "_id": element.get('id'),
        "user": element.get('user'),
        "uid": element.get('uid')    
    }

    #timestamp 
    try:
        json_el["created"] = datetime.datetime.strptime(element.get('timestamp'), '%Y-%m-%dT%H:%M:%SZ').isoformat()
    except Exception as e:
        print e

    if 'node' == element.tag:
        # lat
        json_el["lat"] = get_number(element.get('lat'))
        json_el["lon"] = get_number(element.get('lon'))

    # append all node references if the element is way
    if 'way' == element.tag:
        json_el["nodes"] = []
        for nd in [nd for nd in element if nd.tag == 'nd']:
            json_el["nodes"].append(nd.get('ref'))
    
    # append all members if element is relation
    if 'relation' == element.tag:
        json_el["members"] = []
        for member in [member for member in element if member.tag == 'member']:
            json_el["members"].append({
                member.get('type'): member.get('ref'),
                "role": member.get('role')
            })
    
    # get all tags
    k_v_temp_store = {}
    for tag in [tag for tag in element if tag.tag == 'tag']:
        k_v_temp_store[tag.get('k').lower()] = tag.get('v')

    # handle tags
    k_v_store = {}
    for key, value in k_v_temp_store.iteritems():
        if key in KEY_MAPPINGS:
            key = KEY_MAPPINGS[key]

        # handle lists
        if ';' in value:
            values = value.split(';')
        else:
            values = [value]

        # clean values
        output_vals = []
        for val in values:
            if key in TIMES:
                val = get_time(val)
            elif key in LENGTHS:
                val = get_length_in_meters(val)
            elif key in SPEEDS:
                val = get_speed_in_mph(val)
            elif key in NUMBERS:
                val = get_number(val)
            elif val.lower() in ['no', 'yes']:
                if val.lower() == 'yes':
                    val = True
                else:
                    val = False
        
            output_vals.append(val)

        # handle namespace
        namespace_present = NAMESPACED.search(key)
        if namespace_present:
            namespace_parts = key.split(':')
            main_key, sub_key = (namespace_parts[0], namespace_parts[1])

            if main_key in k_v_store:
                if isinstance(k_v_store[main_key], dict):
                    if sub_key in k_v_store[main_key]:
                        k_v_store[main_key][sub_key].extend(output_vals)
                    else:
                        k_v_store[main_key][sub_key] = output_vals
                else:
                    tmp_vals = k_v_store[main_key]
                    k_v_store[main_key] = {
                        "value": tmp_vals,
                        sub_key: output_vals
                    }

            else:
                k_v_store[main_key] = {sub_key: output_vals}
        else:
            if key in k_v_store:
                pass
            else:
                k_v_store[key] = output_vals

    
    if k_v_store:
        #replace lists with 1 value to be just that value 
        final_k_v_store = {}
        for k, v in k_v_store.iteritems():
            if isinstance(v, dict):
                final_k_v_store[k] = {}
                for subk, subv in v.iteritems():
                    if len(subv) == 1:
                        final_k_v_store[k][subk] = subv[0]
                    else:
                        final_k_v_store[k][subk] = subv
            else:
                if len(v) == 1:
                    final_k_v_store[k] = v[0]
                else:
                    final_k_v_store[k] = v

        # add tag fields and values to the json element
        for k, v in final_k_v_store.iteritems():
            json_el[k] = v

    return json_el

def main():
    """
    Transforms XML elements in DATA_FILE into a list of JSON objects
    Produces json file containing transformed elements
    """
    elements = []
    elem_count = 0
    for _, element in ET.iterparse(DATA_FILE):
        if element.tag in SUPPORTED_ELEMS:
            doc = shape_element(element)
            elements.append(doc)
            elem_count += 1

    print "Total Elements cleaned and shaped: " + str(elem_count)
    
    with open('data.json', 'w') as outfile:
        json.dump(elements, outfile)

if __name__ == "__main__":
    main()