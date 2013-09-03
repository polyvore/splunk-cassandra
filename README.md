splunk-cassandra
================

Splunk Cassandra Connect

## Requires

* Splunk Python SDK libs intalled or splunk-sdk-python on PYTHONPATH

* Cassandra
    - Resources:
        - $CASSANDRA_HOME/README.txt
        - http://wiki.apache.org/cassandra/GettingStarted

### Contrib

* pycassa 1.7.2 
    - Installed in {app}/bin/pycassa

* CQL 1.4.0 
    - Installed in {app}/bin/cql

## Running the application

Start Cassandra Cluster and verify listening on 9160

## Inspecting Cassandra

Launch the Cassandra CLI

    cd $CASSANDRA_HOME/bin
    ./cassandra-cli --host localhost

Get listing of available keyspaces:

    show keyspaces;

## Initial App Setup

    edit {app}/bin/setting.py
    set Cassandra Host and Port
    ## Note v.Next will have UI setup for multi cluster
    
    Install universal forwarder on all cassandra nodes 
    Add a splunk forwarder and this entry to /loca/inputs.conf
               [monitor:///var/log/cassandra/*] 
               index=casslogs

    Verify logs are coming into the casslogs index
    Run {app}/bin/python dbschema.py and verify keyspace config shows up
    Run {app}/bin/python dbdiscover.py and verify all Column_Families show up

## Commands Info

[dbcql]
dbcql.py
USAGE: dbcql {query}
    # A query may consist of multiple expressions. We execute each of
    # the expressions in order and output the results from the final
    # expression. The primary scenario is:
    #
    #     "USE {keyspace}; SELECT * FROM {Column_family} WHERE {Conditions}""
    #

[dbinsert]
dbinsert.py
Usage: dbinsert {cfpath} {key} {fields}
    # cfpath must be Keyspace.Column_family notation

[dblookup]
dblookup.py
Usage: dblookup {cfpath} {key}
    # cfpath must be Keyspace.Column_family notation

[dbschema]
dbschema.py
USAGE: dbschema << None OR Keyspace OR Keyspace Column_Family
     # Can use No parameters for cluster, a Keyspace or a Keyspace Column_family
     # dbschema     ## Returns all schema information on cluster
     # dbschema {Keyspace}    ## Returns all schema information for Keyspace = schema1
     # dbschema {Keyspace} {Column_family}    ## Returns all schema information for Column_Family 

[dbgetkeys]
dbgetkeys.py
Usage: dbgetkeys {Keyspace Column_Family}
     # Must be run with both elements Keyspace and Column_family
     # Returns a complete list of Row Keys in format Keyspace,Column_Family,Key

[dbdiscover]
dbdiscover.py
Usage: dbdiscover
     # Collects all keyspaces and column_families on the cluster in   
     # keyspace=system,column_family=schema_keyspaces format


## Configuration Verification 

| dbcql "create keyspace test with strategy_class='LocalStrategy'"

# Verify that the new keyspace exists
| dbschema

| dbcql "use test; create columnfamily test (KEY varchar PRIMARY KEY)"

# Verify that the new columnfamily exists
| dbschema test.test

# Insert verified users into new keyspace
| dbinsert test.test user_id "johnsmith,jsmith"

# Query for all users inserted into new keyspace
| dbcql "use test; select * from test"

# Add stats clause to confirm that there are only one jsmith
| dbcql "use test; select * from test" | search jsmith | stats count

# Drop the test columnfamily
| dbcql "use test; drop columnfamily test"

# Verify that the test columnfamily is gone
| dbschema test

# Drop the test keyspace
| dbcql "drop keyspace test"

# Verify that the test keyspace is gone
| dbschema


