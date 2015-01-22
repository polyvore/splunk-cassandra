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

import settings
from apputils import error, excinfo, Logger, parse

from cassandra.cluster import Cluster
from cassandra.query import dict_factory

debug = False
output = Logger(__file__) if debug else sys.stdout

def main(argv):
    usage = "Usage: db [options] [keyspace] {query}"

    args, kwargs = parse(argv)

    if len(args) > 1:
        error(output, "Unexpected argument: '%s'" % args[1], 2)

    keyspace = kwargs.get('keyspace', None)
    hosts = kwargs.get('hosts', settings.DEFAULT_CASSANDRA_HOSTS)
    if type(hosts) is str:
        hosts = hosts.split(',')
    port = int(kwargs.get('port', settings.DEFAULT_CASSANDRA_PORT))
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

    session = None
    try:
        cluster = Cluster(
            hosts,
            port=port,
            protocol_version = 1 # TODO: Option for protocol version
        )
        session = cluster.connect(keyspace)
        # Results returned as list of dicts. Can use other formats specified here:
        # https://datastax.github.io/python-driver/api/cassandra/cluster.html
        session.row_factory = dict_factory

        # Everything looks ok .. so run them.
        for expression in expressions:
            writer = None
            rows = session.execute(expression)
            if not rows:
                # Statements like 'use' don't return results
                continue
            for row in rows:
                if not writer:
                    # Use the first returned row to get column names
                    fields = row.keys()
                    writer = csv.DictWriter(output, fields)
                    writer.writeheader()
                writer.writerow(row)
    except:
        error(output, excinfo(), 2)

    finally:
        if session:
            session.shutdown()
        if cluster:
            cluster.shutdown()

if __name__ == "__main__":
    main(sys.argv[1:])
