from pprint import pprint
from mapknowledge import KnowledgeStore

def print_knowledge(store, entity):
    print(f'{entity}:')
    pprint(store.entity_knowledge(entity))
    print()

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)

    store = KnowledgeStore(npo=True, log_build=True)
    print('NPO models:')
    pprint(store.connectivity_models('NPO'))
    print_knowledge(store, 'ilxtr:NeuronKblad')
    print_knowledge(store, 'ilxtr:neuron-type-keast-8')
    print_knowledge(store, 'ilxtr:sparc-nlp/mmset1/3a')
    print_knowledge(store, 'ilxtr:sparc-nlp/mmset1/4')
    print_knowledge(store, 'ilxtr:sparc-nlp/mmset2cn/6')
    store.close()
