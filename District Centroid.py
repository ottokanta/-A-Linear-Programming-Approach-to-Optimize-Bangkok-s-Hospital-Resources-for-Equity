import geopandas as gpd

gdf = gpd.read_file("district.shp") 

print(gdf.columns)
print(gdf.head())

gdf = gdf.to_crs(epsg=4326)
gdf['centroid'] = gdf.geometry.centroid
gdf['Latitude'] = gdf.centroid.y
gdf['Longitude'] = gdf.centroid.x

district_centroids = gdf[['dcode', 'dname_e', 'Latitude', 'Longitude']]

district_centroids.to_csv('bangkok_district_centroids.csv', index=False)

print("District centroids saved to bangkok_district_centroids.csv")