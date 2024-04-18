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

import os
import rdflib
from pyontutils.core import OntGraph, OntResIri
from pyontutils.namespaces import rdfs, ilxtr
from neurondm.core import Config, graphBase, NegPhenotype
from neurondm.core import OntTerm, OntId, RDFL
from neurondm import orders

#===============================================================================

from .namespaces import NAMESPACES
from .apinatomy import EXCLUDED_LAYERS
from .utils import request_json, log

#===============================================================================

NPO_OWNER = 'SciCrunch'
NPO_REPO = 'NIF-Ontology'
NPO_API = f'https://api.github.com/repos/{NPO_OWNER}/{NPO_REPO}'
NPO_RAW = f'https://raw.githubusercontent.com/{NPO_OWNER}/{NPO_REPO}'
NPO_GIT = f'https://github.com/{NPO_OWNER}/{NPO_REPO}'
NPO_TTLS = ('apinat-partial-orders',
            'apinat-pops-more',
            'apinat-simple-sheet',
            'sparc-nlp')
SUFFIX = '.ttl'
gen_neurons_path = 'ttl/generated/neurons/'

#===============================================================================

#### Functions to load knowledge from SCKAN Github ###

def makelpesrdf():
    collect = []
    def lpes(neuron, predicate):
        """ get predicates from python bags """
        # TODO could add expected cardinality here if needed
        return [NAMESPACES.curie(str(o)) for o in neuron.getObjects(predicate)
                if not collect.append((predicate, o))]

    def lrdf(neuron, predicate):
        """ get predicates from graph """
        return [  # XXX FIXME core_graph bad etc.
            NAMESPACES.curie(str(o)) for o in
            neuron.core_graph[neuron.identifier:predicate]]

    return lpes, lrdf, collect


def simplify(e):
    if e is None:
        return
    elif isinstance(e, rdflib.Literal):  # blank case
        return e.toPython()
    else:
        return OntTerm(e).curie

def simplify_nested(f, nested):
    for e in nested:
        if isinstance(e, list) or isinstance(e, tuple):
            yield tuple(simplify_nested(f, e))
        elif isinstance(e, orders.rl):
            yield orders.rl(f(e.region), f(e.layer))
        else:
            yield f(e)

def for_composer(n, cull=False):
    lpes, lrdf, collect = makelpesrdf()
    _po = n.partialOrder()
    fc = dict(
        id = NAMESPACES.curie(str(n.id_)),
        label = str(n.origLabel),
        origin = [l for l in lpes(n, ilxtr.hasSomaLocatedIn)],
        dest = (
            # XXX looking at this there seems to be a fault assumption that
            # there is only a single destination type per statement, this is
            # not the case, there is destination type per destination
            [dict(loc=l, type='AXON-T') for l in lpes(n, ilxtr.hasAxonPresynapticElementIn)] +
            # XXX I strongly reccoment renaming this to SENSORY-T so that the
            # short forms are harder to confuse A-T and S-T
            [dict(loc=l, type='AFFERENT-T') for l in lpes(n, ilxtr.hasAxonSensorySubcellularElementIn)]
        ),
        order = tuple(simplify_nested(simplify, _po)) if _po else [],
        path = (  # TODO pull ordering from partial orders (not implemented in core atm)
            [dict(loc=l, type='AXON') for l in lpes(n, ilxtr.hasAxonLocatedIn)] +
            # XXX dendrites don't really ... via ... they are all both terminal and via at the same time ...
            [dict(loc=l, type='DENDRITE') for l in lpes(n, ilxtr.hasDendriteLocatedIn)]
        ),
        #laterality = lpes(n, ilxtr.hasLaterality),  # left/rigth tricky ?
        #projection_laterality = lpes(n, ilxtr.???),  # axon located in contra ?
        species =            [l for l in lpes(n, ilxtr.hasInstanceInTaxon)],
        sex =                [NAMESPACES.curie(str(p.p)) for p in n if not isinstance(p, NegPhenotype) and p.e==ilxtr.hasBiologicalSex and not collect.append((ilxtr.hasBiologicalSex , p.p))],
        neg_sex =            [NAMESPACES.curie(str(p.p)) for p in n if isinstance(p, NegPhenotype) and p.e==ilxtr.hasBiologicalSex and not collect.append((ilxtr.hasBiologicalSex , p.p))],
        circuit_type =       lpes(n, ilxtr.hasCircuitRolePhenotype),
        phenotype =          [l for l in lpes(n, ilxtr.hasAnatomicalSystemPhenotype)],  # current meaning of composer phenotype
        anatomical_system =  [l for l in lpes(n, ilxtr.hasAnatomicalSystemPhenotype)],
        # there are a number of dimensions that we aren't converting right now
        dont_know_fcrp =     lpes(n, ilxtr.hasFunctionalCircuitRolePhenotype),
        other_phenotype = (  lpes(n, ilxtr.hasPhenotype)
                           + lpes(n, ilxtr.hasMolecularPhenotype)
                           + lpes(n, ilxtr.hasProjectionPhenotype)),
        forward_connection = lpes(n, ilxtr.hasForwardConnectionPhenotype),

        # direct references from individual individual neurons
        provenance =      lrdf(n, ilxtr.literatureCitation),
        sentence_number = lrdf(n, ilxtr.sentenceNumber),
        note_alert =      lrdf(n, ilxtr.alertNote),
        # XXX provenance from ApiNATOMY models as a whole is not ingested
        # right now because composer lacks support for 1:n from neuron to
        # prov, (or rather lacks prov collections) and because it attaches
        # prov to the sentece, which does not exist for all neurons

        # TODO more ...
        # notes = ?

        # for _ignore, hasClassificationPhenotype is used for ApiNATOMY
        # unlikely to be encountered for real neurons any time soon
        _ignore = [l for l in lpes(n, ilxtr.hasClassificationPhenotype)],  # used to ensure we account for all phenotypes
    )
    npo = set((p.e, p.p) for p in n.pes)
    cpo = set(collect)
    unaccounted_pos = npo - cpo
    if unaccounted_pos:
        log.warning(
            str([n.id_, [[n.in_graph.namespace_manager.qname(e) for e in pos]
                     for pos in unaccounted_pos]]))
    return {k:v for k, v in fc.items() if v} if cull else fc

def get_connectivity_edges(partial_order):
    # functions to parse connectivities
    def parse_connectivities(connectivities, partial_order):#, root: str|tuple="blank"):
        if len(partial_order) > 1:
            root = (
                        (
                            partial_order[0].layer, 
                            tuple([partial_order[0].region]),
                        ) 
                        if isinstance(partial_order[0], orders.rl)
                        else (partial_order[0], ())
                    )
            for sub_partial_order in partial_order[1:]:
                adj = (
                    (
                        sub_partial_order[0].layer, 
                        tuple([sub_partial_order[0].region]),
                    ) 
                    if isinstance(sub_partial_order[0], orders.rl)
                    else (sub_partial_order[0], ())
                )
                connectivities += [(root, adj)]
                if len(sub_partial_order) > 1:
                    parse_connectivities(connectivities, sub_partial_order)
    connectivities = []
    if partial_order != "blank":
        parse_connectivities(connectivities, partial_order)

    # filter layer terms, returning filtered_edge
    filtered_connectivities = []
    for edge in connectivities:
        new_edge = []
        for node in edge:
            new_node = []
            for terms in node:
                if isinstance(terms, tuple):
                    terms = [t for t in terms if t not in EXCLUDED_LAYERS]
                    new_node += [tuple(terms)]
                else:
                    terms = terms if terms not in EXCLUDED_LAYERS else []
                    new_node += [terms]
            if isinstance((node_0:=new_node[0]), orders.rl):
                node_0 = [node_0.region, (node_0.layer,)]
            else:
                node_0 = [node_0, ()]
            if len(new_node[0]) == 0 and len(new_node[1]) == 0:
                continue
            elif len(new_node[0]) == 0:
                new_node = [new_node[1][0], tuple(list(new_node[1])[1:])]
            new_edge += [tuple(new_node)]
        if ("blank", ()) in new_edge or len(new_edge) < 2:
            continue
        if new_edge[0] == new_edge[1]:
            continue
        filtered_connectivities += [tuple(new_edge)]
    return list(set(filtered_connectivities))

def load_knowledge_from_ttl(npo_release):
    config = Config('random-merge')
    g = OntGraph()  # load and query graph

    # remove scigraph and interlex calls
    graphBase._sgv = None
    del graphBase._sgv
    if len(OntTerm.query._services) > 1:
        # backup services and avoid issues on rerun
        _old_query_services = OntTerm.query._services
        _noloc_query_services = _old_query_services[1:]

    OntTerm.query._services = (RDFL(g, OntId),)

    for f in NPO_TTLS:
        ori = OntResIri(f'{NPO_RAW}/{npo_release}/{gen_neurons_path}{f}{SUFFIX}')
        [g.add(t) for t in ori.graph]

    for f in ('apinatomy-neuron-populations', 
                '../../npo'):
        p = os.path.normpath(gen_neurons_path + f)
        ori = OntResIri(f'{NPO_RAW}/{npo_release}/{p}{SUFFIX}')
        [g.add((s, rdfs.label, o)) for s, o in ori.graph[:rdfs.label:]]

    config.load_existing(g)
    neurons = config.neurons()  # scigraph required here if deps not removed above
    
    neuron_knowledge = {}
    neuron_terms = {}
    for n in neurons:
        neuron = for_composer(n)
        neuron['connectivity'] = get_connectivity_edges(neuron['order'])
        neuron['class'] = f'ilxtr:{type(n).__name__}'
        neuron['terms-dict'] = {NAMESPACES.curie(str(p.p)):str(p.pLabel) for p in n}
        neuron_terms = {**neuron_terms, **neuron['terms-dict']}
        neuron_knowledge[neuron['id']] = neuron
    return neuron_knowledge, neuron_terms

#===============================================================================

class Npo:
    def __init__(self, npo_release):
        self.__npo_release = self.__check_npo_release(npo_release)
        self.__npo_knowledge, self.__npo_terms = load_knowledge_from_ttl(self.__npo_release)

    def __check_npo_release(self, npo_release):
        if (response:=request_json(f'{NPO_API}/releases')) is not None:
            releases = {r['tag_name']:r for r in response}
            if npo_release is None or npo_release not in releases:
                release = response[0]
                if npo_release is None:
                    log.warning(f'The NPO release is not provided. It is now set to {release["tag_name"]}')
                else:
                    log.warning(f'The NPO {npo_release} release is not found. It is now set to {release["tag_name"]}')
            else:
                release = releases[npo_release]
            response = request_json(f'{NPO_API}/git/refs/tags/{release["tag_name"]}')
            self.__npo_build = {
                'sha': response['object']['sha'] if response is not None else release['tag_name'],
                'date': release['created_at'],
                'released': release['created_at'].split('T')[0],
                'path': f'{NPO_GIT}/tree/{release["tag_name"]}'
            }
            return release['tag_name']
        else:
            log.error(f'{NPO_API} is not reachable.')

    def connectivity_models(self):
        return {v['class']:{'label': '', 'version': ''} for v in self.__npo_knowledge.values()}
    
    def connectivity_paths(self):
        return {k:{'label': '', 'version': ''} for k in self.__npo_knowledge.keys()}

    def build(self):
        return self.__npo_build
    
    def get_knowledge(self, entity) -> dict:
        knowledge = {
            'id': entity
        }
        # check if entity is an ILX or UBERON term
        if entity in self.__npo_terms:
            knowledge['label'] = self.__npo_terms[entity]

        # check if entity is a connectivity model
        if entity in self.connectivity_models():
            knowledge['label'] = entity
            knowledge['paths'] = [{'id': v['id'], 'models': v['id']} for v in self.__npo_knowledge.values() if v['class'] == entity]
            knowledge['references'] = []

        # check if entity is a connecitvity path
        if (path_kn:=self.__npo_knowledge.get(entity)) is not None:
            knowledge['label'] = path_kn['label']
            knowledge['long-label'] = path_kn['label']
            knowledge['connectivity'] = path_kn['connectivity']
            if len(phenotype:=path_kn['phenotype']+path_kn['circuit_type']) > 0:
                knowledge['phenotypes'] = phenotype
            if len(taxon:=path_kn['species']) > 0:
                knowledge['taxon'] = taxon
            else:
                knowledge['taxon'] = ['NCBITaxon:40674']      # Default to Mammalia
            if len(sex:=path_kn['sex']) == 1:
                knowledge['biologicalSex'] = sex[0]
            if len(alert:=path_kn['note_alert']) > 0:
                knowledge['alert'] = alert
            nodes = {}
            for c in path_kn['connectivity']:
                nodes[tuple([c[0][0]] + list(c[0][1]))] = c[0]
                nodes[tuple([c[1][0]] + list(c[1][1]))] = c[1]
            dendrites = [nodes[c] for d in path_kn['origin'] for c in nodes if d in c]
            knowledge['dendrites'] = list(set(dendrites))
            axons = [nodes[c] for a in path_kn['dest'] for c in nodes if a['loc'] in c]
            knowledge['axons'] = axons
            if len(references:=path_kn['provenance']) > 0:
                knowledge['references'] = references

        return knowledge

#===============================================================================
