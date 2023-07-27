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
            self.ep = KnowledgeStore(store_directory=None, clean_connectivity=False, scicrunch_release=SCKAN[endpoint])
        elif endpoint == 'npo':
            self.ep = NPOExplorer()
        else:
            raise argparse.ArgumentError(f'Incorrect endpoint argument: {endpoint}')
        
        self.ep_name = endpoint
        self.results = {'model': model}
        neurons = self.ep.entity_knowledge(model)
        if 'paths' not in neurons:
            raise Exception(f'No neurons for {model}')
        else:
            neurons = [n['id'] for n in neurons['paths']]

        self.ent_knowledges = {n_id:self.ep.entity_knowledge(n_id) for n_id in tqdm(neurons)}
        self.G_conns = {n_id:self.__const_connectivity_graph(conn) for n_id, conn in self.ent_knowledges.items()}
        
    def __const_connectivity_graph(self, knowledge):
        G = nx.Graph()
        for n, pair in enumerate(knowledge.get('connectivity', [])):
            node_0 = tuple([pair[0][0]] + list(pair[0][1]))
            node_1 = tuple([pair[1][0]] + list(pair[1][1]))
            G.add_edge(node_0, node_1, directed=True, id=n)
        return G

    def __remap_nodes(self, G1, G2):
        maps = {}
        counter = 1
        g1_diff = G1.nodes() - G2.nodes()
        g2_diff = G2.nodes() - G1.nodes()
        for n in G1.nodes() & G2.nodes():
            maps[counter] = [n, n]
            counter += 1

        # double loop to find matches
        for n1 in g1_diff:
            candidate = False
            g2_match = False
            for n2 in g2_diff:
                # remove the same nodes but in different attribute orders
                if len(set(n1)-set(n2))==0 and len(set(n2)-set(n1))==0:
                    maps[counter] = [n1, n2]
                    counter += 1
                    g2_match = n2
                    break
                # find candidate with node partial similarity
                if len(set(n1)-set(n2))<len(n1):
                    if candidate:
                        if len(set(n1)-set(n2)) < len(set(n1)-set(candidate)):
                            candidate = n2    
                    else:
                        candidate = n2

            if g2_match:
                g2_diff = set(g2_diff) - {g2_match}
                g2_match = False
            
            if candidate:
                maps[counter] = [n1, candidate]
                counter += 1
                g2_diff = set(g2_diff) - {candidate}
                candidate = None
                
        return maps

    def compare(self, c_model):
        self.results['comparing'] = f'{self.ep_name} vs {c_model.ep_name}'
        self.results['paths'] = []
        for n_id, G in self.G_conns.items():
            G_to = c_model.G_conns.get(n_id)
            
            # compare isomorphic, for graph structure
            is_struct_sim = nx.is_isomorphic(G, G_to)
            map_nodes = self.__remap_nodes(G, G_to)

            # strore initial results
            result = {'id': n_id, 'is_isomorphic': True if is_struct_sim else False}

            if not is_struct_sim:
                # relable graph
                G_map = {v[0]:k for k, v in map_nodes.items()}
                G = nx.relabel_nodes(G, G_map)
                G_to_map = {v[1]:k for k, v in map_nodes.items()}
                G_to = nx.relabel_nodes(G_to, G_to_map)
                # get edge difference
                G_edge_diffs = G.edges() - G_to.edges()
                G_edge_to_diffs = G_to.edges() - G.edges()
                
                # record the difference
                result['edges'] = []
                result['edges'] += [{self.ep_name:(map_nodes[e[0]][0], map_nodes[e[1]][0])} for e in G_edge_diffs]
                result['edges'] += [{c_model.ep_name:(map_nodes[e[0]][1], map_nodes[e[1]][1])} for e in G_edge_to_diffs]

            # store map_nodes to results:
            result['nodes'] = [{self.ep_name:ng, c_model.ep_name:nt} for ng, nt in map_nodes.values() if ng != nt]

            self.results['paths'] += [result]
        return self.results
    
    def close(self):
        self.ep.close()

def print_tabular(results, endpoint1, endpoint2):
    print(f"results['model'], {endpoint1}, {endpoint1}")
    print(f'neuron, {endpoint1} edge, {endpoint2} edge')
    for path in results['paths']:
        for edge in path['edges']:
            for ep, e in edge.items():
                ne = []
                for tup in e:
                    str_tup = '/'.join([sub_tup for sub_tup in tup])
                    ne.append(f'({str_tup})')

                ne_str = '-'.join(ne)
                print(f"{path['id']}, {ne_str if ep==endpoint1 else ''}, {ne_str if ep==endpoint2 else ''}")

def compare_model(model, endpoint1, endpoint2, style):
    kb1 = ComparedModel(endpoint1, model)
    kb2 = ComparedModel(endpoint2, model)
    
    results = kb1.compare(kb2)
    if style in ['compact', 'tabular']:
        sanitised_paths = []
        for path in results['paths']:
            if not path['is_isomorphic']:
                sanitised_paths = path
                del sanitised_paths['nodes']
        results['paths'] = sanitised_paths
    
    if style == 'tabular':
        print_tabular(results, endpoint1, endpoint2)
    else:
        print(results)

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
    parser.add_argument('--style', dest='style', default='compact',
                        help='the output style, i.e. compact, tabular, detail , default:compact')
    
    args = parser.parse_args()
    compare_model(args.model, args.endpoint1, args.endpoint2, args.style)

#===============================================================================
