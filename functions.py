import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from matplotlib.colors import Normalize
import matplotlib.cm as cm

@st.experimental_memo
def get_layout():

    layout = go.Layout(
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        hovermode='closest',
        margin=dict(b=30,l=0,r=0,t=30),
        annotations=[dict(
            text="Source : <a href='https://genius.com'>Genius</a>",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.05,
            font=dict(color='white')
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    return layout

@st.experimental_memo
def get_featuring_graph_chart(_graph, l0_nodes, artist_dict:dict):

    def get_marker_trace_sp(shortest_path, chart_graph, artist_dict, chart_colors, node_pos):

        x = [node_pos[node][0] for node in shortest_path]
        y = [node_pos[node][1] for node in shortest_path]
        s = [chart_graph.nodes[node]['size'] for node in shortest_path]
        c = [chart_colors[node] for node in shortest_path]
        t = [artist_dict[node] for node in shortest_path]
        tp = ['top center' if size * 2  - len(text) * 14 < 3 else 'middle center' for text, size in zip(t, s)]

        trace = go.Scatter(
            x = x, 
            y = y, 
            hoverinfo = 'none', 
            text = t, 
            mode = 'markers+text',
            textposition = tp,
            textfont = dict(color='white', size=14),
            marker = dict(
                color = c,
                opacity = 1,
                size = s, 
                sizemin = 4,
                sizeref = 2.5,
                line = dict(
                    color = 'rgba(255, 255, 255, 0.2)', 
                    width = 8),
            ),
        )

        return trace

    def get_marker_trace_lo(layer_one_nodes, chart_graph, artist_dict, chart_colors, node_pos):

        x = [node_pos[node][0] for node in layer_one_nodes]
        y = [node_pos[node][1] for node in layer_one_nodes]
        s = [chart_graph.nodes[node]['size'] for node in layer_one_nodes]
        c = [chart_colors[chart_graph.nodes[node]['parent']] for node in layer_one_nodes]
        t = [artist_dict[node] for node in layer_one_nodes]

        trace = go.Scatter(
            x = x, 
            y = y, 
            hoverinfo = 'text', 
            hoverlabel=dict(font_size=12, font=dict(color='black')),
            hovertemplate = [f'<b>{j}</b><extra></extra>' for j in t],
            text = t, 
            mode = 'markers',
            marker = dict(
                color = c,
                opacity = 0.5,
                size = s,
                sizemin = 4,
                sizeref = 2.5,
                line = dict(width=2, color='rgba(255, 255, 255, 0.5)')
            ),
        )

        return trace

    def get_marker_trace_lt(layer_two_nodes, chart_graph, artist_dict, node_pos):

        x = [node_pos[node][0] for node in layer_two_nodes]
        y = [node_pos[node][1] for node in layer_two_nodes]
        s = [chart_graph.nodes[node]['size'] for node in layer_two_nodes]
        c = ['gray' for node in layer_two_nodes]
        t = [artist_dict[node] for node in layer_two_nodes]

        trace = go.Scatter(
            x = x, 
            y = y, 
            hoverinfo = 'text', 
            hoverlabel=dict(font_size=12, font=dict(color='black')),
            hovertemplate = [f'<b>{j}</b><extra></extra>' for j in t],
            text = t, 
            mode = 'markers',
            marker = dict(
                color = c,
                opacity=0.1,
                size = s,
                sizemin = 4,
                sizeref = 2.5,
                line = dict(
                    width = 0),
            ),
        )

        return trace

    def get_edge_traces_sp(shortest_path_edges, chart_colors, node_pos):

        traces = list()
        for i, edge in enumerate(shortest_path_edges):

            edge = tuple(sorted(edge))
            x0, y0 = node_pos[edge[0]]
            x1, y1 = node_pos[edge[1]]

            x = (x0 + x1) / 2
            y = (y0 + y1) / 2

            trace = go.Scatter(
                x=[x0, x, None], 
                y=[y0, y, None], 
                line=dict(width=5, color=chart_colors[edge[0]]), 
                hoverinfo='none',
                mode='lines',
            )

            traces.append(trace)

            trace = go.Scatter(
                x=[x, x1, None], 
                y=[y, y1, None], 
                line=dict(width=5, color=chart_colors[edge[1]]), 
                hoverinfo='none', 
                mode='lines',
            )

            traces.append(trace)

        return traces

    def get_edge_traces_lo(layer_one_edges, shortest_path, chart_colors, node_pos):

        traces = list()
        for i, edge in enumerate(layer_one_edges):

            edge = tuple(sorted(edge))
            x0, y0 = node_pos[edge[0]]
            x1, y1 = node_pos[edge[1]]

            color = chart_colors[edge[0]] if edge[0] in shortest_path else chart_colors[edge[1]]

            trace = go.Scatter(
                x = [x0, x1, None], 
                y = [y0, y1, None], 
                line = dict(width=2, color=color), 
                opacity = 0.4,
                hoverinfo = 'none',
                mode = 'lines',
            )

            traces.append(trace)

        return traces

    def get_edge_trace_lt(layer_two_edges, node_pos):

        x, y = list(), list()
        for edge in layer_two_edges:

            x0, y0 = node_pos[edge[0]]
            x1, y1 = node_pos[edge[1]]

            x.extend([x0, x1, None])
            y.extend([y0, y1, None])

        trace = go.Scatter(
            x = x, 
            y = y, 
            line=dict(width=1, color='grey'), 
            opacity=0.2,
            hoverinfo='none',
            mode='lines',
        )

        return trace

    lim_1 = 20
    lim_2 = 1

    chart_graph = _graph.copy()

    #l0_nodes = nx.shortest_path(chart_graph, artist_1_id, artist_2_id)
    all_nodes, l1_nodes, l2_nodes = l0_nodes, list(), list()

    # layer 0
    nx.set_node_attributes(chart_graph, {node: {'layer': 0, 'parent': None} for node in l0_nodes})

    # layer 1
    for parent_node in l0_nodes:

        child_nodes = np.array(list(set(chart_graph.neighbors(parent_node)) - set(all_nodes)))

        if chart_graph.nodes[parent_node]['size'] > lim_1:
            
            child_nodes_weight = np.array([chart_graph.edges.get((node, parent_node))['weight'] for node in child_nodes])

            if (child_nodes_weight > 1).sum() >= lim_1:
                child_nodes = list(child_nodes[np.argsort(child_nodes_weight)][-lim_1:])

            else:
                a = child_nodes[child_nodes_weight > 1]
                b = child_nodes[child_nodes_weight == 1]  
                b_sizes = np.array([chart_graph.nodes[node]['size'] for node in b])
                child_nodes = list(np.concatenate([b[np.argsort(b_sizes)][len(a) - lim_1:], a]))
                
        else:
            child_nodes = list(child_nodes)
        
        nx.set_node_attributes(chart_graph, {node: {'layer': 1, 'parent': parent_node} for node in child_nodes})

        l1_nodes = list(set(l1_nodes + child_nodes))
    all_nodes = list(set(all_nodes + l1_nodes))
        
    for parent_node in l1_nodes:
        
        child_nodes = np.array(list(set(chart_graph.neighbors(parent_node)) - set(all_nodes)))

        if chart_graph.nodes[parent_node]['size'] > lim_2:
            
            child_nodes_weight = np.array([chart_graph.edges.get((node, parent_node))['weight'] for node in child_nodes])

            if (child_nodes_weight > 1).sum() >= lim_2:
                child_nodes = list(child_nodes[np.argsort(child_nodes_weight)][-lim_2:])

            else:
                a = child_nodes[child_nodes_weight > 1]
                b = child_nodes[child_nodes_weight == 1]  
                b_sizes = np.array([chart_graph.nodes[node]['size'] for node in b])
                child_nodes = list(np.concatenate([b[np.argsort(b_sizes)][len(a) - lim_2:], a]))
                
        else:
            child_nodes = list(child_nodes)
            
        nx.set_node_attributes(chart_graph, {node: {'layer': 2, 'parent': parent_node} for node in child_nodes})
        
        l2_nodes = list(set(l2_nodes + child_nodes))
    
    all_nodes = list(set(all_nodes + l2_nodes))
        
    # remove nodes
    remove_nodes = list(set(chart_graph.nodes) - set(all_nodes))
    chart_graph.remove_nodes_from(remove_nodes)

    remove_nodes = [node for node, degree in nx.degree(chart_graph, nbunch=l2_nodes) if degree == 1]
    l2_nodes = [node for node in l2_nodes if not node in remove_nodes]
    chart_graph.remove_nodes_from(remove_nodes)
    node_pos = nx.spring_layout(chart_graph, seed=1, iterations=50)

    colors = px.colors.sequential.Agsunset + px.colors.sequential.Bluyl
    chart_colors = colors[::len(colors) // len(l0_nodes)]
    chart_colors = {node:chart_colors[i] for i, node in enumerate(l0_nodes)}
    
    l0_edges =  [tuple(sorted((l0_nodes[i], l0_nodes[i+1]))) for i in range(len(l0_nodes) - 1) if chart_graph.has_edge(l0_nodes[i], l0_nodes[i+1])]
    l1_edges = [tuple(sorted(edge)) for edge in chart_graph.edges if (edge[0] in l0_nodes or edge[1] in l0_nodes) and (tuple(sorted(edge)) not in l0_edges)]
    l2_edges = [tuple(sorted(edge)) for edge in chart_graph.edges if tuple(sorted(edge)) not in l0_edges and tuple(sorted(edge)) not in l1_edges]

    marker_trace_sp = get_marker_trace_sp(l0_nodes, chart_graph, artist_dict, chart_colors, node_pos)
    marker_trace_lo = get_marker_trace_lo(l1_nodes, chart_graph, artist_dict, chart_colors, node_pos)
    marker_trace_lt = get_marker_trace_lt(l2_nodes, chart_graph, artist_dict, node_pos)
    edge_traces_sp = get_edge_traces_sp(l0_edges, chart_colors, node_pos)
    edge_traces_lo = get_edge_traces_lo(l1_edges, l0_nodes, chart_colors, node_pos)
    edge_trace_lt = get_edge_trace_lt(l2_edges, node_pos)

    data = [edge_trace_lt, marker_trace_lt] + edge_traces_lo + [marker_trace_lo] + edge_traces_sp + [marker_trace_sp]
    fig = go.Figure(data = data, layout = get_layout())
    
    return fig
