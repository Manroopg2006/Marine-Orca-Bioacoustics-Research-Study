import pandas as pd
import folium
from folium.plugins import HeatMap
import os

df = pd.read_csv("data/processed/detections.csv")
print(f"Loaded {len(df)} detections")

# Center map between both locations
m = folium.Map(location=[48.0, -122.9], zoom_start=9)

# Color by location
coords = {
    'Dyes Inlet South': (47.6181, -122.6865),
    'Dyes Inlet North': (47.6181, -122.6865),
    'Orcasound Lab - San Juan Island': (48.5503, -123.1700)
}

colors = {
    'Dyes Inlet South': 'red',
    'Dyes Inlet North': 'red',
    'Orcasound Lab - San Juan Island': 'blue'
}

for location, group in df.groupby('location'):
    color = colors[location]
    for _, row in group.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=4,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=row['confidence'],
            popup=f"{location}<br>Time: {row['start_sec']:.1f}s<br>Confidence: {row['confidence']}"
        ).add_to(m)

    # Summary marker per location
    folium.Marker(
        location=[group.iloc[0]['lat'], group.iloc[0]['lon']],
        popup=f"{location}<br>{len(group)} detections<br>Avg confidence: {group['confidence'].mean():.2f}",
        icon=folium.Icon(color='blue' if color == 'blue' else 'red', icon='info-sign')
    ).add_to(m)

# Add heatmap layer
heat_data = [[row['lat'], row['lon'], row['confidence']] for _, row in df.iterrows()]
HeatMap(heat_data, radius=30).add_to(m)

m.save("data/processed/orca_map.html")
print("Map saved")