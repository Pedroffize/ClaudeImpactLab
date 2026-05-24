import pandas as pd

path = r"c:\Users\pedro\Documents\2026\ClaudeImpactLab\dados\df_ocorrencias_tratado - Extração 1 .csv"
df = pd.read_csv(path, encoding='utf-8', low_memory=False)

# Parse datas (formato DD/MM/YYYY)
df['data_parsed'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
df['ano_parsed'] = df['data_parsed'].dt.year

# Conta por intervalo de ano
print("Distribuição de anos na coluna 'data':")
print(df['ano_parsed'].value_counts().sort_index().to_string())
print()
valid_mask = df['ano_parsed'].between(2020, 2024)
print(f"Datas válidas (2020-2024): {valid_mask.sum():,} / {len(df):,} ({valid_mask.mean():.1%})")
print()

# Cross-check: registros válidos têm ano coerente entre 'ano' e 'data_parsed'?
coerente = df[valid_mask & df['ano'].between(2020,2024)]
print(f"ano (campo) == ano (data_parsed): {(coerente['ano'] == coerente['ano_parsed']).mean():.1%}")
print()

# Mostra exemplos de datas válidas
print("Exemplos de datas válidas:")
print(df[valid_mask][['data','ano','mes','dia_semana']].head(10).to_string())
