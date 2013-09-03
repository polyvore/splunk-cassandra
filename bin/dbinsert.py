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
import sys

import pycassa

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

# Perform any needed data type conversions on the given row (dict)
# UNDONE: Can we avoid the unicode to utf8 conversion below somehow?
def convert(row):
    for k,v in row.iteritems():
        if isinstance(v, unicode):  # UNDONE: Why????
            row[k] = v.encode("utf8")
    return row

def main(argv):
    usage = "Usage: dbinsert [options] {cfpath} {key} {fields}"

    args, kwargs = parse(argv)

    host = kwargs.get('host', settings.DEFAULT_CASSANDRA_HOST)
    port = kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT)
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
    cfpath = cfpath.split('.')
    if len(cfpath) != 2: 
        error(output, "Invalid column family path", 2)
    ksname, cfname = cfpath

    try:
        server = "%s:%d" % (host, port)
        pool = pycassa.connect(ksname, [server])
        cfam = pycassa.ColumnFamily(pool, cfname)
    except pycassa.cassandra.c08.ttypes.InvalidRequestException, e:
        error(output, e.why, 2)
    except pycassa.cassandra.c08.ttypes.NotFoundException, e:
        error(output, e.why, 2)
    except:
        error(output, excinfo(), 2)

    for line in sys.stdin:
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

    # The pycassa batch context manager will automatically transmit updates 
    # when `queue_size` is reached and when the context manager exits.
    with cfam.batch(queue_size=batchsize) as batch:
        for row in reader:
            key = row[keycol]
            record = dict([(k, v) for k, v in row.iteritems() if k in fields])
            batch.insert(key, record)
            writer.writerow(row)

if __name__ == "__main__":
    main(sys.argv[1:])

