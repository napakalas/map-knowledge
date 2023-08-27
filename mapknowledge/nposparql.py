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

from pprint import pprint

from SPARQLWrapper import SPARQLWrapper2
from SPARQLWrapper.SmartWrapper import Value

#===============================================================================

from .namespaces import NAMESPACES

#===============================================================================

NPO_NLP_NEURONS = 'ilxtr:sparc-nlp/'

#===============================================================================

NPO_SPARQL_ENDPOINT = 'https://blazegraph.scicrunch.io/blazegraph/sparql'

#===============================================================================

CONNECTIVITY = """
# Query to generate the adjacency matrix representing the axonal paths of the neuron populations.

PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ilxtr: <http://uri.interlex.org/tgbugs/uris/readable/>

SELECT DISTINCT ?Neuron_IRI ?V1 ?V2
WHERE
{{
    ?Neuron_IRI ilxtr:neuronPartialOrder ?PO .
        ?PO (rdf:rest|rdf:first)* ?r1 .
        ?r1 (rdf:rest|rdf:first)* ?r2 .
        ?r1 rdf:first ?V1 .
        ?r2 rdf:first ?V2 .
        ?V1 rdf:type owl:Class .
        ?V2 rdf:type owl:Class .

        FILTER (?mediator = ?r1)  # draw only from the same partial order
        ?mediator rdf:first ?V1 .  # car
        ?mediator rdf:rest+/rdf:first/rdf:first ?V2 .  # caadr

    FILTER (?V1 != ?V2).
    FILTER(?Neuron_IRI = {entity})
}}
ORDER BY ?V1 ?V2
LIMIT 10000
"""

#===============================================================================

"""
SELECT DISTINCT ?Neuron_IRI
{
   ?Neuron_IRI rdfs:subClassOf*/rdfs:label ?lbl. #http://uri.neuinfo.org/nif/nifstd/sao1417703748
   FILTER((?lbl = 'Neuron'))
}
ORDER BY ?Neuron_IRI
LIMIT 9999



"""

METADATA2 = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX partOf: <http://purl.obolibrary.org/obo/BFO_0000050>
    PREFIX ilxtr: <http://uri.interlex.org/tgbugs/uris/readable/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT ?Neuron_IRI ?Neuron_Label ?Neuron_Pref_Label ?ObservedIn ?Sex
                    ?Phenotype ?Forward_Connections ?Alert ?Citation
    WHERE
    {{
        {{
            SELECT DISTINCT  ?Neuron_IRI ?Neuron_Label ?Neuron_Pref_Label ?Sex ?Alert ?Citation
            WHERE
            {{
                OPTIONAL{{?Neuron_IRI rdfs:label ?Neuron_Label.}}
                OPTIONAL{{?Neuron_IRI skos:prefLabel ?Neuron_Pref_Label.}}

                ?Neuron_IRI ilxtr:hasSomaLocation ?A_IRI.
                OPTIONAL {{?Neuron_IRI ilxtr:hasAxonLocation ?C_IRI.}}
                ?Neuron_IRI (ilxtr:hasAxonTerminalLocation | ilxtr:hasAxonSensoryLocation) ?B_IRI.

                OPTIONAL {{?Neuron_IRI ilxtr:hasPhenotypicSex ?Sex.}}
                OPTIONAL {{?Neuron_IRI ilxtr:literatureCitation ?Citation.}}
                OPTIONAL {{?Neuron_IRI ilxtr:alertNote ?Alert.}}
            }}
        }}

        {{
            SELECT DISTINCT  ?Neuron_IRI ?ObservedIn
            WHERE
            {{
                ?Neuron_IRI ilxtr:hasSomaLocation ?A_IRI.
                OPTIONAL {{?Neuron_IRI ilxtr:hasAxonLocation ?C_IRI.}}
                ?Neuron_IRI (ilxtr:hasAxonTerminalLocation | ilxtr:hasAxonSensoryLocation) ?B_IRI.

                OPTIONAL {{?Neuron_IRI ilxtr:isObservedInSpecies ?ObservedIn.}}
            }}
            GROUP BY ?Neuron_IRI ?ObservedIn
        }}
        {{
            SELECT DISTINCT  ?Neuron_IRI
            (group_concat(distinct ?ForwardConnection; separator=", ") as ?Forward_Connections)
            WHERE
            {{
                ?Neuron_IRI ilxtr:hasSomaLocation ?A_IRI.
                OPTIONAL {{?Neuron_IRI ilxtr:hasAxonLocation ?C_IRI.}}
                ?Neuron_IRI (ilxtr:hasAxonTerminalLocation | ilxtr:hasAxonSensoryLocation) ?B_IRI.

                OPTIONAL {{?Neuron_IRI ilxtr:hasForwardConnection ?ForwardConnection.}}
            }}
            GROUP BY ?Neuron_IRI
        }}

        {{
            SELECT DISTINCT  ?Neuron_IRI ?Phenotype
            WHERE
            {{
                ?Neuron_IRI ilxtr:hasSomaLocation ?A_IRI.
                OPTIONAL {{?Neuron_IRI ilxtr:hasAxonLocation ?C_IRI.}}
                ?Neuron_IRI (ilxtr:hasAxonTerminalLocation | ilxtr:hasAxonSensoryLocation) ?B_IRI.

                OPTIONAL {{?Neuron_IRI (ilxtr:hasNeuronalPhenotype |
                                      ilxtr:hasFunctionalCircuitRole |
                                      ilxtr:hasCircuitRole |
                                      ilxtr:hasProjection
                                      ) ?Phenotype.}}
            }}
            GROUP BY ?Neuron_IRI ?Phenotype
        }}
        FILTER(?Neuron_IRI = {entity})
    }}
    ORDER BY ?Neuron_IRI ?Neuron_Label
    LIMIT 10000
"""


METADATA = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX partOf: <http://purl.obolibrary.org/obo/BFO_0000050>
    PREFIX ilxtr: <http://uri.interlex.org/tgbugs/uris/readable/>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT DISTINCT ?Neuron_IRI ?Neuron_Label ?Neuron_Pref_Label ?ObservedIn ?Sex
                    ?Phenotype  ?Forward_Connection
                    ?Alert ?Citation
    WHERE
    {{
                OPTIONAL{{?Neuron_IRI rdfs:label ?Neuron_Label.}}
                OPTIONAL{{?Neuron_IRI skos:prefLabel ?Neuron_Pref_Label.}}

                ?Neuron_IRI ilxtr:hasSomaLocation ?A_IRI.
                OPTIONAL {{?Neuron_IRI ilxtr:hasAxonLocation ?C_IRI.}}
                ?Neuron_IRI (ilxtr:hasAxonTerminalLocation | ilxtr:hasAxonSensoryLocation) ?B_IRI.

                OPTIONAL {{?Neuron_IRI ilxtr:hasPhenotypicSex ?Sex.}}
                OPTIONAL {{?Neuron_IRI ilxtr:literatureCitation ?Citation.}}
                OPTIONAL {{?Neuron_IRI ilxtr:alertNote ?Alert.}}

                OPTIONAL {{?Neuron_IRI ilxtr:isObservedInSpecies ?ObservedIn.}}

                OPTIONAL {{?Neuron_IRI ilxtr:hasForwardConnection ?ForwardConnection.}}

                OPTIONAL {{?Neuron_IRI (ilxtr:hasNeuronalPhenotype |
                                      ilxtr:hasFunctionalCircuitRole |
                                      ilxtr:hasCircuitRole |
                                      ilxtr:hasProjection
                                      ) ?Phenotype.}}
        FILTER(?Neuron_IRI = {entity})
    }}
"""
#===============================================================================

def sparql_uri(curie: str) -> str:
    return f'<{NAMESPACES.uri(curie)}>'

#===============================================================================

class NpoSparql:
    def __init__(self):
        self.__sparql = SPARQLWrapper2(NPO_SPARQL_ENDPOINT)

    def query(self, sparql) -> list[dict]:
        self.__sparql.setQuery(sparql)
        return self.__sparql.query().bindings

    @staticmethod
    def __row_as_dict(result_row: dict[str, Value]):
        row_dict = {}
        for column, row_data in result_row.items():
            if row_data.type == 'uri':
                row_dict[column] = NAMESPACES.curie(row_data.value)
            else:
                row_dict[column] = row_data.value
        return row_dict

    @staticmethod
    def __results_as_list(results: list[dict]):
        results_list = []
        for result_row in results:
            results_list.append(NpoSparql.__row_as_dict(result_row))
        return results_list

    @staticmethod
    def __result_as_dict(results: list[dict]):
        if len(results):
            ## could have lots of rows if multiple values for query vars, e.g. citation, species, ...
            return NpoSparql.__row_as_dict(results[0])
        else:
            return {}

    def __connectivity(self, neuron):
        return self.__results_as_list(
            self.query(CONNECTIVITY.format(entity=sparql_uri(neuron))))

    def __metadata(self, neuron):
        return self.__result_as_dict(
            self.query(METADATA.format(entity=sparql_uri(neuron))))

    def get_knowledge(self, entity) -> dict:
        metadata = self.__metadata(entity)
        if len(metadata) == 0:
            return {}
        knowledge = {
            'id': entity
        }
        if 'Neuron_Label' in metadata:
            knowledge['label'] = metadata['Neuron_Label']
        else:
            knowledge['label'] = ''
        knowledge['long-label'] = knowledge['label']
        if 'Phenotype' in metadata:
            knowledge['phenotypes'] = [metadata['Phenotype']]
        if 'ObservedIn' in metadata:
            knowledge['taxon'] = metadata['ObservedIn']
        else:
            knowledge['taxon'] = 'NCBITaxon:40674'      # Default to Mammalia
        if 'Sex' in metadata:
            knowledge['biologicalSex'] = metadata['Sex']
        connectivity = []
        for connection in self.__connectivity(entity):
            if ((node_1 := connection.get('V1')) is not None
            and (node_2 := connection.get('V2')) is not None):
                connectivity.append(((node_1, ()), (node_2, ())))
        knowledge['connectivity'] = connectivity
        return knowledge

#===============================================================================
