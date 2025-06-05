#===============================================================================
#
#  Flatmap viewer and annotation tools
#
#  Copyright (c) 2019-21  David Brooks
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
#===============================================================================

import json
import logging
import os
from pathlib import Path
from typing import Optional

from tqdm import tqdm

#===============================================================================

from mapknowledge import KnowledgeStore

#===============================================================================

def get_prior_knowledge(store: KnowledgeStore, knowledge_source: Optional[str]) -> list[tuple[str, str]]:
#========================================================================================================
    if store.db is not None and knowledge_source is not None:
        sources = store.knowledge_sources()     # Ordered, most recent first
        if len(sources) and knowledge_source not in sources:
            # We have no knowledge of the new source so first copy all knowledge from
            # the previous source, updating the source column for the new source
            prior_knowledge = store.db.execute('select entity, knowledge from knowledge where source=?',
                                (sources[0], )).fetchall()
            store.db.executemany('insert into knowledge (source, entity, knowledge) values (?, ?, ?)',
                                ((knowledge_source, row[0], row[1]) for row in prior_knowledge))
            store.db.commit()
        # Now remove all connectivity knowledge
        store.clean_connectivity(knowledge_source)
        # Get all non-connectivity knowledge
        prior_knowledge = store.db.execute('select entity, knowledge from knowledge where source=?',
                                            (knowledge_source, )).fetchall()
        # Delete everything to do with the new knowledge source
        store.db.execute('delete from knowledge where source=?', (knowledge_source,))
        store.db.commit()
        # Return the non-connectivity knowledge from the previous source
        return prior_knowledge
    return []

def save_prior_knowledge(store: KnowledgeStore, knowledge_source: Optional[str], prior_knowledge: list[tuple[str, str]]):
#========================================================================================================================
    if store.db is not None and knowledge_source is not None:
        store.db.executemany('replace into knowledge (source, entity, knowledge) values (?, ?, ?)',
                            ((knowledge_source, row[0], row[1]) for row in prior_knowledge))
        store.db.commit()

#===============================================================================

def load(args):
    scicrunch_key = os.environ.get('SCICRUNCH_API_KEY')
    if scicrunch_key is None:
        logging.error('Undefined SCICRUNCH_API_KEY -- cannot load SCKAN knowledge')
        exit(1)

    store = KnowledgeStore(
        store_directory=args.store_directory,
        knowledge_base=args.knowledge_store,
        sckan_version=args.sckan,
        scicrunch_key=scicrunch_key,
        use_sckan=True,
        verbose=False
        )
    if store.db is None:
        raise IOError(f'Unable to open knowledge store {args.store_directory}/{args.knowledge_store}')

    knowledge_source = store.source
    logging.info(f'Loading SCKAN NPO connectivity for source `{knowledge_source}`')

    all_entities = [row[0] for row in store.db.execute(
        'select distinct entity from knowledge where source=? order by entity', (knowledge_source, )).fetchall()]
    if args.purge:
        if store.db is not None and knowledge_source is not None:
            logging.info(f'Purging all knowledge for source `{knowledge_source}`')
            store.db.execute('delete from knowledge where source=?', (knowledge_source, ))
            store.db.execute('delete from connectivity_nodes where source=?', (knowledge_source, ))
            store.db.commit()
        prior_knowledge = []
    else:
        prior_knowledge = get_prior_knowledge(store, knowledge_source)

    paths = store.connectivity_paths()
    progress_bar = tqdm(total=len(all_entities),
        unit='path', ncols=80,
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')

    path_count = 0
    for path in paths:
        store.entity_knowledge(path, source=knowledge_source)
        progress_bar.update(1)
        path_count += 1

    save_prior_knowledge(store, knowledge_source, prior_knowledge)

    missing_entities = set(all_entities).difference(set([row[0] for row in store.db.execute(
        'select distinct entity from knowledge where source=?', (knowledge_source, )).fetchall()]))
    progress_bar.update(len(all_entities) - len(missing_entities) - path_count)
    for entity in missing_entities:
        store.entity_knowledge(entity, source=knowledge_source)
        progress_bar.update(1)

    store.close()
    progress_bar.close()
    logging.info(f'Loaded connectivity for {path_count} paths for `{knowledge_source}`')

    # Having loaded connectivity we can now save it to JSON
    if args.save_json:
        args.source = knowledge_source
        extract(args)

#===============================================================================

def extract(args):
    knowledge_source = args.source
    store = KnowledgeStore(
        store_directory=args.store_directory,
        knowledge_base=args.knowledge_store,
        read_only=True,
        knowledge_source=knowledge_source)
    if store.db is None:
        raise IOError(f'Unable to open knowledge store {args.store_directory}/{args.knowledge_store}')
    knowledge_source = store.source
    if knowledge_source is None:
        raise ValueError(f'No valid knowledge sources in {args.store_directory}/{args.knowledge_store}')

    saved_knowledge = {
        'source': knowledge_source,
        'knowledge': []
    }
    for row in store.db.execute('select entity, knowledge from knowledge where source=?', (knowledge_source,)).fetchall():
        knowledge = json.loads(row[1])
        knowledge['id'] = row[0]
        saved_knowledge['knowledge'].append(knowledge)
    store.close()

    json_file = Path(args.store_directory) / f'{knowledge_source}.json'
    with open(json_file, 'w') as fp:
        json.dump(saved_knowledge, fp, indent=4)
    logging.info(f"Saved {len(saved_knowledge['knowledge'])} records for `{knowledge_source}` to `{json_file}`")

#===============================================================================

def restore(args):
    with open(args.json_file) as fp:
        saved_knowledge = json.load(fp)
    store = KnowledgeStore(
        store_directory=args.store_directory,
        knowledge_base=args.knowledge_store,
        use_sckan=False)
    if store.db is None:
        raise IOError(f'Unable to open knowledge store {args.store_directory}/{args.knowledge_store}')

    knowledge_source = saved_knowledge['source']

    if args.purge:
        if store.db is not None and knowledge_source is not None:
            logging.info(f'Purging all knowledge for source `{knowledge_source}`')
            store.db.execute('delete from knowledge where source=?', (knowledge_source, ))
            store.db.execute('delete from connectivity_nodes where source=?', (knowledge_source, ))
            store.db.commit()
        prior_knowledge = []
    else:
        prior_knowledge = get_prior_knowledge(store, knowledge_source)

    for knowledge in saved_knowledge['knowledge']:
        entity = knowledge['id']
        store.db.execute('replace into knowledge (source, entity, knowledge) values (?, ?, ?)',
                                             (knowledge_source, entity, json.dumps(knowledge)))
        if 'connectivity' in knowledge:
            seen_nodes = set()
            for edge in knowledge['connectivity']:
                for node in edge:
                    node = (node[0], tuple(node[1]))
                    if node not in seen_nodes:
                        seen_nodes.add(node)
                        store.db.execute('insert into connectivity_nodes (source, node, path) values (?, ?, ?)',
                                                                    (knowledge_source, json.dumps(node), entity))
    store.db.commit()

    save_prior_knowledge(store, knowledge_source, prior_knowledge)

    store.close()
    logging.info(f"Restored {len(saved_knowledge['knowledge'])} records for `{knowledge_source}` from `{args.json_file}`")

#===============================================================================

def info(args):
    store = KnowledgeStore(
        store_directory=args.store_directory,
        knowledge_base=args.knowledge_store,
        read_only=True,
        use_sckan=False)
    for source in store.knowledge_sources():
        print(source)
    store.close()

#===============================================================================

def upgrade(args):
    store = KnowledgeStore(
        store_directory=args.store_directory,
        knowledge_base=args.knowledge_store,
        read_only=False,
        use_sckan=False)
    store.close()

#===============================================================================

def extract_map(args):
    flatmap_dir = Path(args.flatmap_directory)

    # Load uuid and sckan_release
    if not (index_file := flatmap_dir / 'index.json').is_file():
        raise IOError(f'Unable to open {index_file}')
    with open(index_file, 'r') as fp:
        index_data = json.load(fp)
        if not (uuid := index_data.get('uuid')):
            raise IOError("Flatmap source doesn't have uuid.")
        sckan_release = index_data.get('connectivity', {}).get('npo', {}).get('release')

    store = KnowledgeStore(
        store_directory=args.store_directory,
        knowledge_base=args.knowledge_store,
        read_only=False,
        use_sckan=False)

    # Load pathways.json
    if not (pathways_file := flatmap_dir / 'pathways.json').is_file():
        raise IOError(f'Unable to open {pathways_file}')
    with open(pathways_file, 'r') as fp:
        pathways = json.load(fp).get('paths', {})

    # Load *_features.json
    if not (feature_files := list(flatmap_dir.glob('*_features.json'))):
        raise IOError(f'No *_features.json file found in {args.flatmap_directory!r}')
    with open(feature_files[0], 'r') as fp:
        features = json.load(fp).get('features', [])

    # Load *_pathways.json excluding neural-routes
    if not (feature_pathways_files := [p for p in flatmap_dir.glob('*_pathways.json') if not p.name.startswith('neural-routes')]):
        raise IOError(f'No *_pathways.json file found in {args.flatmap_directory!r}')
    with feature_pathways_files[0].open() as fp:
        feature_pathways = json.load(fp).get('features', [])

    knowledge_terms = {}
    for path_id, path in pathways.items():
        if 'connectivity' in path:
            db_knowledge = store.entity_knowledge(path_id, sckan_release)
            knowledge_terms[path_id] = {
                'id': path_id,
                'label': db_knowledge['label'],
                'long-label': db_knowledge['long-label'],
                'connectivity': path['connectivity'],
                'taxons': [index_data.get('taxon', '')],
                'forward-connections': path['forward-connections'],
                'node-phenotypes': path['node-phenotypes'],
                'nerves': path.get('node-nerves', []),
                'pathDisconnected': db_knowledge['pathDisconnected'],
                'phenotypes': db_knowledge.get('phenotypes', []),
                'source': uuid
            }

    for feature in features + feature_pathways:
        if (property := feature.get('properties')) and (model := property.get('models')) and model not in knowledge_terms:
            db_knowledge = store.entity_knowledge(model, sckan_release)
            knowledge_terms[model] = {
                'id': model,
                'label': db_knowledge['label'],
                'source': uuid,
                **({'type': type} if (type := db_knowledge.get('type')) else {})
            }

    saved_knowledge = {
        'source': uuid,
        'knowledge': list(knowledge_terms.values())
    }

    json_file = Path(args.flatmap_directory) / f'{uuid}.json'
    with open(json_file, 'w') as fp:
        json.dump(saved_knowledge, fp, indent=4)
    logging.info(f"Saved {len(saved_knowledge['knowledge'])} records for `{uuid}` to `{json_file}`")

    store.close()

#===============================================================================

DEFAULT_STORE = 'knowledgebase.db'

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Load, extract, and restore SCKAN NPO connectivity knowledge in a local knowledge store.')
    parser.add_argument('--store-directory', required=True, help='Directory containing a knowledge store')
    parser.add_argument('--knowledge-store', default=DEFAULT_STORE, help=f'Name of knowledge store file. Defaults to `{DEFAULT_STORE}`')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress INFO log messages')

    subparsers = parser.add_subparsers(title='commands', required=True)

    parser_load = subparsers.add_parser('load', help='Load connectivity knowledge from SCKAN NPO into a local knowledge store.')
    parser_load.add_argument('--sckan', help='SCKAN release identifier; defaults to latest available version of SCKAN')
    parser_load.add_argument('--purge', action='store_true', help='Optionally flush and reload all entities.')
    parser_load.add_argument('--save-json', action='store_true', help='Optionally save connectivity knowledge as JSON in the store directory.')
    parser_load.set_defaults(func=load)

    parser_extract = subparsers.add_parser('extract', help='Save connectivity knowledge from a local store as JSON in the store directory.')
    parser_extract.add_argument('--source', help='Knowledge source to extract; defaults to the most recent source in the store.')
    parser_extract.set_defaults(func=extract)

    parser_extract_map = subparsers.add_parser('extract-map', help='Save connectivity knowledge from a flatmap as JSON in the flatmap directory.')
    parser_extract_map.add_argument('--flatmap-directory', required=True, help='Directory containing flatmap knowledge.')
    parser_extract_map.set_defaults(func=extract_map)

    parser_info = subparsers.add_parser('info', help='List knowledge sources in a local store.')
    parser_info.set_defaults(func=info)

    parser_restore = subparsers.add_parser('restore', help='Restore connectivity knowledge to a local store from JSON.')
    parser_restore.add_argument('--purge', action='store_true', help='Optionally flush and reload all entities.')
    parser_restore.add_argument('json_file', metavar='JSON_FILE', help='File to load connectivity knowledge from.')
    parser_restore.set_defaults(func=restore)

    parser_upgrade = subparsers.add_parser('upgrade', help='Upgrade local knowledge store to latest database schema.')
    parser_upgrade.set_defaults(func=upgrade)

    args = parser.parse_args()
    if not args.quiet:
        logging.basicConfig(level=logging.INFO)
    args.func(args)

#===============================================================================

if __name__ == '__main__':
#=========================
    main()

#===============================================================================
