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

from functools import reduce
import json
import logging
import os
from typing import Any, Optional

from tqdm import tqdm

#===============================================================================

import psycopg as pg

#===============================================================================

from mapknowledge import KnowledgeStore

#===============================================================================

PG_DATABASE = 'map-knowledge'

DEFAULT_STORE = 'knowledgebase.db'

KNOWLEDGE_USER = os.environ.get('KNOWLEDGE_USER')
KNOWLEDGE_HOST = os.environ.get('KNOWLEDGE_HOST', 'localhost:5432')

#===============================================================================

def clean_source(source: str) -> str:
    if source.endswith('-npo'):
        return source[:-4]
    return source

#===============================================================================

type KnowledgeDict = dict[str, Any]

class KnowledgeList:
    def __init__(self, source: str, knowledge: Optional[list[KnowledgeDict]]=None):
        self.__source = clean_source(source)
        if knowledge is None:
            self.__knowledge: list[KnowledgeDict] = []
        else:
            self.__knowledge = knowledge

    @property
    def source(self):
        return self.__source

    @property
    def knowledge(self):
        return self.__knowledge

    def append(self, knowledge: KnowledgeDict):
        self.__knowledge.append(knowledge)

#===============================================================================

AFFERENT_TERMINAL_ID = 'afferent-terminal'
AXON_LOCATION_ID = 'axon-location'
AXON_TERMINAL_ID = 'axon-terminal'
DENDRITE_ID = 'dendrite'
SOMA_ID = 'soma'
UNKNOWN_ID = 'unknown'

def setup_anatomical_types(cursor):
#==================================
    anatomical_types = [
        (AFFERENT_TERMINAL_ID, 'Afferent terminal', 'The node is located in an afferent terminal'),
        (AXON_LOCATION_ID, 'Axon location', 'The node is located in an axon'),
        (AXON_TERMINAL_ID, 'Axon terminal', 'The node is located in an axon terminal'),
        (DENDRITE_ID, 'Dendrite', 'The node is located in a dendrite'),
        (SOMA_ID, 'Soma', 'The node is located in a soma'),
        (UNKNOWN_ID, 'Unknown', "The node's phenotype is unknown"),
    ]
    cursor.executemany('INSERT INTO anatomical_types (type_id, label, description) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                       anatomical_types)

#===============================================================================

def delete_source_from_tables(cursor, source: str):
#==================================================
    cursor.execute('DELETE FROM path_taxons WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM feature_evidence WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM path_edges WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM path_features WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM path_node_features WHERE source_id=%s', (source,  ))
    cursor.execute('DELETE FROM path_forward_connections WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM path_node_types WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM path_phenotypes WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM path_properties WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM path_nodes WHERE source_id=%s', (source, ))
    cursor.execute('DELETE FROM feature_terms WHERE source_id=%s', (source, ))

def update_connectivity(cursor, knowledge: KnowledgeList):
#=========================================================
    source = knowledge.source
    progress_bar = tqdm(total=len(knowledge.knowledge),
        unit='records', ncols=80,
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}')
    for record in knowledge.knowledge:
        if source == clean_source(record.get('source', '')):
            if (connectivity := record.get('connectivity')) is not None:
                path_id = record['id']

                # Taxons
                taxons = record.get('taxons', ['NCBITaxon:40674'])
                cursor.executemany('INSERT INTO taxons (taxon_id) VALUES (%s) ON CONFLICT DO NOTHING',
                                   ((taxon,) for taxon in taxons))

                # Path taxons
                with cursor.copy("COPY path_taxons (source_id, path_id, taxon_id) FROM STDIN") as copy:
                    for taxon in taxons:
                        copy.write_row((source, path_id, taxon))

                # Evidence
                evidence = record.get('references', [])
                cursor.executemany('INSERT INTO evidence (evidence_id) VALUES (%s) ON CONFLICT DO NOTHING',
                                   ((evidence,) for evidence in evidence))

                # Path evidence
                with cursor.copy("COPY feature_evidence (source_id, term_id, evidence_id) FROM STDIN") as copy:
                    for evidence_id in evidence:
                        copy.write_row((source, path_id, evidence_id))

                # Nodes
                nodes = set(json.dumps(node) for (node, _) in connectivity) | set(json.dumps(node) for (_, node) in connectivity)
                cursor.executemany('INSERT INTO path_nodes (source_id, path_id, node_id) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                                   ((source, path_id, node,) for node in nodes))

                # Node features
                node_features = [ (source, path_id, node, feature)
                                        for (node, features) in [(node, json.loads(node)) for node in nodes]
                                            for feature in [features[0]] + features[1] ]
                cursor.executemany('INSERT INTO path_node_features (source_id, path_id, node_id, feature_id) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING',
                                    node_features)

                # Path edges
                path_nodes = [ (source, path_id, json.dumps(node_0), json.dumps(node_1)) for (node_0, node_1) in connectivity ]
                with cursor.copy("COPY path_edges (source_id, path_id, node_0, node_1) FROM STDIN") as copy:
                    for row in path_nodes:
                        copy.write_row(row)

                # Path features
                path_features = [(source, path_id, feature) for feature in set([nf[3] for nf in node_features])]
                with cursor.copy("COPY path_features (source_id, path_id, feature_id) FROM STDIN") as copy:
                    for row in path_features:
                        copy.write_row(row)

                # Forward connections
                forward_connections = [(source, path_id, forward_path) for forward_path in record.get('forward-connections', [])]
                with cursor.copy("COPY path_forward_connections (source_id, path_id, forward_path_id) FROM STDIN") as copy:
                    for row in forward_connections:
                        copy.write_row(row)

                # Path node types
                afferent_terminal_nodes = [json.dumps(node) for node in record.get('afferent-terminals', [])]
                axon_location_nodes = [json.dumps(node) for node in record.get('axon-locations', [])]
                axon_terminal_nodes = [json.dumps(node) for node in record.get('axon-terminals', [])]
                dendrite_nodes = [json.dumps(node) for node in record.get('dendrites', [])]
                soma_nodes = [json.dumps(node) for node in record.get('somas', [])]
                node_types = []
                for node in nodes:
                    unknown_node_type = True
                    node_values = (source, path_id, node)
                    if node in afferent_terminal_nodes:
                        node_types.append((*node_values, AFFERENT_TERMINAL_ID))
                        unknown_node_type = False
                    if node in axon_location_nodes:
                        node_types.append((*node_values, AXON_LOCATION_ID))
                        unknown_node_type = False
                    if node in axon_terminal_nodes:
                        node_types.append((*node_values, AXON_TERMINAL_ID))
                        unknown_node_type = False
                    if node in dendrite_nodes:
                        node_types.append((*node_values, DENDRITE_ID))
                        unknown_node_type = False
                    if node in soma_nodes:
                        node_types.append((*node_values, SOMA_ID))
                        unknown_node_type = False
                    if unknown_node_type:
                        node_types.append((*node_values, UNKNOWN_ID))
                with cursor.copy("COPY path_node_types (source_id, path_id, node_id, type_id) FROM STDIN") as copy:
                    for row in node_types:
                        copy.write_row(row)

                # Path phenotypes
                with cursor.copy("COPY path_phenotypes (source_id, path_id, phenotype) FROM STDIN") as copy:
                    for phenotype in record.get('phenotypes', []):
                        copy.write_row((source, path_id, phenotype))

                # General path properties
                cursor.execute('INSERT INTO path_properties (source_id, path_id, biological_sex, alert, disconnected) VALUES (%s, %s, %s, %s, %s)',
                                   (source, path_id, record.get('biologicalSex'), record.get('alert'), record.get('pathDisconnected')))

        progress_bar.update(1)
    progress_bar.close()

def update_features(cursor, knowledge: KnowledgeList):
#=====================================================
    source = knowledge.source
    cursor.execute('DELETE FROM feature_terms WHERE source_id=%s', (source, ))
    with cursor.copy("COPY feature_terms (source_id, term_id, label, description) FROM STDIN") as copy:
        for record in knowledge.knowledge:
            if source == clean_source(record.get('source', '')):
                copy.write_row([source, record['id'], record.get('label'), record.get('long-label')])

def update_knowledge_source(cursor, source):
#===========================================
    cursor.execute('INSERT INTO knowledge_sources (source_id) VALUES (%s) ON CONFLICT DO NOTHING', (source,))

#===============================================================================

def pg_import(knowledge: KnowledgeList):
#=======================================
    user = f'{KNOWLEDGE_USER}@' if KNOWLEDGE_USER else ''
    with pg.connect(f'postgresql://{user}{KNOWLEDGE_HOST}/{PG_DATABASE}') as db:
        with db.cursor() as cursor:
            setup_anatomical_types(cursor)
            update_knowledge_source(cursor, knowledge.source)
            delete_source_from_tables(cursor, knowledge.source)
            update_features(cursor, knowledge)
            update_connectivity(cursor, knowledge)
            #if (paths := knowledge.get('paths')) is not None:
            #    pass
        db.commit()

"""
        knowledge = {
            'id': entity
        }
        knowledge['label'] = self.__npo_terms[entity]

        # check if entity is a connectivity model

        if entity in self.connectivity_models():
            knowledge['paths'] = [{'id': v['id'], 'models': v['id']} for v in self.__npo_knowledge.values() if v['class'] == entity]
            knowledge['references'] = []

        # check if entity is a connecitvity path
        if (path_kn:=self.__npo_knowledge.get(entity)) is not None:

{'id': 'ilxtr:NeuronAacar',
 'label': 'ilxtr:NeuronAacar',
 'paths': [{'id': 'ilxtr:neuron-type-aacar-9a',
                        'models': 'ilxtr:neuron-type-aacar-9a'},
                     {'id': 'ilxtr:neuron-type-aacar-7a',
                        'models': 'ilxtr:neuron-type-aacar-7a'},
                     {'id': 'ilxtr:neuron-type-aacar-8a',
                        'models': 'ilxtr:neuron-type-aacar-8a'},

"""

#===============================================================================

def json_knowledge(args) -> KnowledgeList:
#=========================================
    with open(args.json_file) as fp:
        knowledge = json.load(fp)
    knowledge = KnowledgeList(knowledge['source'], knowledge['knowledge'])
    return knowledge

def store_knowledge(args) -> KnowledgeList:
#==========================================
    knowledge_source = args.source
    store = KnowledgeStore(
        store_directory=args.store_directory,
        knowledge_base=args.knowledge_store,
        read_only=True,
        knowledge_source=knowledge_source)
    if store.db is None:
        raise IOError(f'Unable to open knowledge store {args.store_directory}/{args.knowledge_store}')
    if store.source is None:
        raise ValueError(f'No valid knowledge sources in {args.store_directory}/{args.knowledge_store}')
    knowledge = KnowledgeList(store.source)
    for row in store.db.execute('select entity, knowledge from knowledge where source=?', (store.source,)).fetchall():
        entity_knowledge = json.loads(row[1])
        entity_knowledge['id'] = row[0]
        knowledge.knowledge.append(entity_knowledge)
    store.close()
    return knowledge

#===============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import SCKAN knowledge into a PostgresQL knowledge store.')
    parser.add_argument('-q', '--quiet', action='store_true', help='Suppress INFO log messages')
    subparsers = parser.add_subparsers(title='commands', required=True)

    store_parser = subparsers.add_parser('json', help='Import knowledge from a JSON knowledge file.')
    store_parser.add_argument('json_file', metavar='JSON_FILE', help='SCKAN knowledge saved as JSON')
    store_parser.set_defaults(func=json_knowledge)

    store_parser = subparsers.add_parser('store', help='Import knowledge from a local knowledge store.')
    store_parser.add_argument('--store-directory', required=True, help='Directory containing a knowledge store')
    store_parser.add_argument('--knowledge-store', default=DEFAULT_STORE, help=f'Name of knowledge store file. Defaults to `{DEFAULT_STORE}`')
    store_parser.add_argument('--source', help='Knowledge source to import; defaults to the most recent source in the store.')
    store_parser.set_defaults(func=store_knowledge)

    args = parser.parse_args()
    if not args.quiet:
        logging.basicConfig(level=logging.INFO)
    pg_import(args.func(args))

#===============================================================================

if __name__ == '__main__':
#=========================
    main()

#===============================================================================
