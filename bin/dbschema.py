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

"""A custom search command that presents metadata for a Cassandra instance."""

# UNDONE: Support for optional host/port command line args

import csv
import sys

from pycassa.system_manager import SystemManager

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

# Lists the schema of the given (keyspace, column_family)
def list_column_family(system, ksname, cfname):
    ksinfo = system.get_keyspace_column_families(
        ksname, use_dict_for_col_metadata=True)
    cfinfo = ksinfo[cfname].column_metadata

    attrs = [
        "name",
        "index_name",
        "index_type",
        "validation_class"
    ]
    header = ["keyspace", "column_family"] + attrs
    writer = csv.DictWriter(output, header)
    writer.writer.writerow(header)

    for _, cdef in cfinfo.iteritems():
        row = {'keyspace': ksname, 'column_family': cfname}
        for attr in attrs:
            row[attr] = getattr(cdef, attr)
        writer.writerow(row)

# Lists the contents of the given keyspace
def list_keyspace(system, ksname):
    ksinfo = system.get_keyspace_column_families(
        ksname, use_dict_for_col_metadata=True)

    attrs = [
        "id",
        "column_type",
        "comment",
        "comparator_type",
        "default_validation_class",
        "gc_grace_seconds",
        "key_alias",
        "key_cache_save_period_in_seconds",
        "key_cache_size",
        "key_validation_class",
        "max_compaction_threshold",
        "memtable_operations_in_millions",
        "memtable_throughput_in_mb",
        "memtable_flush_after_mins",
        "merge_shards_chance",
        "min_compaction_threshold",
        "read_repair_chance",
        "replicate_on_write",
        "row_cache_provider",
        "row_cache_save_period_in_seconds",
        "row_cache_size",
        "subcomparator_type",
    ]
    header = ["keyspace", "column_family"] + attrs
    writer = csv.DictWriter(output, header)
    writer.writer.writerow(header)

    for cfname, cfdef in ksinfo.iteritems():
        row = { 'keyspace': ksname, 'column_family': cfname }
        for attr in attrs:
            row[attr] = getattr(cfdef, attr)
        writer.writerow(row)

# Lists the contents of the current cassandra instance
def list_keyspaces(system):
    ksprops = system.get_keyspace_properties("system").keys()
    header = ["keyspace"] + sorted(ksprops)
    writer = csv.DictWriter(output, header)
    writer.writer.writerow(header)
    for keyspace in system.list_keyspaces():
        row = system.get_keyspace_properties(keyspace)
        row['keyspace'] = keyspace
        writer.writerow(row)

def main(argv):
    usage = "Usage: dbschema [options] [{resource}]"

    args, kwargs = parse(argv)

    host = kwargs.get('host', settings.DEFAULT_CASSANDRA_HOST)
    port = kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT)

    try:
        system = SystemManager("%s:%s" % (host, port))

#  FOR TESTING ONLY
#        print str(argv)
        
        if len(argv) == 0:
            list_keyspaces(system)
            return

        if len(argv) == 1:
            ksname = argv[0]
            list_keyspace(system, ksname)

        if len(argv) == 2:
            ksname = argv[0]
            cfname = argv[1]
            if cfname != 'ANY':
                list_column_family(system, ksname, cfname)
            else:
                list_keyspace(system, ksname)

    except:
        error(output, excinfo(), 2)

if __name__ == "__main__":
    main(sys.argv[1:])
    
