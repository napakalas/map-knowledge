# map-knowledge

Provide a sanitised and simplified view of SCKAN knowledge.

## Installation for development

```sh
$ git clone https://github.com/AnatomicMaps/map-knowledge.git
$ cd map-knowledge
$ uv sync --extra tools
```

## Updating SCKAN NPO knowledge

```sh
$ python tools/sckan_connectivity.py --store-directory sckan load --sckan sckan-2024-09-21 --save
```

## Reloading CQ database with SCKAN NPO knowledge

```sh
$ source .venv/bin/activate
$ export KNOWLEDGE_USER=xxxxxx:xxxxxxx
$ PYTHONPATH=. python tools/pg_import.py json sckan/sckan-2024-09-21.json
```
