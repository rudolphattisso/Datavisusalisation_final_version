import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap, HeatMapWithTime
import plotly.express as px

# Script de visualisation des données TBM Bordeaux.
# Ce script produit des cartes interactives (Folium/Plotly), des heatmaps
# et plusieurs graphiques PNG destinés au rapport final.

BASE   = r'c:\Users\attis\Documents\002_EPSI\00_Cours\visualisation de données\dataviz_Final'
PROC   = os.path.join(BASE, 'data', 'processed')
OUTPUT = os.path.join(BASE, 'data', 'output')
os.makedirs(OUTPUT, exist_ok=True)

BORDEAUX_LAT = 44.8378
BORDEAUX_LON = -0.5792

print('=== SCRIPT VISUALISATION — CHARGEMENT ===')
df      = pd.read_csv(os.path.join(PROC, 'bordeaux_tbm_merged.csv'), low_memory=False)
df_stops = pd.read_csv(os.path.join(PROC, 'bordeaux_stops.csv'), low_memory=False)
print(f'  Dataset charge : {len(df):,} lignes')
print(f'  Stops charge   : {len(df_stops):,} arrets')

# ─── Tâche 1 : Carte des arrêts Folium ────────────────────────────────────────
print()
print('=== TACHE 1 : carte_arrets_bordeaux.html ===')
m1 = folium.Map(location=[BORDEAUX_LAT, BORDEAUX_LON], zoom_start=13, tiles='CartoDB positron')

# Couleurs par type
color_map = {'Tramway': 'red', 'Bus': 'blue', 'Ferry': 'green'}

for _, row in df_stops.iterrows():
    if pd.isna(row['stop_lat']) or pd.isna(row['stop_lon']):
        continue
    color = color_map.get(row.get('transport_type', 'Bus'), 'gray')
    radius = 5 if color == 'red' else 3
    folium.CircleMarker(
        location=[row['stop_lat'], row['stop_lon']],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        popup=folium.Popup(f"{row['stop_name']} - {row.get('transport_type','?')}", max_width=200)
    ).add_to(m1)

# Légende
legend_html = '''
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:white;
     padding:10px;border-radius:8px;border:2px solid grey;font-size:13px;">
  <b>TBM Bordeaux</b><br>
  <span style="color:red;">&#9679;</span> Tramway<br>
  <span style="color:blue;">&#9679;</span> Bus
</div>
'''
m1.get_root().html.add_child(folium.Element(legend_html))
m1.save(os.path.join(OUTPUT, 'carte_arrets_bordeaux.html'))
print('  carte_arrets_bordeaux.html OK')

# ─── Tâche 2 : Heatmap densité ────────────────────────────────────────────────
print()
print('=== TACHE 2 : heatmap_densite_bordeaux.html ===')
stop_passages = df.groupby('stop_name').size().reset_index(name='nb_passages')
# df_stops peut contenir plusieurs lignes par arrêt (une par type de transport).
# On déduplique par nom d'arrêt en conservant la première latitude/longitude.
stops_dedup = df_stops.drop_duplicates(subset='stop_name')[['stop_name','stop_lat','stop_lon']].dropna()
stop_heat = stops_dedup.merge(stop_passages, on='stop_name', how='left').dropna(subset=['stop_lat','stop_lon','nb_passages'])

m2 = folium.Map(location=[BORDEAUX_LAT, BORDEAUX_LON], zoom_start=12, tiles='CartoDB dark_matter')
heat_data = [[row['stop_lat'], row['stop_lon'], row['nb_passages']] for _, row in stop_heat.iterrows()]
HeatMap(heat_data, radius=15, blur=10, min_opacity=0.3).add_to(m2)
m2.save(os.path.join(OUTPUT, 'heatmap_densite_bordeaux.html'))
print('  heatmap_densite_bordeaux.html OK')

# ─── Tâche 3 : Heatmap temporelle animée ──────────────────────────────────────
print()
print('=== TACHE 3 : heatmap_temporelle_bordeaux.html ===')
m3 = folium.Map(location=[BORDEAUX_LAT, BORDEAUX_LON], zoom_start=12, tiles='CartoDB dark_matter')
hours = list(range(5, 24))
heat_time_data = []
index_labels   = []
for h in hours:
    df_h = df[df['hour'] == h].groupby(['stop_lat', 'stop_lon']).size().reset_index(name='cnt')
    df_h = df_h.dropna(subset=['stop_lat', 'stop_lon'])
    heat_time_data.append([[r['stop_lat'], r['stop_lon'], r['cnt']] for _, r in df_h.iterrows()])
    index_labels.append(f'{h:02d}:00')

HeatMapWithTime(
    heat_time_data,
    index=index_labels,
    auto_play=True,
    speed_step=1,
    radius=15
).add_to(m3)
m3.save(os.path.join(OUTPUT, 'heatmap_temporelle_bordeaux.html'))
print('  heatmap_temporelle_bordeaux.html OK')

# ─── Tâche 4 : Carte Plotly Mapbox ────────────────────────────────────────────
print()
print('=== TACHE 4 : dashboard_carte_arrets.html ===')
stop_map = df.groupby(['stop_name', 'stop_lat', 'stop_lon', 'transport_type']).size().reset_index(name='nb_passages')
stop_map = stop_map.dropna(subset=['stop_lat', 'stop_lon'])
fig4 = px.scatter_mapbox(
    stop_map,
    lat='stop_lat', lon='stop_lon',
    size='nb_passages', color='transport_type',
    hover_name='stop_name',
    mapbox_style='carto-positron',
    center={'lat': BORDEAUX_LAT, 'lon': BORDEAUX_LON},
    zoom=12,
    title='Carte des arrets TBM — Taille = Frequence de desserte',
    size_max=20
)
fig4.write_html(os.path.join(OUTPUT, 'dashboard_carte_arrets.html'))
print('  dashboard_carte_arrets.html OK')

# ─── Tâche 5 : Dashboard passages/heure ───────────────────────────────────────
print()
print('=== TACHE 5 : dashboard_passages_heure.html ===')
ph = df.groupby('hour').size().reset_index(name='nb_passages')
fig5 = px.bar(
    ph, x='hour', y='nb_passages',
    color='nb_passages',
    color_continuous_scale='YlOrRd',
    labels={'hour': 'Heure', 'nb_passages': 'Nombre de passages'},
    title='Passages par heure — TBM Bordeaux'
)
fig5.write_html(os.path.join(OUTPUT, 'dashboard_passages_heure.html'))
print('  dashboard_passages_heure.html OK')

# ─── Tâche 6 : Dashboard top arrêts ───────────────────────────────────────────
print()
print('=== TACHE 6 : dashboard_top_arrets.html ===')
top20 = df['stop_name'].value_counts().head(20).reset_index()
top20.columns = ['stop_name', 'nb_passages']
fig6 = px.bar(
    top20.sort_values('nb_passages'), x='nb_passages', y='stop_name',
    orientation='h',
    color='nb_passages',
    color_continuous_scale='Viridis',
    labels={'nb_passages': 'Nombre de passages', 'stop_name': 'Arret'},
    title='Top 20 arrets les plus desservis — TBM Bordeaux'
)
fig6.write_html(os.path.join(OUTPUT, 'dashboard_top_arrets.html'))
print('  dashboard_top_arrets.html OK')

# ─── Tâche 7 : PNG pour le rapport ────────────────────────────────────────────
print()
print('=== TACHE 7 : PNG rapport ===')

# pie_transport.png
transport_counts = df['transport_type'].value_counts()
filtered = transport_counts[transport_counts.index.isin(['Tramway','Bus'])]
colors_pie = ['#e74c3c', '#3498db']
fig7a, ax = plt.subplots(figsize=(8, 6))
ax.pie(filtered.values, labels=filtered.index, autopct='%1.1f%%',
       colors=colors_pie, startangle=90)
ax.set_title('Repartition Tramway vs Bus — TBM Bordeaux', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'pie_transport.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  pie_transport.png OK')

# bar_tranche_transport.png
order_ts = ['Nuit', 'Pointe matin', 'Heures creuses', 'Pointe soir', 'Soiree']
df_tb = df[df['transport_type'].isin(['Bus','Tramway'])]
pivot_tt = df_tb.pivot_table(index='time_slot', columns='transport_type', values='trip_id', aggfunc='count', fill_value=0)
pivot_tt = pivot_tt.reindex([x for x in order_ts if x in pivot_tt.index])
fig7b, ax = plt.subplots(figsize=(10, 6))
pivot_tt.plot(kind='bar', ax=ax, color=['#3498db', '#e74c3c'], edgecolor='white')
ax.set_title('Passages par tranche horaire et type de transport', fontsize=14, fontweight='bold')
ax.set_xlabel('Tranche horaire')
ax.set_ylabel('Nombre de passages')
ax.legend(title='Type')
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'bar_tranche_transport.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  bar_tranche_transport.png OK')

# bar_top10_lignes.png
top10 = df['route_short_name'].value_counts().head(10)
fig7c, ax = plt.subplots(figsize=(10, 6))
colors_top10 = plt.cm.tab10(np.linspace(0, 1, 10))
ax.barh(top10.index[::-1], top10.values[::-1], color=colors_top10)
ax.set_title('Top 10 lignes les plus desservies — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de passages')
ax.set_ylabel('Ligne')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'bar_top10_lignes.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  bar_top10_lignes.png OK')

# ─── Tâche 8 : Inventaire ─────────────────────────────────────────────────────
print()
print('=== INVENTAIRE /data/output/ ===')
for f in sorted(os.listdir(OUTPUT)):
    ext = os.path.splitext(f)[1]
    ftype = 'HTML' if ext == '.html' else 'PNG'
    size_kb = os.path.getsize(os.path.join(OUTPUT, f)) / 1024
    print(f'  [{ftype}] {f:<45} {size_kb:>8.1f} Ko')

print()
print('=================================================')
print('   OK SCRIPT VISUALISATION - TERMINE')
print('=================================================')
