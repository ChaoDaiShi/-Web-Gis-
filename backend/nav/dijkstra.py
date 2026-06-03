import heapq

def build_graph(nodes, edges):
    """构建邻接表图"""
    graph = {node['node_id']: [] for node in nodes}
    
    for edge in edges:
        from_node = edge['from_node_id']
        to_node = edge['to_node_id']
        length = edge['length']
        
        graph[from_node].append({
            'to': to_node,
            'length': length,
            'edge_id': edge['edge_id'],
            'name': edge.get('name')
        })
        
        if edge.get('is_bidirectional', True):
            graph[to_node].append({
                'to': from_node,
                'length': length,
                'edge_id': edge['edge_id'],
                'name': edge.get('name')
            })
    
    return graph

def dijkstra(graph, start_node_id, end_node_id):
    """
    迪杰斯特拉算法实现
    返回从起点到终点的最短路径
    """
    if start_node_id not in graph or end_node_id not in graph:
        return None
    
    # 距离字典，存储到每个节点的最短距离
    distances = {node: float('inf') for node in graph}
    distances[start_node_id] = 0
    
    # 前驱节点字典，用于回溯路径
    previous = {node: None for node in graph}
    
    # 优先队列，(距离, 节点)
    heap = [(0, start_node_id)]
    
    while heap:
        current_dist, current_node = heapq.heappop(heap)
        
        # 如果已经到达终点，可以提前退出
        if current_node == end_node_id:
            break
        
        # 如果当前距离大于已知最短距离，跳过
        if current_dist > distances[current_node]:
            continue
        
        # 遍历相邻节点
        for neighbor in graph[current_node]:
            neighbor_node = neighbor['to']
            weight = neighbor['length']
            distance = current_dist + weight
            
            # 如果找到更短的路径
            if distance < distances[neighbor_node]:
                distances[neighbor_node] = distance
                previous[neighbor_node] = {
                    'from': current_node,
                    'edge_id': neighbor['edge_id'],
                    'name': neighbor.get('name'),
                    'length': weight
                }
                heapq.heappush(heap, (distance, neighbor_node))
    
    # 回溯路径
    if previous[end_node_id] is None:
        return None
    
    path = []
    current = end_node_id
    while current is not None:
        prev_info = previous[current]
        if prev_info:
            path.insert(0, {
                'from_node': prev_info['from'],
                'to_node': current,
                'edge_id': prev_info['edge_id'],
                'name': prev_info['name'],
                'length': prev_info['length']
            })
        current = prev_info['from'] if prev_info else None
    
    return {
        'total_distance': distances[end_node_id],
        'path': path
    }

def get_path_coordinates(path, nodes):
    """将路径转换为坐标序列"""
    if not path or not path.get('path'):
        return []
    
    node_dict = {node['node_id']: node for node in nodes}
    coordinates = []
    
    # 添加起点坐标
    first_edge = path['path'][0]
    start_node = node_dict.get(first_edge['from_node'])
    if start_node:
        coordinates.append([start_node['lng'], start_node['lat']])
    
    # 添加中间节点坐标
    for edge in path['path']:
        end_node = node_dict.get(edge['to_node'])
        if end_node:
            coordinates.append([end_node['lng'], end_node['lat']])
    
    return coordinates
