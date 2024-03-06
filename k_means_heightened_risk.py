import folium
import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
import json
from shapely.geometry import MultiPoint, Point

# Load the CSV data into a DataFrame
data = pd.read_csv('Piracy Data/pirate_attacks.csv')

# Convert latitude and longitude to radians for clustering
data['lat_rad'] = data['latitude'] * (3.141592653589793 / 180)
data['lon_rad'] = data['longitude'] * (3.141592653589793 / 180)

# Define the threshold distance (in degrees) for including points in the cluster footprint
threshold_distance = 5  # Adjust value down to make smaller footprint, larger for larger footprint
number_of_clusters = 12 # Adjust number of cliust

# Perform K-Means clustering to create [x] clusters based on coordinates
kmeans = KMeans(n_clusters=number_of_clusters, random_state=0).fit(data[['lat_rad', 'lon_rad']])
data['cluster'] = kmeans.labels_

# Create a GeoDataFrame from the original DataFrame
gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data['longitude'], data['latitude']))

# Create a map centered around the coordinates of your data
m = folium.Map(location=[22.746643521000067, 115.82595611500005], zoom_start=5)

# Iterate through the clusters and create GeoJSON polygons for each cluster
for cluster_id in range(number_of_clusters):
    cluster_data = gdf[gdf['cluster'] == cluster_id]

    # Extract the coordinates of the cluster points as Shapely Point objects
    cluster_coordinates = [Point(point) for point in cluster_data.geometry]

    # Create a MultiPoint object
    multipoint = MultiPoint(cluster_coordinates)

    # Create a convex hull polygon from the MultiPoint
    convex_hull = multipoint.convex_hull

    # Filter out outliers based on distance from cluster center
    cluster_center = multipoint.centroid
    filtered_coordinates = [point for point in cluster_coordinates if point.distance(cluster_center) <= threshold_distance]

    # Create a MultiPoint object from filtered coordinates
    filtered_multipoint = MultiPoint(filtered_coordinates)

    # Create an adjusted footprint using the filtered MultiPoint
    adjusted_footprint = filtered_multipoint.convex_hull

    # Convert the adjusted footprint to GeoJSON
    adjusted_footprint_geojson = adjusted_footprint.__geo_interface__

    print(adjusted_footprint_geojson)


    # Specify the file path where you want to save the GeoJSON file
    file_path = "imminent.geojson"

    # Open the file in write mode
    with open(file_path, 'w') as file:
        # Write the GeoJSON data to the file
        json.dump(adjusted_footprint_geojson, file)

    # Create a GeoJson layer for the adjusted footprint and add it to the map
    folium.GeoJson(
        adjusted_footprint_geojson,
        name=f'Cluster {cluster_id} Adjusted Footprint',
        style_function=lambda feature: {
            'color': 'red',  # Change the color as needed
            'fillColor': 'red',
            'fillOpacity': 0.2,
            'weight': 2,
        }
    ).add_to(m)

    # Iterate through the piracy attacks and add black circle markers for each one
    for index, row in data.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=1,  # Radius 1 as per your request
            color='black',  # Black color
            fill=True,
            fill_color='black',
            fill_opacity=1,
        ).add_to(m)

# Save the map to an HTML file or display it
m.save(f'Cluster {threshold_distance,number_of_clusters} Adjusted Footprint.html')
