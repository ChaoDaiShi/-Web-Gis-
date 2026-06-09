import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

os.environ['FLASK_ENV'] = 'production'

from app import app

def handler(event, context):
    environ = {
        'REQUEST_METHOD': event['requestContext']['http']['method'],
        'SCRIPT_NAME': '',
        'PATH_INFO': event.get('rawPath', event.get('path', '/')),
        'QUERY_STRING': event.get('queryStringParameters', ''),
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '80',
        'SERVER_PROTOCOL': 'HTTP/1.1',
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': 'https',
        'wsgi.input': None,
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False,
    }
    
    headers = {}
    if 'headers' in event.get('requestContext', {}).get('http', {}):
        for key, value in event['requestContext']['http']['headers'].items():
            wsgi_key = 'HTTP_' + key.upper().replace('-', '_')
            environ[wsgi_key] = value
            if key.lower() == 'content-type':
                environ['CONTENT_TYPE'] = value
            if key.lower() == 'content-length':
                environ['CONTENT_LENGTH'] = value
    
    body = event.get('body', '')
    if body:
        import io
        environ['wsgi.input'] = io.BytesIO(body.encode('utf-8'))
    
    response_body = []
    response_status = None
    response_headers = []
    
    def start_response(status, headers, exc_info=None):
        nonlocal response_status, response_headers
        response_status = status
        response_headers = headers
        return response_body.append
    
    result = app(environ, start_response)
    
    for part in result:
        if isinstance(part, bytes):
            response_body.append(part)
        else:
            response_body.append(part.encode('utf-8'))
    
    response_dict = {
        'statusCode': int(response_status.split()[0]),
        'headers': dict(response_headers),
        'body': b''.join(response_body).decode('utf-8')
    }
    
    return response_dict
