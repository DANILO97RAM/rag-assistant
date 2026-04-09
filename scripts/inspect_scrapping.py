"""
Script para analizar el contenido scrapeado y sugerir queries realistas.
"""
import pandas as pd
import json

# Cargar datos
pages = pd.read_parquet('data/scraped_pages.parquet')
chunks = pd.read_parquet('data/chunks.parquet')

print('📄 ANÁLISIS DE CONTENIDO SCRAPEADO')
print('=' * 70)
print(f'Total páginas: {len(pages)}')
print(f'Total chunks: {len(chunks)}')
print()

# Analizar categorías
categories = {}
for _, row in pages.iterrows():
    meta = json.loads(row['metadata'])
    cat = meta.get('category', 'sin-categoria')
    url = meta.get('url', '')
    title = meta.get('title', 'Sin título')
    
    if cat not in categories:
        categories[cat] = []
    categories[cat].append({
        'url': url,
        'title': title,
        'words': len(row['texto'].split())
    })

print(f'Categorías únicas: {len(categories)}')
print()

# TOP 10 categorías por contenido
print('🏆 TOP 10 CATEGORÍAS (por contenido total):')
print('-' * 70)
cat_words = {}
for cat, items in categories.items():
    total_words = sum(item['words'] for item in items)
    cat_words[cat] = total_words

for i, (cat, words) in enumerate(sorted(cat_words.items(), key=lambda x: x[1], reverse=True)[:10], 1):
    num_pages = len(categories[cat])
    print(f'{i:2}. {cat:35} {words:6} palabras ({num_pages} pág.)')

print()
print('📋 TOP 15 PÁGINAS CON MÁS CONTENIDO:')
print('-' * 70)

# Páginas individuales
all_pages = []
for _, row in pages.iterrows():
    meta = json.loads(row['metadata'])
    all_pages.append({
        'title': meta.get('title', 'Sin título'),
        'category': meta.get('category', 'sin-categoria'),
        'words': len(row['texto'].split()),
        'url': meta.get('url', '')
    })

for i, page in enumerate(sorted(all_pages, key=lambda x: x['words'], reverse=True)[:15], 1):
    title_short = page['title'][:50] + '...' if len(page['title']) > 50 else page['title']
    cat_short = page['category'][:28]
    print(f'{i:2}. [{cat_short:28}] {page["words"]:4} palabras')
    print(f'    {title_short}')
    print()

# Análisis de temas específicos
print()
print('🔍 ANÁLISIS TEMÁTICO:')
print('-' * 70)

temas_clave = {
    'Créditos': ['credito', 'prestamo', 'financiacion'],
    'Cuentas': ['cuenta', 'ahorro', 'nomina'],
    'Tarjetas': ['tarjeta'],
    'Seguros': ['seguro', 'proteccion'],
    'Inversiones': ['inversion', 'invertir'],
    'Pagos': ['pago', 'transferencia'],
}

for tema, keywords in temas_clave.items():
    matching_cats = []
    for cat in categories.keys():
        if any(kw in cat.lower() for kw in keywords):
            matching_cats.append(cat)
    
    if matching_cats:
        total = sum(cat_words.get(c, 0) for c in matching_cats)
        print(f'• {tema:15} → {len(matching_cats)} categorías, {total:5} palabras')
        for c in matching_cats[:3]:
            print(f'  - {c}')
    else:
        print(f'• {tema:15} → ⚠️  SIN CONTENIDO')

print()
print('💡 SUGERENCIAS DE QUERIES BASADAS EN CONTENIDO REAL:')
print('-' * 70)

# Sugerir queries realistas
queries_sugeridas = []

# Basadas en categorías con contenido
if 'creditos' in categories:
    queries_sugeridas.append('¿Qué tipos de créditos ofrece Bancolombia?')
if 'seguros' in categories:
    queries_sugeridas.append('¿Qué seguros tiene disponibles Bancolombia?')
if 'consumidor-financiero' in categories:
    queries_sugeridas.append('¿Qué es el consumidor financiero?')
if 'cuentas' in categories:
    queries_sugeridas.append('¿Cómo abrir una cuenta en Bancolombia?')
if 'preferencial' in categories:
    queries_sugeridas.append('¿Qué es la banca preferencial?')
if 'a-la-mano' in categories:
    queries_sugeridas.append('¿Qué es A la mano de Bancolombia?')

for i, q in enumerate(queries_sugeridas, 1):
    print(f'{i}. {q}')
