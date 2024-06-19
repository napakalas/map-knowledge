#===============================================================================
#
#  Flatmap viewer and annotation tools
#
#  Copyright (c) 2019-24  David Brooks
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

__version__ = "0.18.1"

#===============================================================================

import sqlite3
import json
import os
from pathlib import Path
from typing import Optional

#===============================================================================

from .apinatomy import CONNECTIVITY_ONTOLOGIES, APINATOMY_MODEL_PREFIX
# from .nposparql import NpoSparql, NPO_NLP_NEURONS
from .npo import Npo
from .scicrunch import SCICRUNCH_PRODUCTION, SCICRUNCH_STAGING
from .scicrunch import SciCrunch
from .utils import log                  # type: ignore

#===============================================================================

KNOWLEDGE_BASE = 'knowledgebase.db'

#===============================================================================

SCHEMA_VERSION = '1.2'

KNOWLEDGE_SCHEMA = f"""
    begin;
    create table metadata (name text primary key, value text);

    create table knowledge (entity text primary key, knowledge text);
    create unique index knowledge_index on knowledge(entity);

    create table labels (entity text primary key, label text);
    create unique index labels_index on labels(entity);

    create table publications (entity text, publication text);
    create index publications_entity_index on publications(entity);
    create index publications_publication_index on publications(publication);

    create table connectivity_models (model text primary key, version text);

    create table pmr_models (term text, score number, model text, workspace text, exposure text);
    create index pmr_models_term_index on pmr_models(term, score);

    insert into metadata (name, value) values ('schema_version', '{SCHEMA_VERSION}');
    commit;
"""

SCHEMA_UPGRADES = {
    None: ('1.1', """
        begin;
        alter table connectivity_models add version text;
        insert or replace into metadata (name, value) values ('schema_version', '1.1');
        commit;
    """),
    '1.1': ('1.2', """
        begin;
        create table pmr_models (term text, score number, model text, workspace text, exposure text);
        create index pmr_models_term_index on pmr_models(term, score);
        insert or replace into metadata (name, value) values ('schema_version', '1.2');
        commit;
    """)
}

#===============================================================================

class KnowledgeBase(object):
    def __init__(self, store_directory, read_only=False, create=False, knowledge_base=KNOWLEDGE_BASE):
        self.__db = None
        self.__read_only = read_only
        if store_directory is None:
            self.__db_name = None
        else:
            # Create store directory if it doesn't exist
            if not os.path.exists(store_directory):
                os.makedirs(store_directory)
            # Create knowledge base if it doesn't exist and we are allowed to
            self.__db_name = Path(store_directory, knowledge_base).resolve()
            if not self.__db_name.exists():
                if not create:
                    raise IOError(f'Missing KnowledgeBase: {self.__db_name}')
                db = sqlite3.connect(self.__db_name,
                    detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
                db.executescript(KNOWLEDGE_SCHEMA)
                db.close()
            self.open(read_only=read_only)

    @property
    def db(self):
        return self.__db

    @property
    def db_name(self):
        return self.__db_name

    @property
    def read_only(self):
        return self.__read_only

    def close(self):
        if self.__db is not None:
            self.__db.close()
            self.__db = None

    def open(self, read_only=False):
        self.close()
        if self.__db_name is not None:
            db_uri = '{}?mode=ro'.format(self.__db_name.as_uri()) if read_only else self.__db_name.as_uri()
            self.__db = sqlite3.connect(db_uri, uri=True,
                                        detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            if self.__db is not None:
                if (schema_version := self.metadata('schema_version')) != SCHEMA_VERSION:
                    if read_only:
                        raise ValueError(f'Knowledge base schema requires an upgrade but opened read only...')
                    while schema_version != SCHEMA_VERSION:
                        if (upgrade := SCHEMA_UPGRADES.get(schema_version)) is None:
                            raise ValueError(f'Unable to upgrade knowledge base schema from {schema_version}')
                        log.info(f'Upgrading knowledge base schema from {schema_version} to version {upgrade[0]}')
                        schema_version = upgrade[0]
                        self.__db.executescript(upgrade[1])

    def metadata(self, name):
        if self.__db is not None:
            row = self.__db.execute('select value from metadata where name=?', (name,)).fetchone()
            if row is not None:
                return row[0]

    def set_metadata(self, name, value):
        if self.__db is not None:
            if not self.__db.in_transaction:
                self.__db.execute('begin')
            self.__db.execute('replace into metadata values (?, ?)', (name,value))
            self.__db.execute('commit')

#===============================================================================

class KnowledgeStore(KnowledgeBase):
    def __init__(self, store_directory=None,
                       knowledge_base=KNOWLEDGE_BASE,
                       create=True,
                       read_only=False,
                       clean_connectivity=False,
                       scicrunch_key=None,
                       scicrunch_version=SCICRUNCH_PRODUCTION,
                       sckan_version: Optional[str]=None,
                       sckan_provenance=False,
                       log_provenance=False,
                       use_npo=True,
                       use_scicrunch=True):
        super().__init__(store_directory, create=create, knowledge_base=knowledge_base, read_only=read_only)
        self.__entity_knowledge = {}     # Cache lookups
        self.__npo_entities = set()
        self.__sckan_provenance = {}

        if (db_name := self.db_name) is not None:
            cache_msg = f'with cache {db_name}'
        else:
            cache_msg = f'with no cache'
        log.info(f'Map Knowledge version {__version__} {cache_msg}')

        self.__scicrunch = (SciCrunch(scicrunch_release=scicrunch_version, scicrunch_key=scicrunch_key)
                                if use_scicrunch else
                            None)
        if self.__scicrunch is not None and sckan_provenance:
            sckan_build = self.__scicrunch.build()
            if sckan_build is not None:
                self.__sckan_provenance['scicrunch'] = {
                    'url': self.__scicrunch.api_endpoint,
                    'date': sckan_build['released']
                }
            if log_provenance:
                scicrunch_build = (f" built at {sckan_build['released']}" if sckan_build is not None else '')
                release_version = 'production' if scicrunch_version == SCICRUNCH_PRODUCTION else 'staging'
                log.info(f"With {release_version} SCKAN{scicrunch_build} from {self.__scicrunch.api_endpoint}")

        if use_npo:
            self.__npo_db = Npo(sckan_version)
            self.__npo_entities = set(self.__npo_db.connectivity_paths())
            self.__npo_entities.update(self.__npo_db.connectivity_models())
            if sckan_provenance:
                npo_builds = self.__npo_db.build()
                if len(npo_builds):
                    self.__sckan_provenance['npo'] = {
                            'date': npo_builds['released'],
                            'release': npo_builds['release'],
                            'path': npo_builds['path'],
                            'sha': npo_builds['sha']
                    }
                    if log_provenance:
                        log.info(f"With NPO built at {npo_builds['released']} from {npo_builds['path']}, SHA: {npo_builds['sha']}")
        else:
            self.__npo_db = None

        # Optionally clear local connectivity knowledge
        if (self.db is not None and clean_connectivity):
            log.info(f'Clearing connectivity knowledge...')
            entities = [f'{APINATOMY_MODEL_PREFIX}%']
            entities.extend([f'{ontology}:%' for ontology in CONNECTIVITY_ONTOLOGIES])
            condition = ' or '.join(len(entities)*['entity like ?'])
            self.db.execute('begin')
            self.db.execute(f'delete from knowledge where {condition}', tuple(entities))
            self.db.execute(f'delete from labels where {condition}', tuple(entities))
            self.db.execute(f'delete from publications where {condition}', tuple(entities))
            self.db.execute(f'delete from connectivity_models')
            self.db.execute('commit')
        self.__cleaned_connectivity = clean_connectivity

    @property
    def sckan_provenance(self):
        return self.__sckan_provenance

    def connectivity_models(self) -> list[str]:
    #==========================================
        """
        Get URIs of connectivity models held in thr NPO knowledge source.

        :returns:   A list of model URIs
        """
        if self.__npo_db is not None:
            # Future: need to warn when NPO has been updated and make sure user
            #         clears the cache...
            return self.__npo_db.connectivity_models()
        else:
            log.warning('NPO connectivity models requested but no connection to NPO service')
        """
        ## FUTURE: Code has been kept to be adapted for caching of NPO connectivity
        ##
        elif source == 'APINATOMY':
            def cached_models():
                return {row[0]: {'label': row[1], 'version': row[2]}
                    for row in self.db.execute('''
                        select c.model, l.label, c.version from connectivity_models as c
                            left join labels as l on c.model = l.entity order by model
                        ''')} if self.db is not None else {}
            if self.__scicrunch is not None:
                sckan_models = self.__scicrunch.connectivity_models()
                if not self.__cleaned_connectivity:
                    model_info = cached_models()
                    for model, properties in sckan_models.items():
                        if ((cached_properties := model_info.get(model)) is not None
                        and cached_properties['version'] != properties['version']):
                            raise ValueError(f'Connectivity model {model} has changed in SCKAN -- please `clean connectivity`')
                if self.db is not None and not self.read_only:
                    if not self.db.in_transaction:
                        self.db.execute('begin')
                    for model, properties in sckan_models.items():
                        self.db.execute('replace into connectivity_models values (?, ?)', (model, properties['version']))
                        self.db.execute('replace into labels values (?, ?)', (model, properties['label']))
                    self.db.commit()
                return sckan_models
            else:
                log.warning('APINATOMY connectivity models requested but no connection to SCKAN service, cached data returned')
            return cached_models()
        else:
            log.warning(f'Unknown connectivity model source -- must be APINATOMY or NPO')
        """
        return []

    def connectivity_paths(self) -> list[str]:
    #=========================================
        """
        Get URIs of connectivity paths held in thr NPO knowledge source.

        :returns:   A list of path URIs
        """
        if self.__npo_db is not None:
            # Future: need to warn when NPO has been updated and make sure user
            #         clears the cache...
            return self.__npo_db.connectivity_paths()
        else:
            log.warning('NPO connectivity paths requested but no connection to NPO service')
        return []

    def labels(self):
    #================
        if self.db is not None:
            return [tuple(row) for row in self.db.execute('select entity, label from labels order by entity')]
        else:
            return []

    @staticmethod
    def __log_errors(entity, knowledge):
    #===================================
        for error in knowledge.get('errors', []):
            log.error(f'SCKAN knowledge error: {entity}: {error}')

    def entity_knowledge(self, entity):
    #==================================
        # Check local cache
        if (knowledge := self.__entity_knowledge.get(entity)) is not None:
            KnowledgeStore.__log_errors(entity, knowledge)
            return knowledge

        knowledge = {}
        if self.db is not None:
            # Check our database
            row = self.db.execute('select knowledge from knowledge where entity=?', (entity,)).fetchone()
            if row is not None:
                knowledge = json.loads(row[0])

        if len(knowledge) == 0 or entity == knowledge.get('label', entity):
            # We don't have knowledge or a valid label for the entity
            ontology = entity.split(':')[0]
            if entity in self.__npo_entities or ontology in CONNECTIVITY_ONTOLOGIES:
                # Always consult NPO for connectivity or if we know it has the term
                if self.__npo_db:
                    knowledge = self.__npo_db.get_knowledge(entity)
            elif self.__scicrunch is not None:
                # Otherwise consult Scicrunch
                knowledge = self.__scicrunch.get_knowledge(entity)
                if 'connectivity' in knowledge:
                    # Get phenotype, taxon, and other metadata
                    knowledge.update(self.__scicrunch.connectivity_metadata(entity))

            if self.db is not None and 'connectivity' in knowledge:
                # Make sure we have labels for each entity used for connectivity
                connectivity_terms = set()
                for (node0, node1) in knowledge['connectivity']:
                    connectivity_terms.update([node0[0], node1[0]])
                    connectivity_terms.update(node0[1])
                    connectivity_terms.update(node1[1])
                for connectivity_term in connectivity_terms:
                    self.label(connectivity_term)
            if len(knowledge) > 0 and self.db is not None and not self.read_only:
                if not self.db.in_transaction:
                    self.db.execute('begin')
                # Use 'long-label' if the entity's label' is the same as itself.
                if 'label' in knowledge:
                    if knowledge['label'] == entity and 'long-label' in knowledge:
                        knowledge['label'] = knowledge['long-label']                # Save knowledge in our database
                self.db.execute('replace into knowledge values (?, ?)', (entity, json.dumps(knowledge)))
                # Save label and references in their own tables
                if 'label' in knowledge:
                    self.db.execute('replace into labels values (?, ?)', (entity, knowledge['label']))
                if 'references' in knowledge:
                    self.__update_references(entity, knowledge.get('references', []))
                self.db.commit()

        # Use the entity's value as its label if none is defined
        if 'label' not in knowledge:
            knowledge['label'] = entity

        # Cache local knowledge
        self.__entity_knowledge[entity] = knowledge

        # Log any errors
        KnowledgeStore.__log_errors(entity, knowledge)

        return knowledge

    def label(self, entity):
    #=======================
        if self.db is not None:
            row = self.db.execute('select label from labels where entity=?', (entity,)).fetchone()
            if row is not None:
                return row[0]
        knowledge = self.entity_knowledge(entity)
        return knowledge['label']

    def __update_references(self, entity, references):
    #=================================================
        if self.db is not None:
            with self.db:
                self.db.execute('delete from publications where entity = ?', (entity, ))
                self.db.executemany('insert into publications(entity, publication) values (?, ?)',
                    ((entity, reference) for reference in references))

#===============================================================================

