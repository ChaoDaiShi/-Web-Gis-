from flask import Blueprint, request, jsonify
from .db import get_all_nodes, get_all_edges, find_nearest_node, add_node, add_edge
from .dijkstra import build_graph, dijkstra, get_path_coordinates
from .gaode_service import (
    get_direction_walking,
    get_direction_driving,
    get_direction_bicycling,
    geocode,
    reverse_geocode,
    search_poi,
    search_poi_around,
    get_weather
)

nav_bp = Blueprint('nav', __name__)

@nav_bp.route('/nodes', methods=['GET'])
def get_nodes():
    """获取所有导航节点"""
    campus_id = request.args.get('campus_id', 'campus_1')
    try:
        nodes = get_all_nodes(campus_id)
        return jsonify({'success': True, 'data': nodes})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@nav_bp.route('/edges', methods=['GET'])
def get_edges():
    """获取所有路段"""
    campus_id = request.args.get('campus_id', 'campus_1')
    try:
        edges = get_all_edges(campus_id)
        return jsonify({'success': True, 'data': edges})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@nav_bp.route('/path', methods=['GET'])
def get_path():
    """获取两点之间的最短路径（使用本地导航）"""
    try:
        start_lng = float(request.args.get('start_lng'))
        start_lat = float(request.args.get('start_lat'))
        end_lng = float(request.args.get('end_lng'))
        end_lat = float(request.args.get('end_lat'))
        campus_id = request.args.get('campus_id', 'campus_1')
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    try:
        start_node = find_nearest_node(start_lng, start_lat, campus_id)
        end_node = find_nearest_node(end_lng, end_lat, campus_id)
        
        if not start_node or not end_node:
            return jsonify({'success': False, 'message': '未找到附近的导航节点'}), 404
        
        nodes = get_all_nodes(campus_id)
        edges = get_all_edges(campus_id)
        
        graph = build_graph(nodes, edges)
        path_result = dijkstra(graph, start_node['node_id'], end_node['node_id'])
        
        if not path_result:
            return jsonify({'success': False, 'message': '无法找到路径'}), 404
        
        coordinates = get_path_coordinates(path_result, nodes)
        
        walking_speed_m_per_min = 85
        estimated_time_minutes = int(path_result['total_distance'] / walking_speed_m_per_min)
        
        return jsonify({
            'success': True,
            'data': {
                'start_node': start_node,
                'end_node': end_node,
                'total_distance': path_result['total_distance'],
                'estimated_time': estimated_time_minutes,
                'path': path_result['path'],
                'coordinates': coordinates
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@nav_bp.route('/nearest-node', methods=['GET'])
def nearest_node():
    """获取最近的导航节点"""
    try:
        lng = float(request.args.get('lng'))
        lat = float(request.args.get('lat'))
        campus_id = request.args.get('campus_id', 'campus_1')
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    try:
        node = find_nearest_node(lng, lat, campus_id)
        if node:
            return jsonify({'success': True, 'data': node})
        else:
            return jsonify({'success': False, 'message': '未找到附近的导航节点'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@nav_bp.route('/node', methods=['POST'])
def create_node():
    """添加导航节点"""
    data = request.get_json()
    if not data or 'lng' not in data or 'lat' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    try:
        name = data.get('name')
        lng = float(data['lng'])
        lat = float(data['lat'])
        node_type = data.get('type', 'intersection')
        campus_id = data.get('campus_id', 'campus_1')
        
        node_id = add_node(name, lng, lat, node_type, campus_id)
        return jsonify({'success': True, 'data': {'node_id': node_id}}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@nav_bp.route('/edge', methods=['POST'])
def create_edge():
    """添加路段"""
    data = request.get_json()
    if not data or 'from_node_id' not in data or 'to_node_id' not in data or 'length' not in data:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    try:
        from_node_id = int(data['from_node_id'])
        to_node_id = int(data['to_node_id'])
        length = float(data['length'])
        name = data.get('name')
        is_bidirectional = data.get('is_bidirectional', True)
        campus_id = data.get('campus_id', 'campus_1')
        
        edge_id = add_edge(from_node_id, to_node_id, length, name, is_bidirectional, campus_id)
        return jsonify({'success': True, 'data': {'edge_id': edge_id}}), 201
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@nav_bp.route('/gaode/direction/walking', methods=['GET'])
def gaode_walking():
    """调用高德步行路径规划API"""
    try:
        start_lng = float(request.args.get('start_lng'))
        start_lat = float(request.args.get('start_lat'))
        end_lng = float(request.args.get('end_lng'))
        end_lat = float(request.args.get('end_lat'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = get_direction_walking(start_lng, start_lat, end_lng, end_lat)
    return jsonify(result)

@nav_bp.route('/gaode/direction/driving', methods=['GET'])
def gaode_driving():
    """调用高德驾车路径规划API"""
    try:
        start_lng = float(request.args.get('start_lng'))
        start_lat = float(request.args.get('start_lat'))
        end_lng = float(request.args.get('end_lng'))
        end_lat = float(request.args.get('end_lat'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = get_direction_driving(start_lng, start_lat, end_lng, end_lat)
    return jsonify(result)

@nav_bp.route('/gaode/direction/bicycling', methods=['GET'])
def gaode_bicycling():
    """调用高德骑行路径规划API"""
    try:
        start_lng = float(request.args.get('start_lng'))
        start_lat = float(request.args.get('start_lat'))
        end_lng = float(request.args.get('end_lng'))
        end_lat = float(request.args.get('end_lat'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = get_direction_bicycling(start_lng, start_lat, end_lng, end_lat)
    return jsonify(result)

@nav_bp.route('/gaode/geocode', methods=['GET'])
def gaode_geocode():
    """调用高德地理编码API"""
    address = request.args.get('address')
    city = request.args.get('city', '成都市')
    
    if not address:
        return jsonify({'success': False, 'message': '缺少地址参数'}), 400
    
    result = geocode(address, city)
    return jsonify(result)

@nav_bp.route('/gaode/reverse-geocode', methods=['GET'])
def gaode_reverse_geocode():
    """调用高德逆地理编码API"""
    try:
        lng = float(request.args.get('lng'))
        lat = float(request.args.get('lat'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    result = reverse_geocode(lng, lat)
    return jsonify(result)

@nav_bp.route('/gaode/poi/search', methods=['GET'])
def gaode_poi_search():
    """调用高德POI搜索API"""
    keywords = request.args.get('keywords')
    city = request.args.get('city', '成都市')
    types = request.args.get('types')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    
    if not keywords:
        return jsonify({'success': False, 'message': '缺少关键词参数'}), 400
    
    result = search_poi(keywords, city, types, page, page_size)
    return jsonify(result)

@nav_bp.route('/gaode/poi/around', methods=['GET'])
def gaode_poi_around():
    """调用高德周边搜索API"""
    try:
        lng = float(request.args.get('lng'))
        lat = float(request.args.get('lat'))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    radius = int(request.args.get('radius', 1000))
    keywords = request.args.get('keywords')
    types = request.args.get('types')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    
    result = search_poi_around(lng, lat, radius, keywords, types, page, page_size)
    return jsonify(result)

@nav_bp.route('/gaode/weather', methods=['GET'])
def gaode_weather():
    """调用高德天气API"""
    city = request.args.get('city', '成都')
    
    result = get_weather(city)
    return jsonify(result)

@nav_bp.route('/gaode/path', methods=['GET'])
def gaode_path():
    """获取路径规划（优先使用高德API，失败时回退到本地导航）"""
    try:
        start_lng = float(request.args.get('start_lng'))
        start_lat = float(request.args.get('start_lat'))
        end_lng = float(request.args.get('end_lng'))
        end_lat = float(request.args.get('end_lat'))
        mode = request.args.get('mode', 'walking')
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    gaode_result = None
    
    if mode == 'walking':
        gaode_result = get_direction_walking(start_lng, start_lat, end_lng, end_lat)
    elif mode == 'driving':
        gaode_result = get_direction_driving(start_lng, start_lat, end_lng, end_lat)
    elif mode == 'bicycling':
        gaode_result = get_direction_bicycling(start_lng, start_lat, end_lng, end_lat)
    else:
        return jsonify({'success': False, 'message': '无效的出行方式'}), 400
    
    if gaode_result.get('success'):
        return jsonify(gaode_result)
    else:
        return get_path()

@nav_bp.route('/route', methods=['GET'])
def route():
    """统一路径规划接口"""
    try:
        start_lng = float(request.args.get('start_lng'))
        start_lat = float(request.args.get('start_lat'))
        end_lng = float(request.args.get('end_lng'))
        end_lat = float(request.args.get('end_lat'))
        mode = request.args.get('mode', 'walking')
        use_gaode = request.args.get('use_gaode', 'true').lower() == 'true'
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400
    
    if use_gaode:
        return gaode_path()
    else:
        return get_path()