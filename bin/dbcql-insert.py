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

from cassandra.cluster import Cluster

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

def convert(row):
    """
    Perform any needed data type conversions on the given row (dict).

    This is necessary because python csv module does not intepret type,
    so our integers/floats on sys.stdin become strings.
    """

    for k,v in row.iteritems():
        if isinstance(v, str):
            if v.isdigit():
                row[k] = int(v)
            elif re.match(r'^\d+[,\.]\d+$', v):
                row[k] = float(v)
    return row
# End convert

def main(argv):
    usage = "Usage: dbinsert [options] {cfpath} {key} {fields}"

    args, kwargs = parse(argv)

    hosts = kwargs.get('hosts', settings.DEFAULT_CASSANDRA_HOSTS)
    if type(hosts) is str:
        hosts = hosts.split(',')
    port = kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT)
    ttl = int(kwargs.get('ttl', None))
    batchsize = kwargs.get('batchsize', settings.DEFAULT_BATCHSIZE)

    if not port.isdigit():
        error(output, "Invalid port", 2)
    port = int(port)

    if not batchsize.isdigit() or int(batchsize) < 1:
        error(output, "Invalid batchsize", 2)
    batchsize = int(batchsize)

    if len(args) != 3: 
        error(output, usage, 2)

    cfpath, keycol, fields = args
    fields = fields.split(',')
    cfpath = cfpath.split('.', 1)
    if len(cfpath) != 2: 
        error(output, "Invalid column family path", 2)
    ksname, cfname = cfpath

    # NOTE: Cassandra driver docs say that when using protocol version 1,
    # protocol-level batch operations aren't available. Awooo... ;_;
    # http://planetcassandra.org/blog/datastax-python-driver-2-0-released/
    # http://datastax.github.io/python-driver/api/cassandra/cluster.html
    try:
        cluster = Cluster(
            hosts,
            port=port,
            protocol_version = 1 # TODO: Option for protocol version
        )
        session = cluster.connect(ksname)
    except:
        error(output, excinfo(), 2)

    for line in sys.stdin:
        # NOTE: This discards the splunk-related job info that is
        # sent to the script prior to the actual header that
        # we're interested in.
        #
        # Doing this will break compatibility with running this
        # from the CLI, unless you prepend a newline character
        # to your input.
        if line == '\n': break

    reader = csv.DictReader(sys.stdin)
    header = reader.fieldnames

    # Make sure the key field exists
    if keycol not in header:
        error(output, "Key field '%s' not found" % keycol, 2)

    # Make sure the fields we are inserting exist in the input stream
    for field in fields:
        if field not in header:
            error(output, "Field '%s' not found" % field, 2)

    writer = csv.DictWriter(output, header)
    writer.writer.writerow(header)

    for row in reader:
        record = dict([(k, v) for k, v in row.iteritems() if k in fields])
        # Cast strings that are integers to int
        record = convert(record)

        # Build an insert statement that we can use a dictionary with
        query = 'INSERT INTO %s (%s) ' % (cfname, ', '.join(record.keys()))
        values_string = ', '.join(['%(' + col + ')s' for col in record.keys()])
        query += 'VALUES (%s)' % values_string
        # Add TTL, if one was given
        if ttl:
            query += ' USING TTL %d' % ttl

        session.execute(query, record)
        writer.writerow(row)

if __name__ == "__main__":
    main(sys.argv[1:])

