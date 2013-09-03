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

# Lists the Keyspaces of the current cassandra instance
def get_details(system):
    ksprops = system.get_keyspace_properties("system").keys()
    header = ["keyspace"] + sorted(ksprops)
    writer = csv.writer(output)
    writer.writer.writerow(header)

    for keyspace in system.list_keyspaces():
        ksinfo = system.get_keyspace_column_families(keyspace, use_dict_for_col_metadata=True)
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

        for cfname, cfdef in ksinfo.iteritems():
            ks = ("keyspace="+ keyspace)
            cf = ("column_family="+ cfname)
            row =(ks, cf)
            writer.writerow(row)

def main(argv):
    usage = "Usage: dbdiscover.py"
    
    args, kwargs = parse(argv)

    host = kwargs.get('host', settings.DEFAULT_CASSANDRA_HOST)
    port = kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT)

    try:
        system = SystemManager("%s:%s" % (host, port))
        ksprops = system.get_keyspace_properties("system").keys()
#        header = ["keyspace"] + sorted(ksprops)
        header = ["keyspace", "column_family"]
        writer = csv.writer(output)
        writer.writerow(header)

        for keyspace in system.list_keyspaces():
            ksinfo = system.get_keyspace_column_families(keyspace, use_dict_for_col_metadata=True)
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

            for cfname, cfdef in ksinfo.iteritems():
                ks = ("keyspace="+ keyspace)
                cf = ("column_family="+ cfname)
                row =(ks, cf)
                writer.writerow(row)


        return

    except:
        error(output, excinfo(), 2)

if __name__ == "__main__":
    main(sys.argv[1:])
    
