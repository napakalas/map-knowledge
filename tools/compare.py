from pprint import pprint
from mapknowledge import KnowledgeStore
from npoexplorer import NPOExplorer
import argparse
from mapknowledge.scicrunch import SCICRUNCH_PRODUCTION, SCICRUNCH_STAGING
import networkx as nx
from tqdm import tqdm

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

class ComparedModel:
    def __init__(self, endpoint, model) -> None:
        if endpoint in SCKAN:
            self.__ep = KnowledgeStore(store_directory=None, clean_connectivity=False, scicrunch_release=SCKAN[endpoint])
        elif endpoint == 'npo':
            self.__ep = NPOExplorer()
        else:
            raise argparse.ArgumentError(f'Incorrect endpoint argument: {endpoint}')
        
        self.ep_name = endpoint
        self.results = {'model': model, 'paths': []}
        neurons = self.__ep.entity_knowledge(model)
        if 'paths' not in neurons:
            raise Exception(f'No neurons for {model}')
        else:
            neurons = [n['id'] for n in neurons['paths']]

        self.connectivities = {n_id:self.__ep.entity_knowledge(n_id) for n_id in tqdm(neurons)}
        self.G_conns = {n_id:self.__const_connectivity_graph(conn) for n_id, conn in self.connectivitie.items()}
        
    def __const_connectivity_graph(self, knowledge):
        self.G = nx.Graph()
        for n, pair in enumerate(knowledge.get('connectivity', [])):
            node_0 = (pair[0][0], tuple(pair[0][1]))
            node_1 = (pair[1][0], tuple(pair[1][1]))
            self.G.add_edge(node_0, node_1, directed=True, id=n)

    def compare(self, c_model):
        for n_id, G_conn in self.G_conns.items():
            G_conn_to = c_model.G_conns.get(n_id)
            
            # compare isomorphic, for graph structure
            structure = nx.is_isomorphic(G_conn, G_conn_to)
            result = {'id': n_id, 'structure': 'same' if structure else 'different', 'connectivity': []}
            
            # organised nodes into sorted list for exact comparison
            g1_diff = G_conn.nodes() - G_conn_to.nodes()
            g1_diff = [tuple([n[0]]+list(n[1])) if isinstance(n[0], str) else tuple(n[0] + list[n[1]]) for n in g1_diff]
            g1_diff = sorted(g1_diff, key=len)
            g2_diff = G_conn.nodes() - G_conn_to.nodes()
            g2_diff = [tuple([n[0]]+list(n[1])) if isinstance(n[0], str) else tuple(n[0] + list[n[1]]) for n in g2_diff]
            g2_diff = sorted(g2_diff, key=len)

            # double loop to find matches
            g1_matches = []
            for n1 in g1_diff:
                candidate = None
                g2_match = None
                for n2 in g2_diff:
                    # remove the same nodes but in different attribute orders
                    if len(set(n1)-set(n2))==0 and len(set(n2)-set(n1))==0:
                        g1_matches += [n1]
                        g2_match = n2
                        continue
                    # find candidate with node partial similarity
                    if len(set(n1)-set(n2))<len(n1):
                        candidate = n2
                if g2_match != None:
                    g2_diff = set(g2_diff) - {g2_match}
                if candidate != None:
                    result['connectivity'] += [{self.ep_name:n1, c_model.ep_name:candidate}]
                    g1_matches += [n1]
                    g2_diff = set(g2_diff) - {candidate}
                    candidate == None

            g1_diff = set(g1_diff) - set(g1_matches)
            if len(g1_diff) > 0:
                result['connectivity'] += [{self.ep_name:n, c_model.ep_name:''} for n in list(g1_diff)]
            if len(g2_diff) > 0:
                result['connectivity'] += [{self.ep_name:'', c_model.ep_name:n} for n in list(g2_diff)]

            self.results['paths'] += [result]
        return self.results
    
    def close(self):
        self.__ep.close()
        
def compare_model(model, endpoint1, endpoint2, output):
    kb1 = ComparedModel(endpoint1, model)
    kb2 = ComparedModel(endpoint2, model)
    
    results = kb1.compare(kb2)

    if output == 'console':
        pprint(results)

    kb1.close()
    kb2.close()

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
