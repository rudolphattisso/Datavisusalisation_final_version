import os
import pandas as pd

# Script de génération de recommandations opérationnelles pour TBM Bordeaux.
# Ce script synthétise les constats de l'analyse et produit des recommandations
# priorisées ainsi que les limites et pistes d'amélioration.

BASE  = r'c:\Users\attis\Documents\002_EPSI\00_Cours\visualisation de données\dataviz_Final'
PROC  = os.path.join(BASE, 'data', 'processed')

print('=== SCRIPT RECOMMANDATIONS — CHARGEMENT ===')
df = pd.read_csv(os.path.join(PROC, 'bordeaux_tbm_merged.csv'), low_memory=False)
print(f'  Dataset charge : {len(df):,} lignes')

# ─── Tâche 1 : Synthèse chiffrée ──────────────────────────────────────────────
print()
print('=== SYNTHESE CHIFFREE ===')

ph = df.groupby('hour').size()
h_pm_val  = ph[ph.index.isin(range(6,10))].idxmax()
h_ps_val  = ph[ph.index.isin(range(16,21))].idxmax()
h_min_val = ph.idxmin()

n_pm  = ph[h_pm_val]
n_ps  = ph[h_ps_val]
n_min = ph[h_min_val]

pct_pointe = (df['time_slot'].isin(['Pointe matin','Pointe soir'])).sum() / len(df) * 100

ligne_counts = df['route_short_name'].value_counts()
top5_lignes = ligne_counts.head(5)
bot5_lignes = ligne_counts.tail(5)

arret_counts = df['stop_name'].value_counts()
top5_arrets  = arret_counts.head(5)

apres_22 = set(df[df['hour'] >= 22]['route_short_name'].unique())
toutes   = set(df['route_short_name'].unique())
n_sans_nuit = len(toutes - apres_22)

n_sem = (df['day_type'] == 'Semaine').sum()
n_we  = (df['day_type'] == 'Week-end').sum()
pct_reduction_we = (1 - n_we / n_sem) * 100 if n_sem > 0 else 0

stop_lines   = df.groupby('stop_name')['route_short_name'].nunique()
n_mono_stop  = (stop_lines == 1).sum()

print(f'  Heure de pointe matin   : {h_pm_val}h ({n_pm:,} passages)')
print(f'  Heure de pointe soir    : {h_ps_val}h ({n_ps:,} passages)')
print(f'  Heure la plus creuse    : {h_min_val}h ({n_min:,} passages)')
print(f'  % passages en pointe    : {pct_pointe:.1f}%')
print()
print('  Top 5 lignes les plus desservies :')
for l, v in top5_lignes.items():
    print(f'    {l}: {v:,}')
print('  Top 5 lignes les moins desservies :')
for l, v in bot5_lignes.items():
    print(f'    {l}: {v:,}')
print('  Top 5 arrets les plus desservis :')
for a, v in top5_arrets.items():
    print(f'    {a}: {v:,}')
print(f'  Lignes actives apres 22h        : {len(apres_22)} (sur {len(toutes)})')
print(f'  Lignes sans service apres 22h   : {n_sans_nuit}')
print(f'  Reduction desserte week-end     : {pct_reduction_we:.1f}%')
print(f'  Arrets desservis par 1 seule ligne : {n_mono_stop}')

# ─── Tâche 2 : Identification des problèmes ────────────────────────────────────
print()
print('=== PROBLEMES IDENTIFIES ===')

tram_pct = (df['transport_type'] == 'Tramway').sum() / len(df) * 100
bus_pct  = (df['transport_type'] == 'Bus').sum() / len(df) * 100
ferry_pct= (df['transport_type'] == 'Ferry').sum() / len(df) * 100

pb = f"""
1. SURCHARGE AUX HEURES DE POINTE
   {pct_pointe:.1f}% des passages sont concentres aux heures de pointe (8h et 17h).
   Les lignes B, A, C (tramway) et principales lignes de bus absorbent l essentiel
   de la demande entre 7h-9h et 16h-19h. Ce desequilibre cree des risques de saturation.

2. FAIBLE DESSERTE EN SOIREE ET NUIT
   {n_sans_nuit} lignes sur {len(toutes)} ne fonctionnent pas apres 22h (soit {n_sans_nuit/len(toutes)*100:.0f}%).
   Le reseau est peu adapte aux horaires decales et aux travailleurs de nuit.

3. DESEQUILIBRE TRAMWAY / BUS
   Le tramway represente {tram_pct:.1f}% des passages, le bus {bus_pct:.1f}%.
   Malgre une capacite superieure du tramway, les bus assurent la desserte de
   la majorite du territoire de la metropole, avec des frequences variables.

4. REDUCTION EXCESSIVE LE WEEK-END
   La desserte baisse de {pct_reduction_we:.1f}% le week-end par rapport a la semaine.
   Cette reduction est particulierement penalisante pour les usagers sans voiture.

5. ARRETS MAL CONNECTES
   {n_mono_stop} arrets sont desservis par une seule ligne, rendant les correspondances
   impossibles et limitant l accessibilite de zones peripheriques.
"""
print(pb)

# ─── Tâche 3 : Recommandations ────────────────────────────────────────────────
print()
print('=== RECOMMANDATIONS ===')

recs = f"""
PRIORITE HAUTE

[ROUGE] R1 : Renforcer la frequence sur les lignes critiques aux heures de pointe
  Probleme  : {pct_pointe:.1f}% des passages se concentrent sur 4h de la journee (8h et 17h),
              la ligne B enregistrant {ligne_counts.get('B', 0):,} passages.
  Solution  : Doubler la frequence (passage toutes les 3-4 min au lieu de 6-8 min)
              sur les lignes Tramway A, B, C de 7h a 9h et de 16h a 19h.
  Lignes    : A, B, C (tramway), lignes de bus 1, 9, 15, 35
  Impact    : Reduction de la saturation, meilleure regularite, attractivite accrue

[ROUGE] R2 : Etendre le service nocturne sur les axes principaux
  Probleme  : {n_sans_nuit} lignes ({n_sans_nuit/len(toutes)*100:.0f}%) ne fonctionnent plus apres 22h,
              laissant de larges zones sans transport.
  Solution  : Creer ou etendre des lignes Liane noctambules sur les 5 axes principaux
              jusqu a 1h du matin, avec une frequence de 30 minutes.
  Lignes    : Tramway A+B + 4 lignes bus principales
  Impact    : Accessibilite pour travailleurs de nuit et sorties culturelles/festives

PRIORITE MOYENNE

[JAUNE] R3 : Ameliorer la desserte du week-end
  Probleme  : Reduction de {pct_reduction_we:.1f}% de la desserte le week-end.
  Solution  : Maintenir au minimum 70% de l offre semaine le samedi et 60% le dimanche,
              avec des renforts ponctuels pour les evenements culturels et sportifs.
  Impact    : Meilleure accessibilite, incitation a laisser la voiture au garage

[JAUNE] R4 : Ameliorer la connexion des arrets mono-ligne
  Probleme  : {n_mono_stop} arrets sont desservis par une seule ligne.
  Solution  : Identifier les {n_mono_stop} arrets isoles et proposer au moins une alternative
              de correspondance (navette, TAD - transport a la demande) dans un rayon de 500m.
  Impact    : Reduction des zones d exclusion, equite territoriale

PRIORITE BASSE

[VERT] R5 : Optimiser les lignes faiblement utilisees
  Probleme  : {len(bot5_lignes)} lignes enregistrent moins de {bot5_lignes.min()} passages.
  Solution  : Etudier la transformation des lignes tres faibles (< 100 passages) en
              transport a la demande (TAD) ou en navettes scolaires/entreprise.
  Impact    : Economies budgetaires reinvestissables, meilleure efficacite du reseau
"""
print(recs)

# ─── Tâche 4 : Limites de l'analyse ───────────────────────────────────────────
print()
print('=== LIMITES DE L ANALYSE ===')

limites = """
1. DONNEES GTFS = OFFRE, PAS DEMANDE REELLE
   Les donnees GTFS decrivent les horaires planifies par TBM.
   Le nombre de passages est un proxy de l offre theorique, pas de l affluence reelle.
   Un arret peu desservi peut etre tres frequente (bus plein) et vice-versa.

2. ABSENCE DE DONNEES DE BILLETIQUE
   Sans donnees de validation de titres, il est impossible de connaitre :
   - Le nombre reel de voyageurs par arret ou par ligne
   - Le taux de remplissage des vehicules
   - Les origines-destinations des voyageurs

3. PERIODE D ANALYSE LIMITEE
   Les donnees couvrent une periode definie dans le feed GTFS (voir feed_info.txt).
   Les evenements exceptionnels (vacances scolaires, evenements sportifs, greves)
   ne sont pas pris en compte.

4. ABSENCE DE DONNEES TEMPS REEL
   Pas d information sur les retards, suppressions ou modifications de service.
   L analyse porte uniquement sur le service theorique programme.

5. GRANULARITE GEOGRAPHIQUE
   L analyse est realisee a l echelle des arrets, sans croisement avec :
   - La densite de population par quartier
   - Les zones d emploi et de commerce
   - Les poles generateurs de deplacements (gares, hopitaux, universites)
"""
print(limites)

# ─── Tâche 5 : Pistes d'amélioration ──────────────────────────────────────────
print()
print('=== PISTES D AMELIORATION ===')
pistes = """
1. Integration des donnees de billetique TBM (validations par arret et par heure)
2. Croisement avec les donnees demographiques INSEE (population par IRIS)
3. Utilisation de donnees temps reel (API TBM / GTFS-RT) pour analyser la ponctualite
4. Application de modeles predictifs (ML) pour anticiper la demande par periode
5. Benchmark avec d autres reseaux metropolitains francais (Nantes, Lyon, Toulouse)
"""
print(pistes)

print()
print('=== TEXTE PRET POUR LE RAPPORT ===')
print('  [Toutes les sections ci-dessus peuvent etre integrees directement dans le rapport]')
print()
print('=================================================')
print('   OK SCRIPT RECOMMANDATIONS - TERMINE')
print('=================================================')
