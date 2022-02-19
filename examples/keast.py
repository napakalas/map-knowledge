from pprint import pprint
from mapknowledge import KnowledgeStore

KEAST_MODEL = 'https://apinatomy.org/uris/models/keast-bladder'

def KEAST_NEURON(n):
    return f'ilxtr:neuron-type-keast-{n}'

def print_knowledge(store, entity):
    print(f'{entity}:')
    pprint(store.entity_knowledge(entity))
    print()

if __name__ == '__main__':
    store = KnowledgeStore('.')
    print_knowledge(store, KEAST_MODEL)
    for n in range(1, 4):
        print_knowledge(store, KEAST_NEURON(n))

    #  NLX    ## Add tests...
    print_knowledge(store, 'CL:0000540')
    print_knowledge(store, 'EMAPA:31526')
    print_knowledge(store, 'FMA:6541')
    print_knowledge(store, 'ILX:0777088')
    print_knowledge(store, 'NCBITaxon:10114')
    print_knowledge(store, 'UBERON:0002108')

    store.close()
