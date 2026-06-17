#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy
import os
import glob

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
            # Skip points without timestamps
            fixed_trkpts.append(pt)
            prev_pt = pt
            continue
            
        curr_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
        
        if prev_time and prev_pt:
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
        if type_elem is None:
            type_elem = ET.Element('type')
            type_elem.text = '9'
            if name is not None:
                trk.insert(list(trk).index(name) + 1, type_elem)
            else:
                trk.insert(0, type_elem)
    
    return tree

def convert_gpx_to_garmin(input_file, output_file):
    """Convert a single GPX file to Garmin-compatible format"""
    try:
        # Step 1: Fix timestamps
        tree = fix_gpx_timestamps(input_file)
        
        # Step 2: Enhance for Garmin
        tree = enhance_gpx_for_garmin(tree)
        
        # Write output
        tree.write(output_file, encoding='UTF-8', xml_declaration=True)
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    input_dir = '/home/ondarenc/CascadeProjects/garminport/GPX Mi'
    output_dir = '/home/ondarenc/CascadeProjects/garminport/GPX Garmin'
    
    # Get all GPX files (exclude CSV and py files)
    gpx_files = glob.glob(os.path.join(input_dir, '*.gpx'))
    gpx_files = [f for f in gpx_files if not f.endswith('.csv') and not f.endswith('.py')]
    
    print(f"Found {len(gpx_files)} GPX files to convert")
    
    success = 0
    failed = []
    
    for i, input_file in enumerate(gpx_files, 1):
        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename)
        
        print(f"[{i}/{len(gpx_files)}] Converting {filename}...")
        
        ok, error = convert_gpx_to_garmin(input_file, output_file)
        
        if ok:
            success += 1
            print(f"  ✓ Saved to {output_file}")
        else:
            failed.append((filename, error))
            print(f"  ✗ Failed: {error}")
    
    print(f"\n=== Summary ===")
    print(f"Converted: {success}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed conversions:")
        for filename, error in failed:
            print(f"  - {filename}: {error}")

if __name__ == '__main__':
    main()
