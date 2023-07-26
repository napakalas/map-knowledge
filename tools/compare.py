from pprint import pprint
from mapknowledge import KnowledgeStore
from npoexplorer import NPOExplorer
import argparse
from mapknowledge.scicrunch import SCICRUNCH_PRODUCTION, SCICRUNCH_STAGING
import networkx as nx

#===============================================================================

SCKAN = {
    'sckan_production': SCICRUNCH_PRODUCTION, 
    'sckan_staging': SCICRUNCH_STAGING,
}

#===============================================================================

def connectivity_from_knowledge(knowledge):
    G = nx.Graph()
    for n, pair in enumerate(knowledge.get('connectivity', [])):
        node_0 = (pair[0][0], tuple(pair[0][1]))
        node_1 = (pair[1][0], tuple(pair[1][1]))
        G.add_edge(node_0, node_1, directed=True, id=n)
    return G

def compare_model(model, endpoint1, endpoint2, output):
    if endpoint1 in SCKAN:
        ep1 = KnowledgeStore(store_directory=None, clean_connectivity=False, scicrunch_release=SCKAN[endpoint1])
    elif endpoint1 == 'npo':
        ep1 = NPOExplorer()
    else:
        raise argparse.ArgumentError(f'Incorrect endpoint1 argument: {endpoint1}')
    if endpoint2 in SCKAN:
        ep2 = KnowledgeStore(store_directory=None, clean_connectivity=False, scicrunch_release=SCKAN[endpoint1])
    elif endpoint2 == 'npo':
        ep2 = NPOExplorer()
    else:
        raise argparse.ArgumentError(f'Incorrect endpoint2 argument: {endpoint2}')
    # get knowledges from endpoints
    conns = [ep1.entity_knowledge(model), ep2.entity_knowledge(model)]
    G_conns = [connectivity_from_knowledge(conns[0]), connectivity_from_knowledge(conns[1])]
    same_structucture = nx.is_isomorphic(G_conns[0], G_conns[1])
    results = {'structure': 'same' if same_structucture else 'different', 'connectivity': {}}
    
    g1_diff = G_conns[0].nodes() - G_conns[1].nodes()
    g1_diff = [set([n[0]]+list(n[1])) if isinstance(n[0], str) else set(n[0] + list[n[1]]) for n in g1_diff]
    g2_diff = G_conns[1].nodes() - G_conns[0].nodes()
    g2_diff = [set([n[0]]+list(n[1])) if isinstance(n[0], str) else set(n[0] + list[n[1]]) for n in g2_diff]
    for n1 in g1_diff:
        for n2 in g2_diff:
            if len(n1-n2)==0 and len(n2-n1)==0:
                continue
            if len(n1-n2)<len(n1):
                results['connectivity'] = [{endpoint1:n1, endpoint2:n2}]
    if output == 'console':    
        from pprint import pprint
        pprint(results)

    ep1.close()
    ep2.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Comparing model connectivities netween NPO, SCKAN production, and SCKAN staging')
    parser.add_argument('--model', dest='model', required=True,
                        help='model name, e.g. ilxtr:neuron-type-keast-5')
    parser.add_argument('--endpoint1', dest='endpoint1', required=True,
                        help='the first endpoint i.e. sckan_production, sckan_staging, npo')
    parser.add_argument('--endpoint2', dest='endpoint2', required=True,
                        help='the second endpoint i.e. sckan_production, sckan_staging, npo')
    parser.add_argument('--output', dest='output', default='console',
                        help='the output type, i.e. console, path to csv file, path to json file , default:console')
    
    args = parser.parse_args()
    compare_model(args.model, args.endpoint1, args.endpoint2, args.output)

#===============================================================================
