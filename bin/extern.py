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

# UNDONE: Need to locate installed Python on Windows

"""Common 'wrapper' script used to invoke an 'external' Python scripts. This
   module is intended to be invoked using Splunk's internal Python stack and
   uses the subprocess module to execute another Python script using the
   platform's installed Python stack."""

from os import path
from subprocess import Popen, STDOUT
import sys

def extern(fname):
    """Invoke the given 'external' python script."""
    run([fname] + sys.argv[1:])

def run(argv):
    process = Popen(["/usr/bin/python"] + argv, env={}, stderr=STDOUT)
    process.communicate()
    process.wait()

if __name__ == "__main__":
    run(sys.argv[1:])
