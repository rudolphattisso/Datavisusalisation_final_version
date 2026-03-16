import os
import pandas as pd
import numpy as np

# Script de nettoyage et de préparation des données GTFS TBM Bordeaux.
# Ce script charge les fichiers bruts, nettoie les valeurs, fusionne les tables,
# enrichit les colonnes temporelles et exporte des jeux de données prêts à analyser.

BASE = r'c:\Users\attis\Documents\002_EPSI\00_Cours\visualisation de données\dataviz_Final'
RAW  = os.path.join(BASE, 'data', 'raw', 'gtfs')
OUT  = os.path.join(BASE, 'data', 'processed')

print('=== SCRIPT NETTOYAGE — CHARGEMENT ===')

# Tâche 1 : Chargement
dfs = {}
for f in ['agency.txt', 'stops.txt', 'routes.txt', 'trips.txt', 'stop_times.txt', 'calendar.txt']:
    df = pd.read_csv(os.path.join(RAW, f), low_memory=False)
    dfs[f.replace('.txt', '')] = df
    print(f'  {f}: {df.shape[0]:>8,} x {df.shape[1]} cols | aperçu cols: {list(df.columns)[:4]}')

print()
print('=== NETTOYAGE ===')

# stops : supprimer lignes sans coordonnées ou nom
s = dfs['stops']
before = len(s)
s = s.dropna(subset=['stop_lat', 'stop_lon', 'stop_name'])
s = s.drop_duplicates()
dfs['stops'] = s
print(f'  stops: {before} -> {len(s)} lignes (supprimé {before - len(s)} invalides/doublons)')

# stop_times : supprimer sans arrival_time / departure_time
st = dfs['stop_times']
before = len(st)
st = st.dropna(subset=['arrival_time', 'departure_time'])
st = st.drop_duplicates()
print(f'  stop_times: {before:,} -> {len(st):,} lignes')

# Correction horaires GTFS > 24:00:00
def fix_gtfs_time(t):
    try:
        parts = str(t).strip().split(':')
        h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
        h = h % 24
        return f'{h:02d}:{m:02d}:{sec:02d}'
    except Exception:
        return t

mask_arr = st['arrival_time'].apply(
    lambda t: int(str(t).split(':')[0]) >= 24 if pd.notna(t) else False
)
mask_dep = st['departure_time'].apply(
    lambda t: int(str(t).split(':')[0]) >= 24 if pd.notna(t) else False
)
corrected = int(mask_arr.sum()) + int(mask_dep.sum())
st['arrival_time']   = st['arrival_time'].apply(fix_gtfs_time)
st['departure_time'] = st['departure_time'].apply(fix_gtfs_time)
dfs['stop_times'] = st
print(f'  stop_times: {corrected:,} horaires > 24h corriges')

# trips, routes, calendar
for name in ['trips', 'routes', 'calendar']:
    df = dfs[name]
    before = len(df)
    df = df.drop_duplicates()
    missing = int(df.isnull().sum().sum())
    dfs[name] = df
    print(f'  {name}: {len(df):,} lignes | doublons supprimes: {before - len(df)} | missings: {missing}')

print()
print('=== FUSION ===')

# Tâche 3 : Fusion séquentielle
merged = st.merge(
    dfs['trips'][['trip_id', 'route_id', 'service_id', 'direction_id']],
    on='trip_id', how='left'
)
print(f'  Apres merge stop_times + trips   : {len(merged):,} lignes')

merged = merged.merge(
    dfs['routes'][['route_id', 'route_short_name', 'route_long_name', 'route_type']],
    on='route_id', how='left'
)
print(f'  Apres merge + routes             : {len(merged):,} lignes')

# Harmoniser le type de stop_id avant la jointure
merged['stop_id'] = merged['stop_id'].astype(str)
dfs['stops']['stop_id'] = dfs['stops']['stop_id'].astype(str)
merged = merged.merge(
    dfs['stops'][['stop_id', 'stop_name', 'stop_lat', 'stop_lon']],
    on='stop_id', how='left'
)
print(f'  Apres merge + stops              : {len(merged):,} lignes')

cal_cols = ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
merged = merged.merge(dfs['calendar'][cal_cols], on='service_id', how='left')
print(f'  Apres merge + calendar           : {len(merged):,} lignes')

print()
print('=== ENRICHISSEMENT ===')

# hour
merged['hour'] = merged['arrival_time'].apply(
    lambda t: int(str(t).split(':')[0]) if pd.notna(t) else np.nan
)

# time_slot
def time_slot(h):
    if pd.isna(h):
        return 'Inconnu'
    h = int(h)
    if 6 <= h <= 8:
        return 'Pointe matin'
    if 9 <= h <= 15:
        return 'Heures creuses'
    if 16 <= h <= 19:
        return 'Pointe soir'
    if 20 <= h <= 23:
        return 'Soiree'
    return 'Nuit'

merged['time_slot'] = merged['hour'].apply(time_slot)

# transport_type
_transport_map = {0: 'Tramway', 1: 'Metro', 2: 'Train', 3: 'Bus', 4: 'Ferry'}

def transport_type(r):
    if pd.isna(r):
        return 'Inconnu'
    return _transport_map.get(int(r), 'Autre')

merged['transport_type'] = merged['route_type'].apply(transport_type)

# is_weekday / is_weekend / day_type
days_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
days_we   = ['saturday', 'sunday']
merged['is_weekday'] = merged[days_week].fillna(0).astype(int).max(axis=1)
merged['is_weekend'] = merged[days_we].fillna(0).astype(int).max(axis=1)
merged['day_type'] = merged.apply(
    lambda r: 'Semaine' if r['is_weekday'] == 1 else ('Week-end' if r['is_weekend'] == 1 else 'Inconnu'),
    axis=1
)

print(f'  Colonnes enrichies: hour, time_slot, transport_type, is_weekday, is_weekend, day_type')
print(f'  Dataset final: {merged.shape[0]:,} lignes x {merged.shape[1]} colonnes')
print()

# Tâche 5 : Export
print('=== EXPORT ===')
merged.to_csv(os.path.join(OUT, 'bordeaux_tbm_merged.csv'), index=False)
print(f'  bordeaux_tbm_merged.csv ({len(merged):,} lignes)')

tram = merged[merged['transport_type'] == 'Tramway']
tram.to_csv(os.path.join(OUT, 'bordeaux_tramway.csv'), index=False)
print(f'  bordeaux_tramway.csv ({len(tram):,} lignes)')

bus = merged[merged['transport_type'] == 'Bus']
bus.to_csv(os.path.join(OUT, 'bordeaux_bus.csv'), index=False)
print(f'  bordeaux_bus.csv ({len(bus):,} lignes)')

stops_unique = (
    merged
    .groupby(['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'transport_type'])
    .size()
    .reset_index(name='nb_passages')
    .sort_values('nb_passages', ascending=False)
)
stops_unique.to_csv(os.path.join(OUT, 'bordeaux_stops.csv'), index=False)
print(f'  bordeaux_stops.csv ({len(stops_unique):,} arrets uniques)')

print()
print('=== RAPPORT DE NETTOYAGE ===')
print(f'  Horaires corriges (>24h)   : {corrected:,}')
print('  Repartition par transport  :')
print(merged['transport_type'].value_counts().to_string())
print('  Repartition par tranche    :')
order = ['Pointe matin', 'Heures creuses', 'Pointe soir', 'Soiree', 'Nuit']
print(merged['time_slot'].value_counts().reindex(order).to_string())
n_stops  = merged['stop_name'].nunique()
n_routes = merged['route_short_name'].nunique()
print(f'  Arrets uniques             : {n_stops:,}')
print(f'  Lignes uniques             : {n_routes:,}')

print()
print('=================================================')
print('   OK SCRIPT NETTOYAGE - TERMINE')
print('=================================================')
