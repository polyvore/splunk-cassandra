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
import pycassa

from cassandra.cluster import Cluster
from cassandra.query import dict_factory

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

def main(argv):
    usage = "Usage: dbgetkeys [{Keyspace, Column_Family}]"

    args, kwargs = parse(argv)

    hosts = kwargs.get('hosts', settings.DEFAULT_CASSANDRA_HOSTS)
    if type(hosts) is str:
        hosts = hosts.split(',')
    port = int(kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT))

    if len(argv) == 2:
        ksname = argv[0]
        cfname = argv[1]

    try:
        cluster = Cluster(
            hosts,
            port=port,
            protocol_version = 1 # TODO: Option for protocol version
        )
        session = cluster.connect(ksname)
        session.row_factory = dict_factory

    except:
        error(output, excinfo(), 2)

    # Get All Keys for given cf
    header = None
    writer = None
    rows = session.execute('select * from %s' % '.'.join([ksname, cfname]))

    for row in rows:
        if not header:
            header = row.keys()
            writer = csv.DictWriter(output, header)
            writer.writeheader()
        writer.writerow(row)

if __name__ == "__main__":
    main(sys.argv[1:])
    
