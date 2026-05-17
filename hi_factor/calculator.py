"""
Homogeneity Index Calculator
Market state factor based on graph automorphism group analysis

Implementation Note:
This module provides two computation modes:
1. Heuristic Mode (default): Fast node-signature based approximation
2. Exact Mode: True automorphism group computation using graph isomorphism

For graphs with >20 nodes, heuristic mode is recommended for performance.
For small graphs or validation purposes, exact mode provides mathematically
precise results.
"""
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher
from collections import defaultdict
from typing import List, Dict, Optional, Tuple
import math


class HomogeneityIndex:
    """
    Calculate market homogeneity index from stock correlation networks.
    
    Parameters
    ----------
    stock_list : List[str]
        List of stock symbols
    db_path : str
        Path to SQLite database with price data
    correlation_threshold : float, default=0.5
        Threshold for building correlation graph
    lookback_days : int, default=20
        Window size for return calculation
    min_stocks : int, default=10
        Minimum number of valid stocks required
    exact_mode : bool, default=False
        If True, use exact automorphism computation (slower but precise).
        If False, use heuristic approximation (faster, recommended for n>20).
    """
    
    def __init__(self, 
                 stock_list: List[str],
                 db_path: str,
                 correlation_threshold: float = 0.5,
                 lookback_days: int = 20,
                 min_stocks: int = 10,
                 exact_mode: bool = False):
        self.stock_list = stock_list
        self.db_path = db_path
        self.correlation_threshold = correlation_threshold
        self.lookback_days = lookback_days
        self.min_stocks = min_stocks
        self.exact_mode = exact_mode
        
    def _get_stock_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch stock data from database."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT trade_date, close_ 
            FROM eq_daily_price_v2 
            WHERE symbol = ? AND trade_date BETWEEN ? AND ?
            ORDER BY trade_date
        """
        df = pd.read_sql(query, conn, params=(symbol, start_date, end_date))
        conn.close()
        return df
    
    def _compute_returns(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate daily returns."""
        df['returns'] = df['close_'].pct_change()
        return df['returns'].dropna().values
    
    def _build_correlation_matrix(self, returns_dict: Dict[str, np.ndarray]) -> Tuple[np.ndarray, List[str]]:
        """Build correlation matrix from returns."""
        symbols = list(returns_dict.keys())
        n = len(symbols)
        corr_matrix = np.zeros((n, n))
        
        for i, sym1 in enumerate(symbols):
            for j, sym2 in enumerate(symbols):
                if i == j:
                    corr_matrix[i, j] = 1.0
                elif i < j:
                    min_len = min(len(returns_dict[sym1]), len(returns_dict[sym2]))
                    if min_len > 10:
                        r1 = returns_dict[sym1][:min_len]
                        r2 = returns_dict[sym2][:min_len]
                        corr = np.corrcoef(r1, r2)[0, 1]
                        if not np.isnan(corr):
                            corr_matrix[i, j] = corr
                            corr_matrix[j, i] = corr
        
        return corr_matrix, symbols
    
    def _build_graph(self, corr_matrix: np.ndarray) -> nx.Graph:
        """Build graph from correlation matrix."""
        n = corr_matrix.shape[0]
        G = nx.Graph()
        G.add_nodes_from(range(n))
        
        for i in range(n):
            for j in range(i + 1, n):
                if corr_matrix[i, j] >= self.correlation_threshold:
                    G.add_edge(i, j, weight=corr_matrix[i, j])
        
        return G
    
    def _compute_node_invariants(self, G: nx.Graph) -> Dict[int, tuple]:
        """
        Compute node invariants for fast equivalence testing.
        Returns dict: node -> (degree, neighbor_degrees, distance_distribution)
        """
        invariants = {}
        for node in G.nodes():
            degree = G.degree(node)
            neighbor_degrees = tuple(sorted([G.degree(nbr) for nbr in G.neighbors(node)]))
            
            # Distance distribution
            dist_counts = defaultdict(int)
            for other in G.nodes():
                if other != node:
                    try:
                        dist = nx.shortest_path_length(G, node, other)
                        dist_counts[dist] += 1
                    except nx.NetworkXNoPath:
                        dist_counts[-1] += 1
            
            max_dist = max(dist_counts.keys()) if dist_counts else 0
            dist_dist = tuple(dist_counts.get(d, 0) for d in range(max_dist + 2))
            
            invariants[node] = (degree, neighbor_degrees, dist_dist)
        
        return invariants
    
    def _are_nodes_equivalent(self, G: nx.Graph, node1: int, node2: int, 
                              invariants: Optional[Dict] = None) -> bool:
        """
        Check if two nodes are in the same orbit using graph isomorphism.
        """
        if invariants is not None and invariants.get(node1) != invariants.get(node2):
            return False
        
        # Create marked graphs
        G1 = G.copy()
        G2 = G.copy()
        
        G1.add_node('marker')
        G1.add_edge('marker', node1)
        
        G2.add_node('marker')
        G2.add_edge('marker', node2)
        
        matcher = GraphMatcher(G1, G2)
        return matcher.is_isomorphic()
    
    def _compute_orbits_exact(self, G: nx.Graph) -> List[List[int]]:
        """
        Compute exact orbits using graph isomorphism.
        Computationally expensive for large graphs.
        """
        invariants = self._compute_node_invariants(G)
        nodes = list(G.nodes())
        
        # Union-find structure
        parent = {node: node for node in nodes}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Check all pairs
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                if self._are_nodes_equivalent(G, node1, node2, invariants):
                    union(node1, node2)
        
        # Collect orbits
        orbit_dict = defaultdict(list)
        for node in nodes:
            root = find(node)
            orbit_dict[root].append(node)
        
        return list(orbit_dict.values())
    
    def _compute_orbits_heuristic(self, G: nx.Graph) -> List[List[int]]:
        """
        Compute approximate orbits using node signatures.
        Fast but may not be mathematically exact.
        """
        node_signatures = {}
        for node in G.nodes():
            degree = G.degree(node)
            neighbors = sorted([G.degree(nbr) for nbr in G.neighbors(node)])
            node_signatures[node] = (degree, tuple(neighbors))
        
        signature_groups = defaultdict(list)
        for node, sig in node_signatures.items():
            signature_groups[sig].append(node)
        
        return list(signature_groups.values())
    
    def _compute_orbits(self, G: nx.Graph) -> Tuple[List[List[int]], str]:
        """
        Compute orbits using selected mode.
        Returns (orbits, method_used).
        """
        n = G.number_of_nodes()
        
        if self.exact_mode or n <= 20:
            return self._compute_orbits_exact(G), "exact"
        else:
            return self._compute_orbits_heuristic(G), "heuristic"
    
    def calculate(self, start_date: str, end_date: str) -> Optional[Dict]:
        """
        Calculate homogeneity index for given period.
        
        Parameters
        ----------
        start_date : str
            Start date (YYYY-MM-DD)
        end_date : str
            End date (YYYY-MM-DD)
            
        Returns
        -------
        dict or None
            Dictionary with homogeneity index and related metrics
        """
        # Fetch data
        returns_dict = {}
        valid_symbols = []
        
        for symbol in self.stock_list:
            try:
                df = self._get_stock_data(symbol, start_date, end_date)
                if len(df) > self.lookback_days:
                    returns = self._compute_returns(df)
                    returns_dict[symbol] = returns
                    valid_symbols.append(symbol)
            except Exception:
                continue
        
        if len(valid_symbols) < self.min_stocks:
            return None
        
        # Build correlation matrix and graph
        corr_matrix, active_symbols = self._build_correlation_matrix(returns_dict)
        G = self._build_graph(corr_matrix)
        
        # Compute orbits
        orbits, method_used = self._compute_orbits(G)
        n_orbits = len(orbits)
        n_valid = len(active_symbols)
        
        # Calculate components
        # 1. Base homogeneity rate
        homo_rate = 1 - (n_orbits / n_valid)
        
        # 2. Max cluster ratio
        max_orbit_size = max(len(o) for o in orbits) if orbits else 0
        max_cluster_ratio = max_orbit_size / n_valid
        
        # 3. Graph density
        n_edges = G.number_of_edges()
        max_edges = n_valid * (n_valid - 1) / 2
        graph_density = n_edges / max_edges if max_edges > 0 else 0
        
        # 4. Concentration
        orbit_sizes = [len(o) for o in orbits]
        total = sum(orbit_sizes)
        if total > 0:
            probs = [s / total for s in orbit_sizes]
            entropy = -sum(p * np.log(p + 1e-10) for p in probs)
            max_entropy = np.log(len(orbits)) if len(orbits) > 1 else 1
            concentration = 1 - (entropy / max_entropy) if max_entropy > 0 else 0
        else:
            concentration = 0
        
        # Weighted homogeneity index
        homogeneity_index = (
            0.40 * homo_rate +
            0.30 * max_cluster_ratio +
            0.20 * graph_density +
            0.10 * concentration
        )
        
        # Determine signal
        if homogeneity_index > 0.105:
            signal = "high"
        elif homogeneity_index < 0.090:
            signal = "low"
        else:
            signal = "normal"
        
        # Automorphism group size estimate
        aut_size = 1
        for orbit in orbits:
            aut_size *= math.factorial(len(orbit))
        
        return {
            "homogeneity_index": homogeneity_index,
            "signal": signal,
            "n_stocks": n_valid,
            "n_orbits": n_orbits,
            "max_orbit_size": max_orbit_size,
            "homo_rate": homo_rate,
            "max_cluster_ratio": max_cluster_ratio,
            "graph_density": graph_density,
            "concentration": concentration,
            "n_edges": n_edges,
            "automorphism_group_size_estimate": aut_size,
            "computation_method": method_used,
            "active_symbols": active_symbols,
            "orbits": [[active_symbols[i] for i in orbit] for orbit in orbits]
        }
    
    def get_signal_description(self, signal: str) -> str:
        """Get human-readable signal description."""
        descriptions = {
            "high": "High homogeneity - reduce exposure, defensive positioning",
            "normal": "Normal state - maintain current strategy",
            "low": "Low homogeneity - stock selection, sector rotation"
        }
        return descriptions.get(signal, "Unknown signal")
