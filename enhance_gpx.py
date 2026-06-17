#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy

def enhance_gpx_for_garmin(input_file, output_file):
    """Enhance GPX file with Garmin-specific namespaces and metadata"""
    
    # Parse the GPX file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Register GPX namespace
    ET.register_namespace('', 'http://www.topografix.com/GPX/1/1')
    ET.register_namespace('gpxtpx', 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1')
    ET.register_namespace('gpxx', 'http://www.garmin.com/xmlschemas/GpxExtensions/v3')
    
    # Update root element with proper namespaces
    root.set('xmlns', 'http://www.topografix.com/GPX/1/1')
    root.set('xmlns:gpxtpx', 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1')
    root.set('xmlns:gpxx', 'http://www.garmin.com/xmlschemas/GpxExtensions/v3')
    root.set('version', '1.1')
    root.set('creator', 'Garmin Compatible')
    
    # Get all track points with namespace handling
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    trkpts = root.findall('.//gpx:trkpt', ns)
    if not trkpts:
        trkpts = root.findall('.//trkpt')
        ns = None
    
    # Get time bounds
    times = []
    for pt in trkpts:
        if ns:
            time_elem = pt.find('gpx:time', ns)
        else:
            time_elem = pt.find('time')
        if time_elem is not None and time_elem.text:
            times.append(datetime.fromisoformat(time_elem.text.replace('Z', '+00:00')))
    
    if times:
        min_time = min(times)
        max_time = max(times)
        
        # Create metadata element
        metadata = ET.Element('metadata')
        
        # Add time bounds
        time_elem = ET.SubElement(metadata, 'time')
        time_elem.text = min_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Add bounds if we have coordinates
        lats = [float(pt.attrib['lat']) for pt in trkpts]
        lons = [float(pt.attrib['lon']) for pt in trkpts]
        
        bounds = ET.SubElement(metadata, 'bounds')
        bounds.set('minlat', str(min(lats)))
        bounds.set('maxlat', str(max(lats)))
        bounds.set('minlon', str(min(lons)))
        bounds.set('maxlon', str(max(lons)))
        
        # Insert metadata after root, before track
        trk = root.find('.//gpx:trk', ns) if ns else root.find('.//trk')
        if trk is not None:
            idx = list(root).index(trk)
            root.insert(idx, metadata)
    
    # Add elevation tags (set to 0 if not present, Garmin prefers ele tags)
    for pt in trkpts:
        if ns:
            ele = pt.find('gpx:ele', ns)
        else:
            ele = pt.find('ele')
        
        if ele is None:
            # Add elevation tag with 0 (can be estimated from DEM if needed)
            ele = ET.Element('ele')
            ele.text = '0'
            pt.insert(0, ele)
    
    # Update track name to be more descriptive
    trk = root.find('.//gpx:trk', ns) if ns else root.find('.//trk')
    if trk is not None:
        name = trk.find('gpx:name', ns) if ns else trk.find('name')
        if name is not None:
            name.text = 'Outdoor Run'
        
        # Add track type
        type_elem = trk.find('gpx:type', ns) if ns else trk.find('type')
        if type_elem is None:
            type_elem = ET.Element('type')
            type_elem.text = '9'  # Garmin type for running
            trk.insert(list(trk).index(name) + 1 if name else 0, type_elem)
    
    # Write output file with proper formatting
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"Enhanced GPX file written to: {output_file}")
    print(f"  - Added Garmin namespaces")
    print(f"  - Added metadata with time bounds")
    print(f"  - Added elevation tags")
    print(f"  - Added track type")

if __name__ == '__main__':
    input_file = '/home/ondarenc/CascadeProjects/garminport/20260524outdoor_run_class_0_garmin.gpx'
    output_file = '/home/ondarenc/CascadeProjects/garminport/20260524outdoor_run_class_0_garmin_enhanced.gpx'
    enhance_gpx_for_garmin(input_file, output_file)
