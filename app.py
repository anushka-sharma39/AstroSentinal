import math
from flask import Flask, render_template, request
from skyfield.api import load
from datetime import datetime

app = Flask(__name__)

# This function pulls real data from Celestrak (NASA/NORAD Source)
def get_live_data():
    stations_url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=tle'
    satellites = load.tle_file(stations_url)
    ts = load.timescale()
    t = ts.now()
    
    current_positions = []
    # We check the 30 brightest objects in space right now
    for sat in satellites[:30]:
        try:
            geocentric = sat.at(t)
            pos = geocentric.position.km
            current_positions.append({
                'id': sat.name,
                'x': pos[0],
                'y': pos[1],
                'z': pos[2]
            })
        except:
            continue
    return current_positions

# 3D Distance Formula: d = sqrt((x2-x1)^2 + (y2-y1)^2 + (z2-z1)^2)
def calculate_3d_dist(p1, p2):
    return math.sqrt((p2['x']-p1['x'])**2 + (p2['y']-p1['y'])**2 + (p2['z']-p1['z'])**2)

@app.route('/')
def index():
    # This is the default view with just live satellite data
    sats = get_live_data()
    results = []
    for i in range(len(sats)):
        obj = sats[i]
        min_dist = 999999
        for j in range(len(sats)):
            if i != j:
                dist = calculate_3d_dist(obj, sats[j])
                if dist < min_dist: min_dist = dist
        
        risk = "HIGH" if min_dist < 500 else "MEDIUM" if min_dist < 2000 else "LOW"
        results.append({'data': obj, 'dist': round(min_dist, 2), 'risk': risk})
    return render_template('index.html', results=results)

@app.route('/check', methods=['POST'])
def check_safety():
    # This is where the User Input (the startup data) is processed!
    user_sat = {
        'id': f"USER: {request.form.get('name')}",
        'x': float(request.form.get('x')),
        'y': float(request.form.get('y')),
        'z': float(request.form.get('z'))
    }
    
    sats = get_live_data()
    results = []
    
    # Check the user's satellite against every live satellite from NASA
    for sat in sats:
        dist = calculate_3d_dist(user_sat, sat)
        risk = "HIGH" if dist < 500 else "MEDIUM" if dist < 2000 else "LOW"
        results.append({'data': sat, 'dist': round(dist, 2), 'risk': risk})
    
    # Sort results to show the closest (most dangerous) objects first
    results = sorted(results, key=lambda x: x['dist'])
    
    return render_template('index.html', results=results, user_mission=user_sat)

if __name__ == '__main__':
    app.run(debug=True)
