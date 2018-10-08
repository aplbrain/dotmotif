# Running with Neo4j

(No data persistance)

Where `$pwd/import/` contains importable CSVs:

```shell
docker run -it -e NEO4J_AUTH=neo4j1/neo4j1 \
 -p 7474:7474 -p 7687:7687 -v /$(pwd)/import/:/_import_csv/ \
 neo4j:3.4 /bin/bash
```

With plugins:
```
docker run -it -e NEO4J_AUTH=neo4j1/neo4j1 -p 7474:7474 -p 7687:7687 \
-v /$(pwd)/import/:/_import_csv/ \
-v $(pwd)/plugins/:/plugins neo4j:3.4 /bin/bash
```

You may need:
```
docker run -it -e NEO4J_dbms_security_procedures_unrestricted=\* \
-e NEO4J_AUTH=neo4j1/neo4j1 -p 7474:7474 -p 7687:7687 -v /$(pwd) \
/import/:/_import_csv/ -v $(pwd)/plugins/:/plugins neo4j:3.4 /bin/bash
```

From inside the container:
```
./bin/neo4j-admin import --id-type STRING --nodes:Neuron \
"/_import_csv/export-neurons-\d+.csv" --relationships:SYN  \
"/_import_csv/export-synapses-\d+.csv" && ./bin/neo4j start
```

