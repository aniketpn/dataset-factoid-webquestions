#!/usr/bin/python3
#
# Creates dataset of freebase mids generated from question concepts
#
# Usage: freebase_mids.py $split
#
# Loads question analysis results from d-dump (typically generated by
# YodaQA) and generates d-freebase-mids/ data that contains for each
# question a set of (label, mid) tuples of referenced concepts/entities.
# In addition, freebaseKey d-freebase annotations are also used (as the
# YodaQA entity linking is quite imperfect).

from __future__ import print_function

import datalib
from SPARQLWrapper import SPARQLWrapper, JSON
import sys


def queryPageID(page_id):
    url = 'http://freebase.ailao.eu:3030/freebase/query'
    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    sparql_query = '''
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ns: <http://rdf.freebase.com/ns/>
SELECT * WHERE {
  ?topic <http://rdf.freebase.com/key/wikipedia.en_id> "''' + page_id + '''" .
} '''
    sparql.setQuery(sparql_query)
    res = sparql.query().convert()
    s = set()
    retVal = []
    for r in res['results']['bindings']:
        if (r['topic']['value'] not in s):
            retVal.append(r['topic']['value'][27:])
        s.add(r['topic']['value'])
    if (len(retVal) < 1):
        return ""
    else:
        return retVal[0]


def queryKey(key):
    url = 'http://freebase.ailao.eu:3030/freebase/query'
    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    sparql_query = '''
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX ns: <http://rdf.freebase.com/ns/>

SELECT ?topic ?label WHERE {
  ?topic <http://rdf.freebase.com/key/en> "''' + key + '''" .
  ?topic rdfs:label ?label .
  FILTER( LANGMATCHES(LANG(?label), "en") )
} '''
    sparql.setQuery(sparql_query)
    res = sparql.query().convert()
    s = set()
    retVal = []
    for r in res['results']['bindings']:
        if (r['topic']['value'] not in s):
            keyPair = {'concept': r['label']['value'], 'mid': r['topic']['value'][27:]}
            retVal.append(keyPair)
        s.add(r['topic']['value'])

    if (len(retVal) < 1):
        return {}
    else:
        return retVal[0]


if __name__ == "__main__":
    split = sys.argv[1]
    data = datalib.load_multi_data(split, ['main', 'd-dump', 'd-freebase'])

    qmids = []
    for q in data.to_list():
        res_line = {}
        res_line['qId'] = q['qId']
        res_line['freebaseMids'] = []

        for c in q['Concept']:
            print('%s (%s) ? %s / %s' % (q['qId'], q['qText'], c['fullLabel'], c['pageID']), file=sys.stderr)
            pair = {}
            pair['concept'] = c['fullLabel']
            pair['mid'] = queryPageID(c['pageID'])
            pair['pageID'] = c['pageID']
            res_line['freebaseMids'].append(pair)

        if 'freebaseKey' in q:
            print('%s (%s) key %s' % (q['qId'], q['qText'], q['freebaseKey']), file=sys.stderr)
            keyPair = queryKey(q['freebaseKey'])
            if keyPair['mid'] not in [p['mid'] for p in res_line['freebaseMids']]:
                res_line['freebaseMids'].append(keyPair)

        # print (json.dumps(res_line))
        qmids.append(res_line)

    with open('d-freebase-mids/%s.json' % (split,), 'w') as f:
        datalib.save_json(qmids, f)
