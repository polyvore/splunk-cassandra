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
    usage = "Usage: dblookup [options] {cfpath} {key}"

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

#    if len(args) < 2: 
#        error(output, usage, 2)

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

    if keycol not in header:
        error(output, "Key field '%s' not found" % keycol, 2)

    header.extend(fields)
    writer = csv.DictWriter(output, header)
    writer.writer.writerow(header)

    while True:
        # Read up to `batchsize` rows and build key list for batch lookup
        rows = []
        keys = []
        for i in xrange(batchsize):
            try:
                row = reader.next()
            except StopIteration:
                break
            key = str(row[keycol])
            keys.append(key)
            rows.append(row)

        if len(keys) == 0: 
            break # All done

        # Make a single multiget request for the batch of keys
        keyset = set(keys) # Remove dups
        values = cfam.multiget(keyset, columns=fields) 

        # Merge the resulting dictionary with the original rows
        for i in xrange(len(keys)):
            value = values.get(keys[i], None)
            if value is None: continue
            rows[i].update(convert(value))

        # Write extended rows back out in original order
        for row in rows:
            writer.writerow(row)

if __name__ == "__main__":
    main(sys.argv[1:])

