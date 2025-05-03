import streamlit as st
from streamlit.components.v1 import html
import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import Point
from folium import Circle, Marker, Icon

#!/usr/bin/env python
# coding: utf-8

# # Task 1: Static Maps by School Level - for all districts in the country

# In[1]:


import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# Load Peru districts shapefile
shapefile_path = r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\DISTRITOS\DISTRITOS_inei.shp"
peru_gdf = gpd.read_file(shapefile_path)

# Rename columns to ensure matching names
peru_gdf.rename(columns={'NOMBDEP': 'Departamento', 'NOMBDIST': 'Distrito'}, inplace=True)

# Load your school data
df = pd.read_excel(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\listado_iiee.xlsx")

# Filter data by school levels
levels = ['Inicial', 'Primaria', 'Secundaria']
dfs_level = {}
for level in levels:
    dfs_level[level] = df[df['Nivel / Modalidad'].str.contains(level, case=False, na=False)]

# Aggregate school counts by district
counts_level = {}
for level in levels:
    counts_level[level] = dfs_level[level].groupby('Distrito').size().reset_index(name='num_schools')

# Merge and plot static maps for each level
for level in levels:
    merged_gdf = peru_gdf.merge(counts_level[level], on='Distrito', how='left')
    merged_gdf['num_schools'] = merged_gdf['num_schools'].fillna(0)

    fig, ax = plt.subplots(figsize=(12, 12))
    merged_gdf.plot(column='num_schools', cmap='OrRd', linewidth=0.1, ax=ax,
                    edgecolor='black', legend=True,
                    legend_kwds={'label': f"Number of {level} Schools by District",
                                 'orientation': "horizontal"})

    ax.set_title(f'Distribution of {level} Schools in Peru', fontsize=16)
    ax.axis('off')
    st.pyplot(plt.gcf())


# In[3]:





# In[9]:


# Step 1: Load school data
df = pd.read_excel(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\listado_iiee.xlsx")

# Convert DataFrame to GeoDataFrame with points
gdf_schools = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitud, df.Latitud), crs="EPSG:4326")

# Step 2: Filter data by region and education level
regions = ['HUANCAVELICA', 'AYACUCHO']
gdf_filtered = gdf_schools[gdf_schools['Departamento'].str.upper().isin(regions)]

# Extract primary and secondary schools separately
gdf_primary = gdf_filtered[gdf_filtered['Nivel / Modalidad'].str.contains('Primaria', case=False)]
gdf_secondary = gdf_filtered[gdf_filtered['Nivel / Modalidad'].str.contains('Secundaria', case=False)]

# Step 3: Project to metric CRS (meters) for accurate distance calculations
gdf_primary_proj = gdf_primary.to_crs(epsg=32718)  # UTM zone suitable for Peru
gdf_secondary_proj = gdf_secondary.to_crs(epsg=32718)

# Step 4: Create 5km radius buffer around each primary school
gdf_primary_proj['buffer_5km'] = gdf_primary_proj.geometry.buffer(5000)

# Step 5: Count high schools within each primary school's buffer
def count_high_schools(row, secondary_schools):
    buffer_geom = row['buffer_5km']
    return secondary_schools.within(buffer_geom).sum()

gdf_primary_proj['num_highschools_nearby'] = gdf_primary_proj.apply(
    count_high_schools, axis=1, secondary_schools=gdf_secondary_proj)

# Step 6: Identify primary schools with min and max high schools nearby
school_min = gdf_primary_proj.loc[gdf_primary_proj['num_highschools_nearby'].idxmin()]
school_max = gdf_primary_proj.loc[gdf_primary_proj['num_highschools_nearby'].idxmax()]

# Helper function for plotting
def plot_proximity(school, secondary_schools, title):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Plot buffer
    buffer_gdf = gpd.GeoDataFrame(geometry=[school.buffer_5km], crs=gdf_primary_proj.crs)
    buffer_gdf.boundary.plot(ax=ax, color='blue', linestyle='--', linewidth=2, label='5 km radius')
    
    # Plot primary school centroid
    gpd.GeoSeries(school.geometry).plot(ax=ax, color='red', markersize=100, marker='*', label='Primary School')
    
    # Plot high schools within buffer
    secondary_in_buffer = secondary_schools[secondary_schools.within(school.buffer_5km)]
    secondary_in_buffer.plot(ax=ax, color='green', markersize=20, label='High Schools')
    
    ax.set_title(title, fontsize=15)
    ax.legend()
    ax.axis('off')
    st.pyplot(plt.gcf())

# Step 7: Plot results
plot_proximity(school_min, gdf_secondary_proj, 
               f"Primary School with FEWEST High Schools nearby ({school_min['num_highschools_nearby']})")

plot_proximity(school_max, gdf_secondary_proj, 
               f"Primary School with MOST High Schools nearby ({school_max['num_highschools_nearby']})")


# In[11]:


import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import matplotlib.pyplot as plt

# Step 1: Load school data
df = pd.read_excel(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\listado_iiee.xlsx")

# Convert DataFrame to GeoDataFrame
gdf_schools = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitud, df.Latitud), crs="EPSG:4326")

# Step 2: Define regions and filter data
regions = ['HUANCAVELICA', 'AYACUCHO']
gdf_filtered = gdf_schools[gdf_schools['Departamento'].str.upper().isin(regions)]

# Separate primary and secondary schools
gdf_primary = gdf_filtered[gdf_filtered['Nivel / Modalidad'].str.contains('Primaria', case=False)]
gdf_secondary = gdf_filtered[gdf_filtered['Nivel / Modalidad'].str.contains('Secundaria', case=False)]

# Step 3: Project data to UTM CRS for accurate distances
utm_crs = 'EPSG:32718'
gdf_primary_proj = gdf_primary.to_crs(utm_crs)
gdf_secondary_proj = gdf_secondary.to_crs(utm_crs)

# Create buffers of 5km radius around primary schools
gdf_primary_proj['buffer_5km'] = gdf_primary_proj.geometry.buffer(5000)

# Function to count high schools in buffers
def count_high_schools(buffer_geom, secondary_schools):
    return secondary_schools.within(buffer_geom).sum()

# Count high schools within 5km radius
gdf_primary_proj['num_highschools_nearby'] = gdf_primary_proj['buffer_5km'].apply(
    lambda x: count_high_schools(x, gdf_secondary_proj))

# Step 4: Analyze separately per region
for region in regions:
    primary_region = gdf_primary_proj[gdf_primary_proj['Departamento'].str.upper() == region]

    # Primary schools with minimum and maximum nearby high schools
    school_min = primary_region.loc[primary_region['num_highschools_nearby'].idxmin()]
    school_max = primary_region.loc[primary_region['num_highschools_nearby'].idxmax()]

    # Plotting function
    def plot_proximity(school, secondary_schools, region_name, proximity_type):
        fig, ax = plt.subplots(figsize=(10, 10))

        # Plot buffer
        buffer_gdf = gpd.GeoDataFrame(geometry=[school.buffer_5km], crs=utm_crs)
        buffer_gdf.boundary.plot(ax=ax, color='blue', linestyle='--', linewidth=2, label='5 km radius')

        # Plot primary school
        gpd.GeoSeries(school.geometry).plot(ax=ax, color='red', markersize=120, marker='*', label='Primary School')

        # High schools within buffer
        high_schools_within = secondary_schools[secondary_schools.within(school.buffer_5km)]
        high_schools_within.plot(ax=ax, color='green', markersize=20, label='High Schools')

        # Plot aesthetics
        ax.set_title(f"{region_name}: Primary School with {proximity_type} High Schools Nearby\n"
                     f"{school['Nombre de SS.EE.']} ({int(school['num_highschools_nearby'])} high schools)",
                     fontsize=14, fontweight='bold')
        ax.legend()
        ax.axis('off')
        st.pyplot(plt.gcf())

    # Plot schools for current region
    plot_proximity(school_min, gdf_secondary_proj, region, "FEWEST")
    plot_proximity(school_max, gdf_secondary_proj, region, "MOST")


# In[17]:


import pandas as pd
import geopandas as gpd
import folium
from folium import Choropleth, LayerControl

# Load Excel school data
df = pd.read_excel(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\listado_iiee.xlsx")

# Standardize column names
df['Distrito'] = df['Distrito'].str.upper()
df['Nivel / Modalidad'] = df['Nivel / Modalidad'].str.upper()

# Load district shapefile
gdf_districts = gpd.read_file(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\DISTRITOS\DISTRITOS_inei.shp")

# Rename for consistency
gdf_districts.rename(columns={'NOMBDEP': 'Departamento', 'NOMBDIST': 'Distrito'}, inplace=True)
gdf_districts['Distrito'] = gdf_districts['Distrito'].str.upper()

# Prepare level filters and colors
levels = {
    'INICIAL': 'Reds',
    'PRIMARIA': 'Blues',
    'SECUNDARIA': 'Greens'
}

# Create base folium map (centered on Peru)
m = folium.Map(location=[-9.19, -75.02], zoom_start=5, tiles='CartoDB positron')

# Count schools per district for each level
for level, color in levels.items():
    df_level = df[df['Nivel / Modalidad'].str.contains(level, na=False)]
    school_counts = df_level.groupby('Distrito').size().reset_index(name='num_schools')
    
    # Merge with shapefile
    merged = gdf_districts.merge(school_counts, on='Distrito', how='left').fillna(0)

    # Convert GeoDataFrame to GeoJSON for Folium
    geojson = merged.to_json()

    # Add layer to map
    choropleth = Choropleth(
        geo_data=geojson,
        name=level.title(),
        data=merged,
        columns=['Distrito', 'num_schools'],
        key_on='feature.properties.Distrito',
        fill_color=color,
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=f'{level.title()} Schools per District',
        nan_fill_color='white'
    ).add_to(m)

# Add layer control
LayerControl().add_to(m)

# Save map to HTML
m_html = m._repr_html_()
html(m_html, height=600)
# m.save(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\folium_school_choropleth.html")


# In[19]:


import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import Point
from folium import Circle, Marker, Map, FeatureGroup, LayerControl, Icon

# Load and prepare school data
df = pd.read_excel(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\listado_iiee.xlsx")
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitud, df.Latitud), crs='EPSG:4326')

# Filter to only Ayacucho and Huancavelica
regions = ['AYACUCHO', 'HUANCAVELICA']
gdf = gdf[gdf['Departamento'].str.upper().isin(regions)]

# Separate primary and secondary schools
gdf_primary = gdf[gdf['Nivel / Modalidad'].str.contains('Primaria', case=False, na=False)]
gdf_secondary = gdf[gdf['Nivel / Modalidad'].str.contains('Secundaria', case=False, na=False)]

# Project to UTM zone 18S (for accurate meters-based distance)
gdf_primary_utm = gdf_primary.to_crs('EPSG:32718')
gdf_secondary_utm = gdf_secondary.to_crs('EPSG:32718')

# Create 5 km buffer around each primary school
gdf_primary_utm['buffer_5km'] = gdf_primary_utm.geometry.buffer(5000)

# Count nearby high schools
def count_high_schools(buffer, secondary_schools):
    return secondary_schools.within(buffer).sum()

gdf_primary_utm['highschool_count'] = gdf_primary_utm['buffer_5km'].apply(
    lambda buf: count_high_schools(buf, gdf_secondary_utm))

# Reproject back to WGS84 for Folium visualization
gdf_primary_wgs = gdf_primary_utm.to_crs('EPSG:4326')
gdf_secondary_wgs = gdf_secondary_utm.to_crs('EPSG:4326')

# Function to create Folium map for a given school
def create_folium_map(school_row, secondary_schools, region, proximity_type):
    # Extract location
    lat = school_row.geometry.y
    lon = school_row.geometry.x

    # Create map centered on primary school
    fmap = Map(location=[lat, lon], zoom_start=12, tiles='OpenStreetMap')

    # Add buffer circle (approximate radius in meters)
    Circle(
        location=(lat, lon),
        radius=5000,
        color='blue',
        fill=True,
        fill_opacity=0.1,
        tooltip='5 km radius'
    ).add_to(fmap)

    # Add primary school marker
    Marker(
        location=[lat, lon],
        popup=f"Primary School: {school_row['Nombre de SS.EE.']}",
        icon=Icon(color='red', icon='star', prefix='fa')
    ).add_to(fmap)

    # Plot nearby high schools
    buffer_geom = school_row.buffer_5km
    buffer_geom_wgs = gpd.GeoSeries([buffer_geom], crs='EPSG:32718').to_crs('EPSG:4326')[0]
    secondary_nearby = secondary_schools[secondary_schools.within(buffer_geom_wgs)]

    for _, hs in secondary_nearby.iterrows():
        Marker(
            location=[hs.geometry.y, hs.geometry.x],
            popup=hs['Nombre de SS.EE.'],
            icon=Icon(color='green', icon='graduation-cap', prefix='fa')
        ).add_to(fmap)

    # Add title-like comment in map
    fmap.get_root().html.add_child(folium.Element(f"""
        <h4 style='position: fixed; 
                   top: 10px; left: 50px; width: 90%;
                   z-index: 9999;
                   font-size: 16px;
                   background-color: white;
                   padding: 10px;
                   border: 1px solid grey;'>
        {region.title()} - Primary School with {proximity_type} Nearby High Schools:<br>
        <b>{school_row['Nombre de SS.EE.']}</b> ({int(school_row['highschool_count'])} high schools)
        </h4>
    """))

    return fmap

# Generate and save maps for each region's min/max primary school
for region in regions:
    subset = gdf_primary_wgs[gdf_primary_wgs['Departamento'].str.upper() == region]

    min_school = subset.loc[subset['highschool_count'].idxmin()]
    max_school = subset.loc[subset['highschool_count'].idxmax()]

    # Create Folium maps
    map_min = create_folium_map(min_school, gdf_secondary_wgs, region, "FEWEST")
    map_max = create_folium_map(max_school, gdf_secondary_wgs, region, "MOST")

    # Save as HTML files
    map_min.save(fr"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\proximity_{region.lower()}_min.html")
    map_max.save(fr"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\proximity_{region.lower()}_max.html")


# In[23]:


import pandas as pd
import geopandas as gpd
import folium
from shapely.geometry import Point
from folium import Circle, Marker, Map, Icon

# Load and prepare school data
df = pd.read_excel(r"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\listado_iiee.xlsx")
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitud, df.Latitud), crs='EPSG:4326')

# Filter to only Ayacucho and Huancavelica
regions = ['AYACUCHO', 'HUANCAVELICA']
gdf = gdf[gdf['Departamento'].str.upper().isin(regions)]

# Separate primary and secondary schools
gdf_primary = gdf[gdf['Nivel / Modalidad'].str.contains('Primaria', case=False, na=False)]
gdf_secondary = gdf[gdf['Nivel / Modalidad'].str.contains('Secundaria', case=False, na=False)]

# Project to UTM for accurate distance calculations
gdf_primary_utm = gdf_primary.to_crs('EPSG:32718')
gdf_secondary_utm = gdf_secondary.to_crs('EPSG:32718')

# Compute 5km buffers and count nearby high schools
gdf_primary_utm['buffer_5km'] = gdf_primary_utm.geometry.buffer(5000)
gdf_primary_utm['highschool_count'] = gdf_primary_utm['buffer_5km'].apply(
    lambda buf: gdf_secondary_utm.within(buf).sum()
)

# Reproject back to EPSG:4326 for Folium
gdf_primary_wgs = gdf_primary_utm.to_crs('EPSG:4326')
gdf_secondary_wgs = gdf_secondary_utm.to_crs('EPSG:4326')

# Function to create a single regional map
def create_region_map(region_name, primary_schools, secondary_schools):
    region_df = primary_schools[primary_schools['Departamento'].str.upper() == region_name]

    # Identify:
    min_schools = region_df[region_df['highschool_count'] == 0]
    max_school = region_df.loc[region_df['highschool_count'].idxmax()]

    # Center map on average location
    avg_lat = region_df.geometry.y.mean()
    avg_lon = region_df.geometry.x.mean()
    fmap = Map(location=[avg_lat, avg_lon], zoom_start=8, tiles='OpenStreetMap')

    # Plot primary schools with 0 high schools nearby
    for _, row in min_schools.iterrows():
        Circle(
            location=(row.geometry.y, row.geometry.x),
            radius=5000,
            color='red',
            fill=True,
            fill_opacity=0.2,
            tooltip=f"0 high schools\n{row['Nombre de SS.EE.']}"
        ).add_to(fmap)

        Marker(
            location=(row.geometry.y, row.geometry.x),
            icon=Icon(color='red', icon='times', prefix='fa'),
            popup=f"{row['Nombre de SS.EE.']}\n(0 high schools)"
        ).add_to(fmap)

    # Plot the primary school with most high schools nearby
    Circle(
        location=(max_school.geometry.y, max_school.geometry.x),
        radius=5000,
        color='green',
        fill=True,
        fill_opacity=0.2,
        tooltip=f"{int(max_school['highschool_count'])} high schools\n{max_school['Nombre de SS.EE.']}"
    ).add_to(fmap)

    Marker(
        location=(max_school.geometry.y, max_school.geometry.x),
        icon=Icon(color='green', icon='star', prefix='fa'),
        popup=f"{max_school['Nombre de SS.EE.']}\n({int(max_school['highschool_count'])} high schools)"
    ).add_to(fmap)

    # Plot the nearby secondary schools around max school
    max_buffer = max_school['buffer_5km']
    max_buffer_wgs = gpd.GeoSeries([max_buffer], crs='EPSG:32718').to_crs('EPSG:4326')[0]
    nearby_highschools = secondary_schools[secondary_schools.within(max_buffer_wgs)]

    for _, hs in nearby_highschools.iterrows():
        Marker(
            location=(hs.geometry.y, hs.geometry.x),
            icon=Icon(color='blue', icon='graduation-cap', prefix='fa'),
            popup=f"High School: {hs['Nombre de SS.EE.']}"
        ).add_to(fmap)

    # Title bar
    fmap.get_root().html.add_child(folium.Element(f"""
        <h4 style='position: fixed; 
                   top: 10px; left: 50px; width: 90%;
                   z-index: 9999;
                   font-size: 16px;
                   background-color: white;
                   padding: 10px;
                   border: 1px solid grey;'>
        {region_name.title()} — Proximity Analysis of Primary Schools
        <br><span style='color:red;'>Red</span>: Primary schools with 0 nearby high schools
        <br><span style='color:green;'>Green</span>: Primary school with most nearby high schools
        <br><span style='color:blue;'>Blue</span>: Nearby secondary schools
        </h4>
    """))
    
    return fmap

# Create and save maps
for region in regions:
    fmap = create_region_map(region, gdf_primary_wgs, gdf_secondary_wgs)
    fmap.save(fr"C:\Users\brfm1\OneDrive\Documentos\Geospatial Analysis of Schools in Peru\proximity_{region.lower()}_map.html")


# In[ ]:




