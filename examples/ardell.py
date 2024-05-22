from pprint import pprint
from mapknowledge import KnowledgeStore
from mapknowledge.scicrunch import SCICRUNCH_PRODUCTION, SCICRUNCH_STAGING

MODEL_URI = 'https://apinatomy.org/uris/models/ard-arm-cardiac'

MODEL_ABBRV = 'aacar'

def NEURON_URI(n):
    return f'ilxtr:neuron-type-{MODEL_ABBRV}-{n}'
def KEAST_NEURON(n):
    return f'ilxtr:neuron-type-keast-{n}'

def print_knowledge(store, entity):
    print(f'{entity}:')
    pprint(store.entity_knowledge(entity))
    print()

def print_terminals(store, entity):
    print(f'{entity}:')
    knowledge = store.entity_knowledge(entity)
    pprint({
        'axons': knowledge.get('axons'),
        'dendrites': knowledge.get('dendrites'),
    })
    print()

def print_phenotypes(store, entity):
    print("Querying", entity)
    knowledge = store.entity_knowledge(entity)
    print(f'{entity}: {knowledge.get("phenotypes", [])}')

def store_knowledge(**kwds):
    print('Store:', kwds)
    store = KnowledgeStore(**kwds)
#    print_terminals(store, NEURON_URI(5))
    print_terminals(store, KEAST_NEURON(9))
    store.close()

if __name__ == '__main__':
#    store_knowledge(store_directory='.', log_build=True)
    store_knowledge(npo=True, log_build=True, sckan_release=SCICRUNCH_STAGING)
#    store_knowledge(npo=False, log_build=True, sckan_release=SCICRUNCH_STAGING)
#    store_knowledge(npo=True, log_build=True, sckan_release=SCICRUNCH_PRODUCTION)
#    store_knowledge(npo=False, log_build=True, sckan_release=SCICRUNCH_PRODUCTION)
