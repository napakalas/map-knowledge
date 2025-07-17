from pprint import pprint
from mapknowledge import KnowledgeStore
from collections import defaultdict

def print_knowledge(store, entity):
    print(f'{entity}:')
    pprint(store.entity_knowledge(entity))
    print()

def main(sckan_version):
    store = KnowledgeStore(sckan_version=sckan_version)

    nps = defaultdict(dict)
    np_with_connectivities = defaultdict(dict)
    edges = set()
    nodes = set()
    terms = set()
    for path_id in store.connectivity_paths():
        nps[path_id] = store.entity_knowledge(path_id)
        if len(conn:=nps[path_id].get('connectivity', [])) > 0:
            np_with_connectivities[path_id] = nps[path_id]
            for edge in conn:
                edges.add(edge)
                nodes.update(edge)
                terms.update([edge[0][0]] + list(edge[0][1]) + [edge[1][0]] + list(edge[1][1]))

    print(f'# of neuron population having connectivity {len(np_with_connectivities)}')
    print(f'# of edges {len(edges)}')
    print(f'# of nodes {len(nodes)}')
    print(f'# of terms {len(terms)}')

    store.close()

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(description='Print sckan_version stats.')
    parser.add_argument('-v', '--sckan-version', dest='sckan_version', default='sckan-2024-09-21')
    args = parser.parse_args()

    main(args.sckan_version)
