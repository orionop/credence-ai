import base64
import io
from typing import Dict, Any
import networkx as nx
import matplotlib.pyplot as plt

try:
    from .gnn_model import score_graph_with_gnn
except ImportError:
    score_graph_with_gnn = None
def build_graph_from_session(
    entity_name: str, 
    rich_gst_data: Dict[str, Any], 
    bank_intelligence: Dict[str, Any], 
    financials: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Builds NetworkX DiGraph from extracted entity relationships.
    Returns network features and base64-encoded PNG.
    """
    G = nx.DiGraph()
    G.add_node(entity_name, type="COMPANY")
    
    # Attempt to extract relationships from rich_gst_data
    top_suppliers = rich_gst_data.get("top_suppliers", [])
    for supplier in top_suppliers:
        name = supplier.get("name", "Unknown Supplier")
        amt = float(supplier.get("amount", 0.0))
        if amt > 0:
            G.add_edge(name, entity_name, amount=amt, source="gst_supplier")
            
    top_customers = rich_gst_data.get("top_customers", [])
    for customer in top_customers:
        name = customer.get("name", "Unknown Customer")
        amt = float(customer.get("amount", 0.0))
        if amt > 0:
            G.add_edge(entity_name, name, amount=amt, source="gst_customer")
            
    # Compute metrics
    if G.number_of_nodes() <= 1:
        return {
            "graph_risk_score": 0.0,
            "graph_cycle_count": 0,
            "graph_max_centrality": 0.0,
            "graph_num_communities": 0,
            "graph_image_base64": None
        }
        
    simple_cycles = list(nx.simple_cycles(G))
    cycle_count = len(simple_cycles)
    
    in_deg = nx.in_degree_centrality(G)
    max_centrality = max(in_deg.values()) if in_deg else 0.0
    
    components = list(nx.weakly_connected_components(G))
    num_communities = len(components)
    
    graph_risk_score = 0.0
    if cycle_count > 0:
        graph_risk_score += min(0.4, 0.05 * cycle_count)
    if max_centrality > 0.3:
        graph_risk_score += 0.3
        
    # Integrate PyTorch Geometric GNN predictions if available
    gnn_risk_score = 0.0
    high_risk_nodes = []
    if score_graph_with_gnn is not None:
        try:
            gnn_risk_score, high_risk_nodes = score_graph_with_gnn(G)
            graph_risk_score += (gnn_risk_score * 0.5) # weigh GNN output
        except Exception as e:
            print(f"Warning: GNN scoring failed: {e}")
            
    graph_risk_score = min(1.0, graph_risk_score)
    
    # Generate image
    plt.figure(figsize=(6, 4))
    # Colors: Company is blue, others are gray
    color_map = ["#4D90FE" if node == entity_name else "#CCCCCC" for node in G.nodes()]
    
    nx.draw(
        G,
        nx.spring_layout(G, seed=42),
        with_labels=True,
        node_color=color_map,
        node_size=800,
        font_size=8,
        font_color="black",
        arrows=True,
        arrowsize=15
    )
    plt.title("Transaction Entity Graph", fontsize=10)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    
    return {
        "graph_risk_score": float(graph_risk_score),
        "graph_cycle_count": int(cycle_count),
        "graph_max_centrality": float(max_centrality),
        "graph_num_communities": int(num_communities),
        "graph_image_base64": img_base64,
        "gnn_risk_score": float(gnn_risk_score),
        "gnn_high_risk_nodes": high_risk_nodes
    }
