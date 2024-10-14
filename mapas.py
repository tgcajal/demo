"""Mapas"""

import numpy as np
import pandas as pd 
import geopandas as gpd
import transform as transform
import folium
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

import streamlit as st

#-------------CARGAR DATOS------------------
hn_dep = gpd.read_file('honduras_departamentos.geojson')
hn_mun = gpd.read_file('honduras_municipios.geojson')


sv_dep = gpd.read_file('el_salvador_departamentos.geojson')
sv_mun = gpd.read_file('el_salvador_municipios.geojson')

df = transform.transform('mora.csv','cashflow.csv')
sucursal = pd.read_csv('sucursal.csv')

#--------------FUNCIONES--------------------

# Preprocesamiento
def get_map_data(df, sucursal):

    # Mantener registros históricos
    map_data = df[~df['estado'].isin(['Exigible','Fijo'])] # Eliminar registros esperados

    # Mantener registros más actuales
    map_data.sort_values(by='fecha_cuota',ascending=False).drop_duplicates(subset=['id_credito'], keep='first', inplace=True)

    # Agrupar por sucursal
    map_data = map_data.groupby('nombre_sucursal')[['pago','id_credito']].agg({'id_credito':'count',
                                                                                              'pago':'sum',
                                                                                              #'saldo_esperado':'sum',
                                                                                              #'saldo_real':'sum'
                                                                                              }).reset_index()
    
    # Agregar datos de catálogo de sucursal
    map_data_ = map_data.merge(sucursal, how='left', on='nombre_sucursal')

    # Llenar campos vacíos con 0
    map_data_.fillna(0, inplace=True)

    # Estandarizar departamento y municipio
    map_data_['departamento'] = map_data_['departamento'].astype(str).apply(str.upper)
    map_data_['municipio'] = map_data_['municipio'].astype(str).apply(str.upper)

    # Agrupar por país, departamento y municipio
    map_data_ = map_data_.groupby(['pais_empresa','departamento','municipio'])[['id_credito','pago']].agg({'id_credito':'sum','pago':'sum'}).reset_index()

    # Limpieza según errores encontrados hasta la fecha
    map_data_.at[1,'departamento'] = 'SONSONATE'

    map_data_.at[26, 'municipio'] = 'SIGUATEPEQUE'
    map_data_.at[27, 'municipio'] = 'TEGUCIGALPA'

    map_data_['departamento'].replace({'SIGUATEPEQUE':'COMAYAGUA', 'TEGUCIGALPA':'FRANCISCO MORAZÁN'}, inplace=True)

    # Crear municipio y departamento
    map_data_municipio = map_data_.groupby(['pais_empresa','municipio'])[['id_credito','pago']].sum()
    map_data_departamento = map_data_.groupby(['pais_empresa','departamento'])[['id_credito','pago']].sum()

    # Agregar tasa impago 
    map_data_municipio['tasa_impago'] = round(1 - map_data_municipio['pago']/map_data_municipio['id_credito'],2)
    map_data_departamento['tasa_impago'] = round(1 - map_data_departamento['pago']/map_data_departamento['id_credito'],2)

    # Crear subdivisiones por país
    hn_dep_data = map_data_departamento.loc['Honduras'].reset_index()
    hn_mun_data = map_data_municipio.loc['Honduras'].reset_index()

    sv_mun_data = map_data_municipio.loc['El Salvador'].reset_index()
    sv_dep_data = map_data_departamento.loc['El Salvador'].reset_index()

    # Limpieza detectada hasta ahora
    hn_mun_data.replace({'DANLI':'DANLÍ', 'ROATAN':'ROATÁN', 'SAN MARCOS DE COLON':'SAN MARCOS DE COLÓN', 'TEGUCIGALPA':'DISTRITO CENTRAL'}, inplace=True)

    return hn_dep_data, hn_mun_data, sv_dep_data, sv_mun_data

# Agregar features a geojson
def add_features(admin_data, gdf):

    if 'departamento' in admin_data.columns: admin_col, nombre = 'departamento','Departamento'
    else: admin_col, nombre = 'municipio', 'Municipio'

    area_gdf = admin_data.merge(gdf, how='left',left_on=admin_col, right_on='name')

    tabla = area_gdf.sort_values(by='tasa_impago', ascending=False)
    tabla[admin_col].replace({0:'Desconocido'})
    tabla.rename(columns={admin_col:nombre, 'id_credito':'Clientes', 'pago':'Clientes sin mora','tasa_impago':'Tasa Impago'}, inplace=True)

    otros = gpd.GeoDataFrame(area_gdf[area_gdf[admin_col]=='0']).reset_index()
    gdf = gpd.GeoDataFrame(data=area_gdf.dropna(), geometry='geometry')

    if len(otros)>0:
        otros_caption = f'Sin {admin_col}: {otros.at[0, "tasa_impago"]} tasa impago ({otros.at[0,"id_credito"]} clientes)'
    else:
        otros_caption = f'Total'

    return gdf, tabla, otros_caption



# PLOT
def plot_map(gdf, value_column, zoom_start=12):
    """
    Plots a GeoDataFrame with polygon geometries on a Folium map, using a red color scale
    based on the values in the specified column.
    """
    print(len(gdf))

    map_center = [gdf.geometry.unary_union.centroid.y, gdf.geometry.unary_union.centroid.x]
    # Create a Folium map centered at map_center
    m = folium.Map(location=map_center, zoom_start=zoom_start)

    # Normalize the values in the specified column
    values = gdf[value_column]
    norm = Normalize(vmin=values.min(), vmax=values.max())  # Normalize values for color scaling
    cmap = plt.cm.Reds  # Use Reds colormap from matplotlib

    # Function to map values to colors
    def get_color(value):
        rgba_color = cmap(norm(value))  # Map normalized value to a color
        hex_color = f'#{int(rgba_color[0]*255):02x}{int(rgba_color[1]*255):02x}{int(rgba_color[2]*255):02x}'
        return hex_color

    # Define style function for polygons
    def style_function(feature):
        value = feature['properties'][value_column]  # Get value from the column
        return {
            'fillColor': get_color(value),  # Set polygon color based on value
            'color': 'black',               # Polygon border color
            'weight': 1,                    # Border thickness
            'fillOpacity': 0.7              # Polygon fill transparency
        }

    # Add GeoDataFrame to the map as GeoJson
    folium.GeoJson(
        gdf,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=['name', value_column])  # Show column value on hover
    ).add_to(m)

    # Function to add a color scale legend
    def add_legend(map_object, title, cmap, vmin, vmax):
        import branca.colormap as cm
        colormap = cm.LinearColormap([cmap(0), cmap(1), cmap(0.5)], vmin=vmin, vmax=vmax)
        colormap.caption = title  # Title of the color scale
        colormap.add_to(map_object)  # Add the color scale to the map

    # Add the color legend for the map
    add_legend(m, 'Tasa Impago', cmap, values.min(), values.max())  # NEW

    return m

#----------------PIPELINE------------------

# Cargar data actual
hn_dep_data, hn_mun_data, sv_dep_data, sv_mun_data = get_map_data(df, sucursal)

# Añadir dimensión geográfica por caso

# Honduras por departamento
hn_dep_gdf, hn_dep_tabla, hn_dep_caption = add_features(hn_dep_data, hn_dep)
hn_dep_map = plot_map(hn_dep_gdf,'tasa_impago')

# Honduras por municipio
hn_mun_gdf, hn_mun_tabla, hn_mun_caption = add_features(hn_mun_data, hn_mun)
hn_mun_map = plot_map(hn_mun_gdf,'tasa_impago')


# El Salvador por departamento
sv_dep_gdf, sv_dep_tabla, sv_dep_caption = add_features(sv_dep_data, sv_dep)
sv_dep_map = plot_map(sv_dep_gdf,'tasa_impago')

# El Salvador por municipio
sv_mun_gdf, sv_mun_tabla, sv_mun_caption = add_features(sv_mun_data, sv_mun)
sv_mun_map = plot_map(sv_mun_gdf,'tasa_impago')

#-----------------ARMAR OBJETO---------------------
# Asumiendo que estará en un container
tab1, tab2 = st.tabs(['El Salvador','Honduras'])

with tab1:
    st.header("Impago El Salvador")
    st.write("Tasa de impago acumulada hasta la fecha.")


    st.button(label='', type="primary", icon=":material/arrow_upward:")
    if st.button(label='', icon=":material/arrow_downward:"):
        caption = sv_mun_caption
        map = sv_mun_map
        table = sv_mun_tabla
    
    else:
        caption = sv_dep_caption
        map = sv_dep_map 
        table = sv_dep_tabla
    
    col1, col2 = st.columns(2)

    with col1:
        st.write(caption)
        st.folium(map)
    
    with col2:
        st.dataframe(table)

with tab2:
    st.header("Impago Honduras")
    st.write("Tasa de impago acumulada hasta la fecha.")


    st.button(label='', type="primary", icon=":material/arrow_upward:")
    if st.button(label='', icon=":material/arrow_downward:"):
        caption = hn_mun_caption
        map = hn_mun_map
        table = hn_mun_tabla
    
    else:
        caption = hn_dep_caption
        map = hn_dep_map 
        table = hn_dep_tabla
    
    col1, col2 = st.columns(2)

    with col1:
        st.write(caption)
        st.folium(map)
    
    with col2:
        st.dataframe(table)
#st.button("Reset", type="primary")
#if st.button("Say hello"):
#    st.write("Why hello there")
#else:
#    st.write("Goodbye")

