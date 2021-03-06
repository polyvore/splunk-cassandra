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

# UNDONE: Support for optional hosts/port command line args

import csv
import sys

from cassandra.cluster import Cluster
from cassandra.query import dict_factory
from cassandra import ConsistencyLevel

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

def main(argv):
    usage = "Usage: dbdiscover.py"
    
    args, kwargs = parse(argv)

    hosts = kwargs.get('hosts', settings.DEFAULT_CASSANDRA_HOSTS)
    if type(hosts) is str:
        hosts = hosts.split(',')
    port = int(kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT))
    protocol = int(kwargs.get('protocol', settings.DEFAULT_PROTOCOL_VERSION))

    try:
        cluster = Cluster(
            hosts,
            port=port,
            protocol_version = protocol
        )
        session = cluster.connect()
        session.row_factory = dict_factory

        # Get keyspaces
        rows = session.execute('select keyspace_name from system.schema_keyspaces')
        keyspaces = [x['keyspace_name'] for x in rows]

        header = ["keyspace", "column_family"]
        writer = csv.writer(output)
        writer.writerow(header)

        # Prepared statement for column family names in keyspace
        column_families = session.prepare("select columnfamily_name from system.schema_columnfamilies where keyspace_name=?")
        # TODO: Option for setting consistency level
        column_families.consistency_level = ConsistencyLevel.LOCAL_QUORUM

        for keyspace in keyspaces:
            rows = session.execute(column_families, [keyspace])
            names = [x['columnfamily_name'] for x in rows]

            for cfname in names:
                ks = ("keyspace="+ keyspace)
                cf = ("column_family="+ cfname)
                row =(ks, cf)
                writer.writerow(row)
        return

    except:
        error(output, excinfo(), 2)

if __name__ == "__main__":
    main(sys.argv[1:])
    
