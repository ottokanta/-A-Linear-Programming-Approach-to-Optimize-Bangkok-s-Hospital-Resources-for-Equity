import pandas as pd
from geopy.distance import geodesic

# Load data
hospitals = pd.read_csv("Research Dataset - Hospitals.csv")
districts = pd.read_csv("Research Dataset - Districts.csv") 

hospitals.columns = hospitals.columns.str.strip()
districts.columns = districts.columns.str.strip()

results = []

for _, d_row in districts.iterrows():
    d_id = d_row['District ID']
    d_name = d_row['District']
    d_lat = d_row['Latitude']
    d_lon = d_row['Longitude']

    for _, h_row in hospitals.iterrows():
        h_id = h_row['Hospital Name']
        h_lat = h_row['Latitude']
        h_lon = h_row['Longitude']

        # Check for missing (NaN) coordinates
        if pd.notna(d_lat) and pd.notna(d_lon) and pd.notna(h_lat) and pd.notna(h_lon):
            try:
                dist_km = geodesic((float(d_lat), float(d_lon)), (float(h_lat), float(h_lon))).km
                results.append({
                    'District ID': d_id,
                    'District': d_name,
                    'Hospital Name': h_id,
                    'Distance_km': dist_km
                })
            except ValueError as e:
                print(f"Skipping invalid coordinates due to ValueError: {e}")
        else:
            print(f"Skipping due to missing coordinates: {d_lat}, {d_lon}, {h_lat}, {h_lon}")

distance_df = pd.DataFrame(results)

distance_df.to_csv("district_hospital_distances.csv", index=False)
print("Distance matrix saved to district_hospital_distances.csv")