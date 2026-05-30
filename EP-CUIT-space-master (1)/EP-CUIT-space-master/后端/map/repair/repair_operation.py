from flask import Blueprint, request, jsonify
import pymysql
import json
import os
import uuid
from .db import get_db

repair_operation_bp = Blueprint('repair_operation', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "images", "repair")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@repair_operation_bp.route('/repair', methods=['POST'])
def create_repair():
    db = None
    cursor = None
    try:
        print(f"\n=== NEW REPAIR REQUEST ===")
        print(f"Content-Type: {request.content_type}")
        
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        repair_category_id = request.form.get("repair_category_id", "").strip()
        reporter_id = request.form.get("reporter_id", "").strip()
        priority = request.form.get("priority", "1")
        lng = request.form.get("lng", "").strip()
        lat = request.form.get("lat", "").strip()
        
        if not title and request.data:
            try:
                data = json.loads(request.data.decode('utf-8'))
                title = str(data.get('title', '')).strip()
                description = str(data.get('description', '')).strip()
                repair_category_id = str(data.get('repair_category_id', '')).strip()
                reporter_id = str(data.get('reporter_id', '')).strip()
                priority = str(data.get('priority', '1'))
                lng = str(data.get('lng', '')).strip()
                lat = str(data.get('lat', '')).strip()
                print("Data loaded from JSON body")
            except Exception as e:
                print(f"Failed to parse JSON: {e}")
        
        print(f"Parsed values:")
        print(f"  title: '{title}'")
        print(f"  description: '{description}'")
        print(f"  repair_category_id: '{repair_category_id}'")
        print(f"  reporter_id: '{reporter_id}'")
        print(f"  priority: '{priority}'")
        print(f"  lng: '{lng}'")
        print(f"  lat: '{lat}'")
        
        if not title:
            return jsonify({'success': False, 'message': '缺少必要参数: title'}), 400
        if not description:
            return jsonify({'success': False, 'message': '缺少必要参数: description'}), 400
        if not repair_category_id:
            return jsonify({'success': False, 'message': '缺少必要参数: repair_category_id'}), 400
        if not reporter_id:
            return jsonify({'success': False, 'message': '缺少必要参数: reporter_id'}), 400

        db = get_db()
        cursor = db.cursor()

        location_id = None
        if lng and lat:
            try:
                lng_float = float(lng)
                lat_float = float(lat)
                
                if not (-180 <= lng_float <= 180) or not (-90 <= lat_float <= 90):
                    print(f"Invalid coordinates: lng={lng_float}, lat={lat_float}")
                else:
                    cursor.execute(
                        "SELECT location_id FROM location WHERE longitude = %s AND latitude = %s LIMIT 1", 
                        (lng_float, lat_float)
                    )
                    result = cursor.fetchone()
                    if result:
                        location_id = result[0]
                        print(f"Found existing location_id: {location_id}")
                    else:
                        cursor.execute(
                            "INSERT INTO location (name, longitude, latitude, detail) VALUES (%s, %s, %s, %s)", 
                            (title, lng_float, lat_float, description)
                        )
                        db.commit()
                        location_id = cursor.lastrowid
                        print(f"Created new location with location_id: {location_id}")
            except ValueError as e:
                print(f"Invalid coordinate format: {e}")
            except Exception as e:
                print(f"Location error: {e}")

        images_json = None
        if 'images' in request.files:
            uploaded_files = request.files.getlist('images')
            if uploaded_files:
                image_paths = []
                for file in uploaded_files:
                    if file and file.filename:
                        ext = os.path.splitext(file.filename)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
                            filename = f"repair_{uuid.uuid4().hex}{ext}"
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            file.save(filepath)
                            image_paths.append(f"/images/repair/{filename}")
                if image_paths:
                    images_json = json.dumps(image_paths)

        sql = """
        INSERT INTO repair (title, description, repair_category_id, location_id, reporter_id, 
                           priority, images, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 0)
        """
        cursor.execute(sql, (
            title,
            description,
            repair_category_id,
            location_id,
            reporter_id,
            priority,
            images_json
        ))
        db.commit()
        repair_id = cursor.lastrowid
        
        print(f"Repair created successfully: repair_id={repair_id}, location_id={location_id}")
        return jsonify({
            'success': True, 
            'repair_id': repair_id,
            'location_id': location_id
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        if db:
            db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@repair_operation_bp.route('/repair/<int:repair_id>', methods=['PUT'])
def update_repair(repair_id):
    db = get_db()
    cursor = db.cursor()
    try:
        data = request.get_json()
        
        status = data.get('status')
        process_note = data.get('process_note')
        assignee_id = data.get('assignee_id')
        
        sql = "UPDATE repair SET "
        params = []
        
        if status is not None:
            sql += "status = %s, "
            params.append(status)
        if process_note is not None:
            sql += "process_note = %s, "
            params.append(process_note)
        if assignee_id is not None:
            sql += "assignee_id = %s, "
            params.append(assignee_id)
        
        sql = sql.rstrip(', ')
        sql += " WHERE repair_id = %s"
        params.append(repair_id)
        
        cursor.execute(sql, params)
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()


@repair_operation_bp.route('/repair/<int:repair_id>', methods=['DELETE'])
def delete_repair(repair_id):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM repair WHERE repair_id = %s", (repair_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': '报修记录不存在'}), 404
        
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        db.close()
