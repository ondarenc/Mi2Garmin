#!/usr/bin/env python3
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import copy

def fix_gpx_timestamps(input_file, output_file):
    """Fix GPX file by filling timestamp gaps to create continuous time-series data"""
    
    # Parse the GPX file
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Handle namespace
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    # Find all track points
    trkpts = root.findall('.//gpx:trkpt', ns)
    if not trkpts:
        # Try without namespace
        trkpts = root.findall('.//trkpt')
        ns = None
    
    print(f"Processing {len(trkpts)} track points...")
    
    fixed_trkpts = []
    prev_time = None
    prev_pt = None
    
    for i, pt in enumerate(trkpts):
        # Get timestamp
        if ns:
            time_elem = pt.find('gpx:time', ns)
        else:
            time_elem = pt.find('time')
        
        curr_time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
        
        if prev_time:
            # Calculate time difference
            diff = (curr_time - prev_time).total_seconds()
            
            if diff > 1:
                # Fill gap with interpolated points
                num_interpolated = int(diff) - 1
                print(f"Gap of {diff}s at point {i}, filling with {num_interpolated} interpolated points")
                
                lat_step = (float(pt.attrib['lat']) - float(prev_pt.attrib['lat'])) / (num_interpolated + 1)
                lon_step = (float(pt.attrib['lon']) - float(prev_pt.attrib['lon'])) / (num_interpolated + 1)
                
                for j in range(num_interpolated):
                    # Create interpolated point
                    new_pt = copy.deepcopy(prev_pt)
                    new_pt.attrib['lat'] = str(float(prev_pt.attrib['lat']) + lat_step * (j + 1))
                    new_pt.attrib['lon'] = str(float(prev_pt.attrib['lon']) + lon_step * (j + 1))
                    
                    # Set interpolated timestamp
                    interp_time = prev_time + timedelta(seconds=j+1)
                    if ns:
                        new_pt.find('gpx:time', ns).text = interp_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    else:
                        new_pt.find('time').text = interp_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                    
                    fixed_trkpts.append(new_pt)
        
        fixed_trkpts.append(pt)
        prev_time = curr_time
        prev_pt = pt
    
    # Replace track segment with fixed points
    if ns:
        trkseg = root.find('.//gpx:trkseg', ns)
    else:
        trkseg = root.find('.//trkseg')
    
    # Clear existing points
    for pt in trkseg.findall('.//gpx:trkpt', ns) if ns else trkseg.findall('.//trkpt'):
        trkseg.remove(pt)
    
    # Add fixed points
    for pt in fixed_trkpts:
        trkseg.append(pt)
    
    # Write output file
    tree.write(output_file, encoding='UTF-8', xml_declaration=True)
    print(f"\nOriginal points: {len(trkpts)}")
    print(f"Fixed points: {len(fixed_trkpts)}")
    print(f"Output written to: {output_file}")

if __name__ == '__main__':
    input_file = '/home/ondarenc/CascadeProjects/garminport/20260524outdoor_run_class_0.gpx'
    output_file = '/home/ondarenc/CascadeProjects/garminport/20260524outdoor_run_class_0_garmin.gpx'
    fix_gpx_timestamps(input_file, output_file)
