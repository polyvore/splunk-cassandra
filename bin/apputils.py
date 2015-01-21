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
import re
import traceback

def excinfo():
    """Retrieve exception info suitable for printing as command error."""
    exc_type, exc_value, _ = sys.exc_info()
    return ''.join(traceback.format_exception_only(exc_type, exc_value))

# message: str | [str*]
def error(output, message, exitcode=None):
    writer = csv.writer(output)
    writer.writerow(["ERROR"])
    writer.writerow([message])
    if exitcode is None: return
    sys.exit(exitcode)

# argv => args, kwargs
def parse(argv):
    """Parse the given argument vector into a list of positional args and
       a dict containing keyword args."""
    args = []
    kwargs = {}
    for item in argv:
        if len(item) > 1 and item.startswith('"') and item.endswith('"'):
            args.append(item[1:-1])
            continue
        if not re.match(r'^[\w\-]+=[\w\-]+$', item):
            args.append(item)
        else:
            key, value = item.split('=', 1)
            kwargs[key] = value
    return args, kwargs

class Logger:
    """A simple file-like utility class that "tees" stdout to a logfile for 
       debugging."""
    def __init__(self, basename):
        self.log = open(basename+".log", 'w')

    def flush(self):
        self.log.flush()

    def write(self, message):
        self.log.write(message)
        sys.stdout.write(message)

