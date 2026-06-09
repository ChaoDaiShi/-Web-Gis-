import requests
import json
from .gaode_config import GAODE_API_KEY, GAODE_API_BASE_URL, DEFAULT_CAMPUS_BOUNDARY

def get_direction_walking(start_lng, start_lat, end_lng, end_lat):
    """
    调用高德步行路径规划API
    :param start_lng: 起点经度
    :param start_lat: 起点纬度
    :param end_lng: 终点经度
    :param end_lat: 终点纬度
    :return: 路径数据
    """
    url = f"{GAODE_API_BASE_URL}/direction/walking"
    params = {
        'key': GAODE_API_KEY,
        'origin': f'{start_lng},{start_lat}',
        'destination': f'{end_lng},{end_lat}',
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1':
            return {
                'success': True,
                'data': {
                    'route': data.get('route', {}),
                    'distance': data.get('route', {}).get('distance', '0'),
                    'duration': data.get('route', {}).get('duration', '0'),
                    'paths': data.get('route', {}).get('paths', [])
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', '获取路径失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def get_direction_driving(start_lng, start_lat, end_lng, end_lat):
    """
    调用高德驾车路径规划API
    :param start_lng: 起点经度
    :param start_lat: 起点纬度
    :param end_lng: 终点经度
    :param end_lat: 终点纬度
    :return: 路径数据
    """
    url = f"{GAODE_API_BASE_URL}/direction/driving"
    params = {
        'key': GAODE_API_KEY,
        'origin': f'{start_lng},{start_lat}',
        'destination': f'{end_lng},{end_lat}',
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1':
            return {
                'success': True,
                'data': {
                    'route': data.get('route', {}),
                    'distance': data.get('route', {}).get('distance', '0'),
                    'duration': data.get('route', {}).get('duration', '0'),
                    'paths': data.get('route', {}).get('paths', [])
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', '获取路径失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def get_direction_bicycling(start_lng, start_lat, end_lng, end_lat):
    """
    调用高德骑行路径规划API
    :param start_lng: 起点经度
    :param start_lat: 起点纬度
    :param end_lng: 终点经度
    :param end_lat: 终点纬度
    :return: 路径数据
    """
    url = f"{GAODE_API_BASE_URL}/direction/bicycling"
    params = {
        'key': GAODE_API_KEY,
        'origin': f'{start_lng},{start_lat}',
        'destination': f'{end_lng},{end_lat}',
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1':
            return {
                'success': True,
                'data': {
                    'route': data.get('route', {}),
                    'distance': data.get('route', {}).get('distance', '0'),
                    'duration': data.get('route', {}).get('duration', '0'),
                    'paths': data.get('route', {}).get('paths', [])
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', '获取路径失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def geocode(address, city='成都市'):
    """
    调用高德地理编码API
    :param address: 地址
    :param city: 城市
    :return: 坐标数据
    """
    url = f"{GAODE_API_BASE_URL}/geocode/geo"
    params = {
        'key': GAODE_API_KEY,
        'address': address,
        'city': city,
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1' and data.get('geocodes'):
            geocode_info = data['geocodes'][0]
            location = geocode_info.get('location', '').split(',')
            return {
                'success': True,
                'data': {
                    'lng': float(location[0]) if len(location) > 0 else None,
                    'lat': float(location[1]) if len(location) > 1 else None,
                    'formatted_address': geocode_info.get('formatted_address'),
                    'address_component': geocode_info.get('addressComponent')
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', '地理编码失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def reverse_geocode(lng, lat):
    """
    调用高德逆地理编码API
    :param lng: 经度
    :param lat: 纬度
    :return: 地址数据
    """
    url = f"{GAODE_API_BASE_URL}/geocode/regeo"
    params = {
        'key': GAODE_API_KEY,
        'location': f'{lng},{lat}',
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1':
            regeocode_info = data.get('regeocode', {})
            return {
                'success': True,
                'data': {
                    'formatted_address': regeocode_info.get('formatted_address'),
                    'address_component': regeocode_info.get('addressComponent'),
                    'pois': regeocode_info.get('pois', [])
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', '逆地理编码失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def search_poi(keywords, city='成都市', types=None, page=1, page_size=20):
    """
    调用高德POI搜索API
    :param keywords: 搜索关键词
    :param city: 城市
    :param types: POI类型
    :param page: 页码
    :param page_size: 每页数量
    :return: POI列表
    """
    url = f"{GAODE_API_BASE_URL}/place/text"
    params = {
        'key': GAODE_API_KEY,
        'keywords': keywords,
        'city': city,
        'page': page,
        'offset': page_size,
        'output': 'json'
    }
    
    if types:
        params['types'] = types
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1':
            return {
                'success': True,
                'data': {
                    'count': int(data.get('count', '0')),
                    'pois': data.get('pois', []),
                    'suggestion': data.get('suggestion', {})
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', 'POI搜索失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def search_poi_around(lng, lat, radius=1000, keywords=None, types=None, page=1, page_size=20):
    """
    调用高德周边搜索API
    :param lng: 中心点经度
    :param lat: 中心点纬度
    :param radius: 搜索半径(米)
    :param keywords: 搜索关键词
    :param types: POI类型
    :param page: 页码
    :param page_size: 每页数量
    :return: POI列表
    """
    url = f"{GAODE_API_BASE_URL}/place/around"
    params = {
        'key': GAODE_API_KEY,
        'location': f'{lng},{lat}',
        'radius': radius,
        'page': page,
        'offset': page_size,
        'output': 'json'
    }
    
    if keywords:
        params['keywords'] = keywords
    if types:
        params['types'] = types
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1':
            return {
                'success': True,
                'data': {
                    'count': int(data.get('count', '0')),
                    'pois': data.get('pois', []),
                    'suggestion': data.get('suggestion', {})
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', '周边搜索失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }

def get_weather(city='成都'):
    """
    调用高德天气API
    :param city: 城市名或城市编码
    :return: 天气数据
    """
    url = f"{GAODE_API_BASE_URL}/weather/weatherInfo"
    params = {
        'key': GAODE_API_KEY,
        'city': city,
        'output': 'json'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == '1' and data.get('lives'):
            return {
                'success': True,
                'data': {
                    'weather': data['lives'][0]
                }
            }
        else:
            return {
                'success': False,
                'message': data.get('info', '获取天气失败')
            }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }