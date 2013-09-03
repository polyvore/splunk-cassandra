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

from pprint import pprint

import csv
import re
import sys

import cql
import cql.cursor

import settings
from apputils import error, excinfo, Logger, parse

debug = False
output = Logger(__file__) if debug else sys.stdout

# Perform any needed data type conversions on the given row (list)
# UNDONE: Can we avoid the unicode to utf8 conversion below somehow?
def convert(row):
    for i in xrange(len(row)):
        item = row[i]
        if isinstance(item, unicode):
            row[i] = item.encode("utf8")
    return row

def normal(cursor, **kwargs):
    """Output the results of a 'regular' query, consisting of either a
       rectangular result set or scalar result, or nothing."""
    if cursor.description is None: 
        return # No result (for example, a DDL query)

    writer = csv.writer(output)

    # The following is a bizarre way to check for a scalar result, but is
    # the same test used in `cqlsh` and I dont see another way to check in
    # the docs.
    if cursor.description is cql.cursor._COUNT_DESCRIPTION:
        writer.writerow(["Result"])
        writer.writerow(cursor.fetchone())
    else:    
        cursor.arraysize = 100 # UNDONE: Paramaterize
        fields = [item[0] for item in cursor.description]
        writer.writerow(fields)
        while True:
            rows = cursor.fetchmany()
            if len(rows) == 0: break
            for row in rows: 
                writer.writerow(convert(row))

# Process a query that returns a 'ragged' result set.
def ragged(cursor, **kwargs):
    """Output a result set that may be 'ragged', aka non-tabular, for example
       the results of a 'SELECT * FROM ..' query."""
    if cursor.rowcount == 0: 
        return

    batchsize = 100

    # Scan up to the first 'batchsize' count of rows and collect up all fields 
    # that we see, these will be emitted as actual columns, anything else that
    # we see for the remainder of the read will be collected into a single 
    # "_extra" column
    count = min(batchsize, cursor.rowcount)
    header = [] # Set of all fields seen in preview window
    rows = []
    for i in xrange(count):
        row = cursor.fetchone()
        fields = [item[0] for item in cursor.description]
        for field in fields:
            if field not in header:
                header.append(field)
        rows.append(dict(zip(fields, convert(row))))
    header.append("_extra")

    writer = csv.DictWriter(output, header)
    writer.writer.writerow(header)

    # Output the preview rows
    for row in rows: 
        writer.writerow(row)

    # Read and output the remaining rows, collecting new fields into _extra
    while True:
        # UNDONE: Python CQL driver doesn't return None when there are no
        # more rows, instead it happily raises IndexError, so add the
        # following hack internal check here.
        if cursor.rs_idx >= len(cursor.result): break

        row = cursor.fetchone()
        if row is None: break
        row = convert(row)

        result = {}
        fields = [item[0] for item in cursor.description]
        for i in xrange(len(row)):
            field = fields[i]
            if field not in header:
                continue # UNDONE: Need to append to _extra
            result[field] = row[i]
        writer.writerow(result)

def main(argv):
    usage = "Usage: dbcql {query}"

    args, kwargs = parse(argv)

    if len(args) > 1:
        error(output, "Unexpected argument: '%s'" % args[1], 2)

    if len(args) < 1:
        error(output, "No query argument", 2)

    keyspace = kwargs.get('keyspace', None)
    host = kwargs.get('host', settings.DEFAULT_CASSANDRA_HOST)
    port = kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT)
    # UNDONE: credentials ..

    query = args[0]
    if query is None:
        error(output, "Command requires a single query argument", 2)

    # A query may consist of multiple expressions. We execute each of
    # the expressions in order and output the results from the final
    # expression. The primary scenario is:
    #
    #     "USE {keyspace}; SELECT * FROM .."
    #
    # However, arbitrary query expressions may be combined in this way.
    expressions = query.split(';')

    # Scan the expressions looking for anything we need to disable
    for expression in expressions:
        # UNDONE: The following disables usage of the CLQ DROP command
        # in order to prevent users from inadvertently (or maliciously)
        # dropping of critical keyspace data until we can properly enable
        # the capability by integrating with Splunk's role based access
        # control (where this would be an admin-only capability).
        if re.match("\s*drop ", expression, re.I):
            error(output, "The CQL DROP command has been disabled.", 2);

    connection = None
    cursor = None
    try:
        connection = cql.connect(host, port, keyspace)
        cursor = connection.cursor()

        # Everything looks ok .. so run them.
        for expression in expressions:
            cursor.execute(expression)

        # A 'SELECT *' expression requires special handling because the
        # results may be "ragged", meaning that we don't know what fields
        # will appear for any given row. In order to handle this case we
        # scan an initial `batchsize` set of rows, collecting all fields
        # that we see. We then use those fields for the results header and
        # collect any additional fields that we subsequently see into an
        # "_extra" MV field. Note that a row in Cassandra can contain up
        # to 2B columns, so "SELECT *" may have other issues aside from the
        # incrimental processing impact on this search script.

        if re.search("select\s+\*", expression, re.I):
            ragged(cursor)
        else:
            normal(cursor)

    except:
        error(output, excinfo(), 2)

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

if __name__ == "__main__":
    main(sys.argv[1:])
