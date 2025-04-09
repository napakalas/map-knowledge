# Setting up a new Postgres SCKAN Knowledge Store

```
$ psql -d postgres

create user abi with encrypted password 'XXX';

drop database "map-knowledge";

create database "map-knowledge" owner abi;
```

```
$ cd knowledge

$ psql -d "map-knowledge" -f sql/map-knowledge.schema.sql -U abi

$ poetry install --with tools

$ poetry shell
$ export KNOWLEDGE_USER=abi:XXX
$ python tools/pg_import.py json sckan/sckan-2024-09-21-npo.json
```
