#!/usr/bin/env python3
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy
import os
import csv
import urllib.request
from urllib.parse import urlparse
import tempfile
import shutil
import zipfile

app = Flask(__name__)
CORS(app)

# Temporary directory for processing
TEMP_DIR = tempfile.mkdtemp()

def fix_gpx_timestamps(input_file):
    """Fix GPX file by filling timestamp gaps to create continuous time-series data"""
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    trkpts = root.findall('.//gpx:trkpt', ns)
    if not trkpts:
        trkpts = root.findall('.//trkpt')
        ns = None
    
    fixed_trkpts = []
    prev_time = None
    prev_pt = None
    
    for pt in trkpts:
        if ns:
            time_elem = pt.find('gpx:time', ns)
        else:
            time_elem = pt.find('time')
        
        if time_elem is None or not time_elem.text:
            fixed_trkpts.append(pt)
            prev_pt = pt
            continue
            
        curr_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
        
        if prev_time is not None and prev_pt is not None:
            diff = (curr_time - prev_time).total_seconds()
            
            if diff > 1:
                num_interpolated = int(diff) - 1
                lat_step = (float(pt.attrib['lat']) - float(prev_pt.attrib['lat'])) / (num_interpolated + 1)
                lon_step = (float(pt.attrib['lon']) - float(prev_pt.attrib['lon'])) / (num_interpolated + 1)
                
                for j in range(num_interpolated):
                    new_pt = copy.deepcopy(prev_pt)
                    new_pt.attrib['lat'] = str(float(prev_pt.attrib['lat']) + lat_step * (j + 1))
                    new_pt.attrib['lon'] = str(float(prev_pt.attrib['lon']) + lon_step * (j + 1))
                    
                    interp_time = prev_time + timedelta(seconds=j+1)
                    if ns:
                        new_pt.find('gpx:time', ns).text = interp_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    else:
                        new_pt.find('time').text = interp_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    
                    fixed_trkpts.append(new_pt)
        
        fixed_trkpts.append(pt)
        prev_time = curr_time
        prev_pt = pt
    
    if ns:
        trkseg = root.find('.//gpx:trkseg', ns)
    else:
        trkseg = root.find('.//trkseg')
    
    if trkseg is not None:
        for pt in trkpts:
            trkseg.remove(pt)
        
        for pt in fixed_trkpts:
            trkseg.append(pt)
    
    return tree

def enhance_gpx_for_garmin(tree):
    """Enhance GPX tree with Garmin-specific namespaces and metadata"""
    root = tree.getroot()
    
    ET.register_namespace('', 'http://www.topografix.com/GPX/1/1')
    ET.register_namespace('gpxtpx', 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1')
    ET.register_namespace('gpxx', 'http://www.garmin.com/xmlschemas/GpxExtensions/v3')
    
    root.set('xmlns', 'http://www.topografix.com/GPX/1/1')
    root.set('xmlns:gpxtpx', 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1')
    root.set('xmlns:gpxx', 'http://www.garmin.com/xmlschemas/GpxExtensions/v3')
    root.set('version', '1.1')
    root.set('creator', 'Garmin Compatible')
    
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    trkpts = root.findall('.//gpx:trkpt', ns)
    if not trkpts:
        trkpts = root.findall('.//trkpt')
        ns = None
    
    times = []
    for pt in trkpts:
        if ns:
            time_elem = pt.find('gpx:time', ns)
        else:
            time_elem = pt.find('time')
        if time_elem is not None and time_elem.text:
            try:
                times.append(datetime.fromisoformat(time_elem.text.replace('Z', '+00:00')))
            except:
                pass
    
    if times:
        min_time = min(times)
        
        metadata = ET.Element('metadata')
        time_elem = ET.SubElement(metadata, 'time')
        time_elem.text = min_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        lats = [float(pt.attrib['lat']) for pt in trkpts]
        lons = [float(pt.attrib['lon']) for pt in trkpts]
        
        bounds = ET.SubElement(metadata, 'bounds')
        bounds.set('minlat', str(min(lats)))
        bounds.set('maxlat', str(max(lats)))
        bounds.set('minlon', str(min(lons)))
        bounds.set('maxlon', str(max(lons)))
        
        trk = root.find('.//gpx:trk', ns) if ns else root.find('.//trk')
        if trk is not None:
            idx = list(root).index(trk)
            root.insert(idx, metadata)
    
    for pt in trkpts:
        if ns:
            ele = pt.find('gpx:ele', ns)
        else:
            ele = pt.find('ele')
        
        if ele is None:
            ele = ET.Element('ele')
            ele.text = '0'
            pt.insert(0, ele)
    
    trk = root.find('.//gpx:trk', ns) if ns else root.find('.//trk')
    if trk is not None:
        name = trk.find('gpx:name', ns) if ns else trk.find('name')
        if name is not None:
            name.text = 'Outdoor Run'
        
        type_elem = trk.find('gpx:type', ns) if ns else trk.find('type')
        if type_elem is None and name is not None:
            type_elem = ET.Element('type')
            type_elem.text = '9'
            trk.insert(list(trk).index(name) + 1, type_elem)
        elif type_elem is None:
            type_elem = ET.Element('type')
            type_elem.text = '9'
            trk.insert(0, type_elem)
    
    return tree

def convert_gpx_to_garmin(input_file, output_file):
    """Convert a single GPX file to Garmin-compatible format"""
    try:
        tree = fix_gpx_timestamps(input_file)
        tree = enhance_gpx_for_garmin(tree)
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
        return True, None
    except Exception as e:
        return False, str(e)

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    """Upload CSV file and process GPX conversions"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    # Create temporary session directory
    session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Save uploaded CSV
    csv_path = os.path.join(session_dir, 'input.csv')
    file.save(csv_path)
    
    # Read CSV and extract GPX URLs
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        if not rows:
            return jsonify({'error': 'CSV is empty'}), 400
        
        gpx_urls = [row['GPX'] for row in rows if row.get('GPX')]
        
        if not gpx_urls:
            return jsonify({'error': 'No GPX URLs found in CSV'}), 400
        
        # Download and convert GPX files
        converted_files = []
        failed_files = []
        
        for i, url in enumerate(gpx_urls):
            try:
                # Extract filename from URL
                parsed = urlparse(url)
                filename = os.path.basename(parsed.path)
                
                # Download GPX
                temp_gpx = os.path.join(session_dir, f'original_{filename}')
                urllib.request.urlretrieve(url, temp_gpx)
                
                # Convert to Garmin format
                output_gpx = os.path.join(session_dir, filename)
                success, error = convert_gpx_to_garmin(temp_gpx, output_gpx)
                
                if success:
                    converted_files.append(filename)
                    os.remove(temp_gpx)  # Remove original
                else:
                    failed_files.append((filename, error))
                    if os.path.exists(temp_gpx):
                        os.remove(temp_gpx)
            
            except Exception as e:
                failed_files.append((filename if 'filename' in locals() else 'unknown', str(e)))
        
        # Create ZIP file with all converted GPX files
        zip_path = os.path.join(session_dir, 'garmin_gpx_files.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for filename in converted_files:
                file_path = os.path.join(session_dir, filename)
                if os.path.exists(file_path):
                    zipf.write(file_path, filename)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'converted': len(converted_files),
            'failed': len(failed_files),
            'failed_files': failed_files
        })
    
    except Exception as e:
        return jsonify({'error': f'Error processing CSV: {str(e)}'}), 500

@app.route('/api/download/<session_id>', methods=['GET'])
def download_files(session_id):
    """Download the ZIP file of converted GPX files"""
    session_dir = os.path.join(TEMP_DIR, session_id)
    zip_path = os.path.join(session_dir, 'garmin_gpx_files.zip')
    
    if not os.path.exists(zip_path):
        return jsonify({'error': 'Files not found or expired'}), 404
    
    return send_file(zip_path, as_attachment=True, download_name='garmin_gpx_files.zip')

@app.route('/api/status/<session_id>', methods=['GET'])
def get_status(session_id):
    """Get status of conversion"""
    session_dir = os.path.join(TEMP_DIR, session_id)
    zip_path = os.path.join(session_dir, 'garmin_gpx_files.zip')
    
    exists = os.path.exists(zip_path)
    return jsonify({'ready': exists})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
