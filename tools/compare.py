import argparse

import networkx as nx
from npoexplorer import NPOExplorer
from tqdm import tqdm

from mapknowledge import KnowledgeStore
from mapknowledge.scicrunch import SCICRUNCH_PRODUCTION, SCICRUNCH_STAGING

# ===============================================================================

SCKAN = {
    "sckan_production": SCICRUNCH_PRODUCTION,
    "sckan_staging": SCICRUNCH_STAGING,
}

# ===============================================================================


def connectivity_from_knowledge(knowledge):
    G = nx.Graph()
    for n, pair in enumerate(knowledge.get("connectivity", [])):
        node_0 = (pair[0][0], tuple(pair[0][1]))
        node_1 = (pair[1][0], tuple(pair[1][1]))
        G.add_edge(node_0, node_1, directed=True, id=n)
    return G


class ComparedModel:
    def __init__(self, endpoint, model) -> None:
        if endpoint in SCKAN:
            self.ep = KnowledgeStore(
                store_directory=None,
                clean_connectivity=False,
                scicrunch_release=SCKAN[endpoint],
            )
            self.released = self.ep.scicrunch.sckan_build()["released"]
        elif endpoint == "npo":
            self.ep = NPOExplorer()
            self.released = self.ep.metadata("NPO")
        else:
            raise argparse.ArgumentError(f"Incorrect endpoint argument: {endpoint}")

        self.ep_name = endpoint
        self.results = {"model": model}
        neurons = self.ep.entity_knowledge(model)
        if "paths" not in neurons:
            raise Exception(f"No neurons for {model}")
        else:
            neurons = [n["id"] for n in neurons["paths"]]

        self.ent_knowledges = {
            n_id: self.ep.entity_knowledge(n_id) for n_id in tqdm(neurons)
        }
        self.G_conns = {
            n_id: self.__const_connectivity_graph(conn)
            for n_id, conn in self.ent_knowledges.items()
        }

    def __const_connectivity_graph(self, knowledge):
        G = nx.Graph()
        for n, pair in enumerate(knowledge.get("connectivity", [])):
            node_0 = tuple([pair[0][0]] + list(pair[0][1]))
            node_1 = tuple([pair[1][0]] + list(pair[1][1]))
            G.add_edge(node_0, node_1, directed=True, id=n)
        return G

    def __remap_nodes(self, G1, G2):
        maps = {}
        counter = 0
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
                if len(set(n1) - set(n2)) == 0 and len(set(n2) - set(n1)) == 0:
                    maps[counter] = [n1, n2]
                    counter += 1
                    g2_match = n2
                    break
                # find candidate with node partial similarity
                if len(set(n1) - set(n2)) < len(n1):
                    if candidate:
                        if len(set(n1) - set(n2)) < len(set(n1) - set(candidate)):
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

        # recheck, in not isomorphyc case, there are nodes not mapped
        for n in g1_diff:
            if n not in maps.values():
                maps[counter] = [n, None]
                counter += 1
        for n in g2_diff:
            if n not in maps.values():
                maps[counter] = [None, n]
                counter += 1
        return maps

    def compare(self, c_model):
        self.results[
            "comparing"
        ] = f"{self.ep_name} at {self.released} vs {c_model.ep_name} at {c_model.released}"
        self.results["paths"] = []

        # comparing the same neurons in this obj and c_model
        for n_id in set(self.G_conns.keys()) & set(c_model.G_conns.keys()):
            G = self.G_conns.get(n_id)
            G_to = c_model.G_conns.get(n_id)

            # compare isomorphic, for graph structure
            is_isomorphic = nx.is_isomorphic(G, G_to)
            map_nodes = self.__remap_nodes(G, G_to)

            # strore initial results
            result = {"id": n_id, "is_isomorphic": True if is_isomorphic else False}
            if not is_isomorphic:
                # relable graph
                G_map = {v[0]: k for k, v in map_nodes.items()}
                G = nx.relabel_nodes(G, G_map)
                G_to_map = {v[1]: k for k, v in map_nodes.items()}
                G_to = nx.relabel_nodes(G_to, G_to_map)
                G_edge_diffs = G.edges() - G_to.edges()
                G_edge_to_diffs = G_to.edges() - G.edges()

                # record the difference
                result["edges"] = [
                    {self.ep_name: (map_nodes[e[0]][0], map_nodes[e[1]][0])}
                    for e in G_edge_diffs
                ]
                result["edges"] += [
                    {c_model.ep_name: (map_nodes[e[0]][1], map_nodes[e[1]][1])}
                    for e in G_edge_to_diffs
                ]

            # store map_nodes to results:
            result["nodes"] = [
                {self.ep_name: ng, c_model.ep_name: nt}
                for ng, nt in map_nodes.values()
                if ng != nt
            ]

            self.results["paths"] += [result]

        # recording neurons available in this obj but not in c_model
        for n_id in set(self.G_conns.keys()) - set(c_model.G_conns.keys()):
            result = {
                "id": n_id,
                "is_isomorphic": False if is_isomorphic else False,
                "status": f"not found in {self.ep_name}",
            }
            result["edges"] = [{self.ep_name: e} for e in self.G_conns.get(n_id)]
            self.results["paths"] += [result]

        # recording neurons available in c_model but not in this obj
        for n_id in set(c_model.G_conns.keys()) - set(self.G_conns.keys()):
            result = {
                "id": n_id,
                "is_isomorphic": False if is_isomorphic else False,
                "status": f"not found in {c_model.ep_name}",
            }
            result["edges"] = [{c_model.ep_name: e} for e in c_model.G_conns.get(n_id)]
            self.results["paths"] += [result]

        return self.results

    def close(self):
        self.ep.close()


def print_tabular(results, kb1: ComparedModel, kb2: ComparedModel):
    print(
        f"{results['model']}, {kb1.ep_name} at {kb1.released}, {kb2.ep_name} at {kb2.released}"
    )
    for path in results["paths"]:
        for edge in path["edges"]:
            for ep, e in edge.items():
                ne = []
                for tup in e:
                    str_tup = "/".join([sub_tup for sub_tup in tup])
                    ne.append(f"({str_tup})")

                ne_str = "-".join(ne)
                print(
                    f"{path['id']}, {ne_str if ep==kb1.ep_name else ''}, {ne_str if ep==kb2.ep_name else ''}"
                )


def compare_model(model, endpoint1, endpoint2, style):
    kb1 = ComparedModel(endpoint1, model)
    kb2 = ComparedModel(endpoint2, model)

    results = kb1.compare(kb2)
    if style in ["compact", "tabular"]:
        sanitised_paths = []
        for path in results["paths"]:
            if not path["is_isomorphic"]:
                sanitised_path = path
                del sanitised_path["nodes"]
                sanitised_paths += [sanitised_path]
        results["paths"] = sanitised_paths

    if style == "tabular":
        print_tabular(results, kb1, kb2)
    else:
        print(results)

    kb1.close()
    kb2.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Comparing model connectivities netween NPO, SCKAN production, and SCKAN staging"
    )
    parser.add_argument(
        "--model",
        dest="model",
        required=True,
        help="model name, e.g. ilxtr:neuron-type-keast-5",
    )
    parser.add_argument(
        "--endpoint1",
        dest="endpoint1",
        required=True,
        help="the first endpoint i.e. sckan_production, sckan_staging, npo",
    )
    parser.add_argument(
        "--endpoint2",
        dest="endpoint2",
        required=True,
        help="the second endpoint i.e. sckan_production, sckan_staging, npo",
    )
    parser.add_argument(
        "--style",
        dest="style",
        default="compact",
        help="the output style, i.e. compact, tabular, detail , default:compact",
    )

    args = parser.parse_args()
    compare_model(args.model, args.endpoint1, args.endpoint2, args.style)

# ===============================================================================
