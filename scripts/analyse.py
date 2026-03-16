import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

# Script d'analyse descriptive des passages TBM Bordeaux.
# Ce script calcule des indicateurs clés, détecte des anomalies et génère
# des graphiques PNG pour l'exploration temporelle, géographique et par ligne.

BASE    = r'c:\Users\attis\Documents\002_EPSI\00_Cours\visualisation de données\dataviz_Final'
PROC    = os.path.join(BASE, 'data', 'processed')
OUTPUT  = os.path.join(BASE, 'data', 'output')
os.makedirs(OUTPUT, exist_ok=True)

print('=== SCRIPT ANALYSE — CHARGEMENT ===')
df = pd.read_csv(os.path.join(PROC, 'bordeaux_tbm_merged.csv'), low_memory=False)
print(f'  Dataset charge : {len(df):,} lignes x {df.shape[1]} colonnes')

# ─── Tâche 1 : Vue d'ensemble ──────────────────────────────────────────────────
print()
print('=== VUE D ENSEMBLE ===')
print(f'  Passages totaux          : {len(df):,}')
print(f'  Lignes uniques           : {df["route_short_name"].nunique():,}')
print(f'  Arrets uniques           : {df["stop_name"].nunique():,}')
print('  Repartition transport    :')
tc = df['transport_type'].value_counts()
for k, v in tc.items():
    print(f'    {k}: {v:,} ({v/len(df)*100:.1f}%)')
print('  Repartition tranche      :')
order_ts = ['Pointe matin', 'Heures creuses', 'Pointe soir', 'Soiree', 'Nuit']
for k in order_ts:
    v = (df['time_slot'] == k).sum()
    print(f'    {k}: {v:,} ({v/len(df)*100:.1f}%)')
print('  Repartition jour         :')
for k, v in df['day_type'].value_counts().items():
    print(f'    {k}: {v:,} ({v/len(df)*100:.1f}%)')

# ─── Tâche 2 : Analyse temporelle ─────────────────────────────────────────────
passages_heure = df.groupby('hour').size().reset_index(name='count').sort_values('hour')

# 1. passages_par_heure.png
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(passages_heure['hour'], passages_heure['count'], color='steelblue', edgecolor='white')
# Annoter pointes
df_matin = passages_heure[passages_heure['hour'].between(6, 9)]
df_soir  = passages_heure[passages_heure['hour'].between(16, 20)]
h_matin  = df_matin.loc[df_matin['count'].idxmax()]
h_soir   = df_soir.loc[df_soir['count'].idxmax()]
ax.annotate(f"Pointe matin\n{int(h_matin['hour'])}h", xy=(h_matin['hour'], h_matin['count']),
            xytext=(h_matin['hour']+1, h_matin['count']*1.05), fontsize=9, color='darkred',
            arrowprops=dict(arrowstyle='->', color='darkred'))
ax.annotate(f"Pointe soir\n{int(h_soir['hour'])}h", xy=(h_soir['hour'], h_soir['count']),
            xytext=(h_soir['hour']+1, h_soir['count']*1.05), fontsize=9, color='darkorange',
            arrowprops=dict(arrowstyle='->', color='darkorange'))
ax.set_title('Nombre de passages par heure — Reseau TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Heure')
ax.set_ylabel('Nombre de passages')
ax.set_xticks(range(0, 24))
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'passages_par_heure.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  passages_par_heure.png OK')

# 2. passages_par_tranche.png
order_ts2 = ['Nuit', 'Pointe matin', 'Heures creuses', 'Pointe soir', 'Soiree']
tc_vals = df['time_slot'].value_counts().reindex(order_ts2).fillna(0)
colors_ts = ['#2c7bb6', '#d7191c', '#abd9e9', '#fdae61', '#ffffbf']
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(tc_vals.index, tc_vals.values, color=colors_ts, edgecolor='white')
ax.set_title('Passages par tranche horaire — Reseau TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Tranche horaire')
ax.set_ylabel('Nombre de passages')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'passages_par_tranche.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  passages_par_tranche.png OK')

# 3. semaine_vs_weekend.png
df_sem = df[df['day_type'] == 'Semaine'].groupby('hour').size().reset_index(name='Semaine')
df_we  = df[df['day_type'] == 'Week-end'].groupby('hour').size().reset_index(name='Week-end')
merged_time = df_sem.merge(df_we, on='hour', how='outer').sort_values('hour').fillna(0)
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(merged_time['hour'], merged_time['Semaine'],  marker='o', label='Semaine',  color='steelblue')
ax.plot(merged_time['hour'], merged_time['Week-end'], marker='s', label='Week-end', color='tomato')
ax.set_title('Comparaison passages semaine vs week-end — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Heure')
ax.set_ylabel('Nombre de passages')
ax.legend()
ax.set_xticks(range(0, 24))
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'semaine_vs_weekend.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  semaine_vs_weekend.png OK')

# ─── Tâche 3 : Analyse par ligne ───────────────────────────────────────────────
top_lignes   = df['route_short_name'].value_counts().head(15)
bot_lignes   = df['route_short_name'].value_counts().tail(10)

# 4. top_lignes.png
fig, ax = plt.subplots(figsize=(12, 7))
sns.barplot(x=top_lignes.values, y=top_lignes.index, palette='viridis', ax=ax)
ax.set_title('Top 15 des lignes les plus desservies — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de passages')
ax.set_ylabel('Ligne')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'top_lignes.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  top_lignes.png OK')

# 5. tram_vs_bus.png
df_tram = df[df['transport_type'] == 'Tramway'].groupby('hour').size().reset_index(name='Tramway')
df_bus  = df[df['transport_type'] == 'Bus'].groupby('hour').size().reset_index(name='Bus')
merged_tb = df_tram.merge(df_bus, on='hour', how='outer').sort_values('hour').fillna(0)
fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(merged_tb['hour'], merged_tb['Tramway'], marker='o', label='Tramway', color='crimson')
ax.plot(merged_tb['hour'], merged_tb['Bus'],     marker='s', label='Bus',     color='royalblue')
ax.set_title('Passages par heure : Tramway vs Bus — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Heure')
ax.set_ylabel('Nombre de passages')
ax.legend()
ax.set_xticks(range(0, 24))
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'tram_vs_bus.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  tram_vs_bus.png OK')

# 6. bottom_lignes.png
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(bot_lignes.index, bot_lignes.values, color='salmon', edgecolor='white')
ax.set_title('10 lignes les moins desservies — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de passages')
ax.set_ylabel('Ligne')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'bottom_lignes.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  bottom_lignes.png OK')

# ─── Tâche 4 : Analyse géographique ───────────────────────────────────────────
top_arrets = df['stop_name'].value_counts().head(20)
bot_arrets = df['stop_name'].value_counts().tail(20)

# 7. top_arrets.png
fig, ax = plt.subplots(figsize=(12, 8))
sns.barplot(x=top_arrets.values, y=top_arrets.index, palette='magma', ax=ax)
ax.set_title('Top 20 arrets les plus desservis — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de passages')
ax.set_ylabel('Arret')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'top_arrets.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  top_arrets.png OK')

# 8. bottom_arrets.png
fig, ax = plt.subplots(figsize=(12, 8))
ax.barh(bot_arrets.index, bot_arrets.values, color='lightcoral', edgecolor='white')
ax.set_title('20 arrets les moins desservis — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Nombre de passages')
ax.set_ylabel('Arret')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'bottom_arrets.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  bottom_arrets.png OK')

# ─── Tâche 5 : Heatmap horaire par ligne ──────────────────────────────────────
top15_lignes = df['route_short_name'].value_counts().head(15).index.tolist()
df_top15 = df[df['route_short_name'].isin(top15_lignes)]
pivot = df_top15.pivot_table(index='route_short_name', columns='hour', values='trip_id', aggfunc='count', fill_value=0)
pivot = pivot.reindex(top15_lignes)  # tri par fréquence

# 9. heatmap_lignes_heures.png
fig, ax = plt.subplots(figsize=(16, 8))
sns.heatmap(pivot, cmap='YlOrRd', linewidths=0.3, ax=ax)
ax.set_title('Heatmap : Frequence par ligne et par heure — TBM Bordeaux', fontsize=14, fontweight='bold')
ax.set_xlabel('Heure')
ax.set_ylabel('Ligne')
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'heatmap_lignes_heures.png'), dpi=150, bbox_inches='tight')
plt.close()
print('  heatmap_lignes_heures.png OK')

# ─── Tâche 6 : Anomalies ──────────────────────────────────────────────────────
print()
print('=== DETECTION ANOMALIES ===')

# Lignes forte concentration pointe
pointe_mask = df['time_slot'].isin(['Pointe matin', 'Pointe soir'])
pointe_ratio = (df[pointe_mask].groupby('route_short_name').size() /
                df.groupby('route_short_name').size()).sort_values(ascending=False).head(5)
print('  Top 5 lignes a forte concentration en pointe :')
print(pointe_ratio.to_string())

# Lignes sans service après 21h
lignes_apres_21 = set(df[df['hour'] >= 21]['route_short_name'].unique())
toutes_lignes   = set(df['route_short_name'].unique())
lignes_sans_nuit = toutes_lignes - lignes_apres_21
print(f'  Lignes sans service apres 21h : {len(lignes_sans_nuit)}')

# Arrêts mono-ligne
stop_lines = df.groupby('stop_name')['route_short_name'].nunique()
mono_stop  = stop_lines[stop_lines == 1]
print(f'  Arrets desservis par une seule ligne : {len(mono_stop)}')

# Ecart semaine / week-end
n_sem = (df['day_type'] == 'Semaine').sum()
n_we  = (df['day_type'] == 'Week-end').sum()
reduction = (1 - n_we / n_sem) * 100 if n_sem > 0 else 0
print(f'  Reduction desserte week-end vs semaine : {reduction:.1f}%')

# ─── Tâche 7 : Synthèse insights ──────────────────────────────────────────────
print()
print('=== INSIGHTS CLES — RESEAU TBM BORDEAUX ===')

df_pm = passages_heure[passages_heure['hour'].between(6,9)]
df_ps = passages_heure[passages_heure['hour'].between(16,20)]
h_pm  = df_pm.loc[df_pm['count'].idxmax()]
h_ps  = df_ps.loc[df_ps['count'].idxmax()]
h_creuse = passages_heure.loc[passages_heure['count'].idxmin()]
pct_pointe = (df['time_slot'].isin(['Pointe matin','Pointe soir'])).sum() / len(df) * 100

print('TEMPOREL')
print(f'  Heure de pointe matin  : {int(h_pm["hour"])}h ({int(h_pm["count"]):,} passages)')
print(f'  Heure de pointe soir   : {int(h_ps["hour"])}h ({int(h_ps["count"]):,} passages)')
print(f'  Heure la plus creuse   : {int(h_creuse["hour"])}h ({int(h_creuse["count"]):,} passages)')
print(f'  % passages en pointe   : {pct_pointe:.1f}%')

ligne_max = df['route_short_name'].value_counts().idxmax()
ligne_min = df['route_short_name'].value_counts().idxmin()
n_max = df['route_short_name'].value_counts().max()
n_min = df['route_short_name'].value_counts().min()
print()
print('PAR LIGNE')
print(f'  Ligne la plus desservie  : {ligne_max} ({n_max:,} passages)')
print(f'  Ligne la moins desservie : {ligne_min} ({n_min:,} passages)')
ntr = (df['transport_type'] == 'Tramway').sum()
nbus = (df['transport_type'] == 'Bus').sum()
print(f'  Ratio Tramway/Bus        : {ntr/len(df)*100:.1f}% / {nbus/len(df)*100:.1f}%')

arret_max = df['stop_name'].value_counts().idxmax()
arret_min = df['stop_name'].value_counts().idxmin()
print()
print('GEOGRAPHIQUE')
print(f'  Arret le plus desservi   : {arret_max} ({df["stop_name"].value_counts().max():,} passages)')
print(f'  Arret le moins desservi  : {arret_min} ({df["stop_name"].value_counts().min():,} passages)')
print(f'  Arrets mono-ligne        : {len(mono_stop)}')

print()
print('ANOMALIES')
print(f'  Lignes sans service apres 21h : {len(lignes_sans_nuit)}')
print(f'  Arrets a une seule ligne      : {len(mono_stop)}')
print(f'  Reduction desserte week-end   : {reduction:.0f}%')

# ─── Tâche 8 (optionnelle) : Modélisation prédictive baseline ───────────────
print()
print('=== MODELISATION PREDICTIVE (BASELINE) ===')

# Série horaire : on agrège l'offre par heure et type de jour.
serie = (
    df.groupby(['day_type', 'hour'])
      .size()
      .reset_index(name='count')
)

# Encodage simple + ordre temporel artificiel pour un modèle pédagogique.
serie['is_weekend'] = (serie['day_type'] == 'Week-end').astype(int)
serie = serie.sort_values(['day_type', 'hour']).reset_index(drop=True)
serie['t'] = np.arange(len(serie))
serie['lag_1'] = serie['count'].shift(1)
serie['lag_2'] = serie['count'].shift(2)
serie = serie.dropna().reset_index(drop=True)

X = serie[['t', 'hour', 'is_weekend', 'lag_1', 'lag_2']]
y = serie['count']

# Split chronologique (80/20) pour simuler une prévision de court terme.
split_idx = int(len(serie) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

model = LinearRegression()
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(y_test.values, label='Reel', marker='o', color='steelblue')
ax.plot(y_pred, label='Predit', marker='s', color='darkorange')
ax.set_title('Prevision d affluence horaire — modele lineaire (baseline)', fontsize=14, fontweight='bold')
ax.set_xlabel('Index test (chronologique)')
ax.set_ylabel('Nombre de passages')
ax.legend()
ax.text(
    0.02,
    0.95,
    f'MAE={mae:.0f} | R2={r2:.2f}',
    transform=ax.transAxes,
    verticalalignment='top',
    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT, 'predict_affluence_ml.png'), dpi=150, bbox_inches='tight')
plt.close()

print(f'  predict_affluence_ml.png OK | MAE={mae:.1f} | R2={r2:.3f}')

print()
print('=================================================')
print('   OK SCRIPT ANALYSE - TERMINE (10 graphiques PNG)')
print('=================================================')
