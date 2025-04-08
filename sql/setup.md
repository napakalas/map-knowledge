# Setting up a new Postgres SCKAN Knowledge Store

```
$ psql -d postgres

create user abi with encrypted password 'XXX';


drop database "map-knowledge";

create database "map-knowledge";
grant all privileges on database "map-knowledge" to abi;
```

```
$ cd knowledge
$ export KNOWLEDGE_USER=abi:XXX
$ psql -d "map-knowledge" -f sql/map-knowledge.schema.sql

$ poetry shell
$ python tools/pg_import.py json sckan/sckan-2024-09-21-npo.json
```
