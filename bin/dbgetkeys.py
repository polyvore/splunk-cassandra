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
import pycassa

from pycassa.system_manager import SystemManager

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

def main(argv):
    usage = "Usage: dbgetkeys [{Keyspace, Column_Family}]"

    args, kwargs = parse(argv)

    host = kwargs.get('host', settings.DEFAULT_CASSANDRA_HOST)
    port = kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT)

    if len(argv) == 2:
        ksname = argv[0]
        cfname = argv[1]

    try:
        server = "%s:%s" % (host, port)
        pool = pycassa.connect(ksname, [server])
        cfam = pycassa.ColumnFamily(pool, cfname)
    except pycassa.cassandra.c08.ttypes.InvalidRequestException, e:
        error(output, e.why, 2)
    except pycassa.cassandra.c08.ttypes.NotFoundException, e:
        error(output, e.why, 2)
    except:
        error(output, excinfo(), 2)

    # Get All Keys for given cf

    header = ["Keyspace","Column_Family","Key"]
    writer = csv.writer(output)
    writer.writerow(header)
    ks = ("keyspace="+ ksname)
    cf = ("column_family="+ cfname)

    for value in cfam.get_range(column_count=0):
         key = ("Key="+ value[0])
         row = (ks, cf, key)
         writer.writerow(row)

if __name__ == "__main__":
    main(sys.argv[1:])
    
