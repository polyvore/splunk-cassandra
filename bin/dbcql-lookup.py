#!/usr/bin/env python
#
# Copyright 2011 Splunk, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import csv
import sys, re

from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import dict_factory

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

def get_csv_input():
    lines = []
    for line in sys.stdin:
        if line == "\n":
            break
    
    return csv.DictReader(sys.stdin)

def row_fully_populated(dictrow):
    for v in dictrow.values():
        if v is None:
            return False
    return True

def convert(value):
    """
    Tries to convert string-formatted numbers to integers or
    floats directly
    """
    if isinstance(value, str):
        if value.isdigit():
            return int(value)
        elif re.match(r'^\d+[,\.]\d+$', value):
            return float(value)
    return value

def key_combo(keys, dictrow):
    keycombo = []
    for k in keys:
        if k in dictrow:
            keycombo.append(convert(dictrow[k]))
        else:
            raise("Key %s is missing in input row %s" % (k, dictrow))
    return keycombo

def main(argv):
    usage = "Usage: dblookup [options] {keyspace.table} {key1,key2} {include col1, include col2}"

    args, kwargs = parse(argv)

    hosts = kwargs.get('hosts', settings.DEFAULT_CASSANDRA_HOSTS)
    if type(hosts) is str:
        hosts = hosts.split(',')
    port = kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT)
    batchsize = kwargs.get('batchsize', settings.DEFAULT_BATCHSIZE)

    if not port.isdigit():
        error(output, "Invalid port", 2)
    port = int(port)

    if not batchsize.isdigit() or int(batchsize) < 1:
        error(output, "Invalid batchsize", 2)
    batchsize = int(batchsize)

    if len(args) < 3:
        error(output, usage, 2)

    cfpath, keycolumns, outcolumns = args
    keycolumns = keycolumns.split(',')
    outcolumns = outcolumns.split(',')
    #print("Key columns: %s" % keycolumns)
    cfpath = cfpath.split('.')
    if len(cfpath) != 2:
        error(output, "Keyspace.table path should consist of 2 elements", 2)
    ksname, cfname = cfpath
    lookup = None
    reader = None
    csvheader = None
    try:
        reader = get_csv_input()
        csvheader = reader.fieldnames
        #TODO: Make the protocol version cluster-dependent
        cluster = Cluster(
                hosts,
                port = port,
                protocol_version = 1
            )
        #print("Connecting to cassandra")
        session = cluster.connect(ksname)
        session.row_factory = dict_factory
        query = "SELECT %s FROM %s.%s WHERE" % (
                                                ', '.join(set(keycolumns + outcolumns)),
                                                ksname,
                                                cfname
                                               )
        fcnt = 0
        for field in keycolumns:
            if not field in csvheader:
                error(output, "Key lookup field %s is missing in input data" % field)
            fcnt += 1
            if fcnt > 1:
                query += " AND"
            query += " %s=?" % field
        #print("Preparing Cassandra lookup query: %s" % query)
        lookup = session.prepare(query)
        #TODO: Consistency level should be part of per-cluster config
        lookup.consistency_level = ConsistencyLevel.LOCAL_QUORUM
    except:
        error(output, excinfo(), 2)

    writer = csv.DictWriter(output, set(keycolumns + outcolumns))
    writer.writeheader()

    unique_key_combos = {}
    while True:
        # Read up to `batchsize` rows and build key list for batch lookup
        row = {}
        try:
            row = reader.next()
        except StopIteration:
            break
        #print("Got input row: %s" % row)
        keycombo = key_combo(keycolumns, row)
        keysig = '-'.join(str(keycombo))
        if not keysig in unique_key_combos:
            # a new key combination
            #print("db fetch")
            values = session.execute(lookup, keycombo)
            unique_key_combos[keysig] = values
        if len(unique_key_combos[keysig]) > 0:
            for result in unique_key_combos[keysig]:
                row.update(result)
                writer.writerow(row)
        else:
            writer.writerow(row)

if __name__ == "__main__":
    main(sys.argv[1:])


