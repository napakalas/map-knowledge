from pprint import pprint
from mapknowledge import KnowledgeStore
from mapknowledge.scicrunch import SCICRUNCH_PRODUCTION, SCICRUNCH_STAGING

def print_knowledge(store, entity):
    print(f'{entity}:')
    pprint(store.entity_knowledge(entity))
    print()

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)

    store = KnowledgeStore(npo=True, log_build=True, scicrunch_release=SCICRUNCH_STAGING)
    if store.npo:
        pprint(store.sckan_provenance)
        print('NPO models:')
        pprint(store.npo.connectivity_models())
        print('NPO paths:')
        pprint(store.npo.connectivity_paths())
    print_knowledge(store, 'ilxtr:NeuronKblad')
    print_knowledge(store, 'ilxtr:neuron-type-keast-8')
    print_knowledge(store, 'ilxtr:sparc-nlp/mmset1/3a')
    print_knowledge(store, 'ilxtr:sparc-nlp/mmset1/4')
    print_knowledge(store, 'ilxtr:sparc-nlp/mmset2cn/6')
    store.close()
