# Setting up a new Postgres SCKAN Knowledge Store

```
$ psql -d postgres

create database "map-knowledge";
create user abi with encrypted password 'XXX';
```

```
$ cd knowledge
$ export KNOWLEDGE_USER=abi:XXX
$ psql -d "map-knowledge" -f sql/map-knowledge.schema.sql

$ poetry shell
$ python tools/pg_import.py json sckan/sckan-2024-09-21-npo.json
```
