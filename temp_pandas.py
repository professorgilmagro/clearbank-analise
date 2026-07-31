LIMITE_SUSPEITO = 10000.00
CSV_PATH = '/content/transacoes.csv'

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style="white", context="talk")

dados = pd.read_csv(CSV_PATH)

def limpar_dados(dados):
  dados_limpos = dados.copy()

  # 1. Validar 'id': deve ser numérico e não nulo
  dados_limpos['id_numerico'] = pd.to_numeric(dados_limpos['id'], errors='coerce')
  condicao_id = dados_limpos['id_numerico'].notna()

  # 2. Validar 'cliente_id': não deve ser nulo
  condicao_cliente_id = dados_limpos['cliente_id'].notna()

  # 3. Validar 'data': formato AAAA-MM-DD e converter para datetime
  dados_limpos['data_dt'] = pd.to_datetime(dados_limpos['data'], errors='coerce', format='%Y-%m-%d')
  condicao_data = dados_limpos['data_dt'].notna()

  # 4. Validar 'tipo': deve ser 'credito' ou 'debito'
  condicao_tipo = dados_limpos['tipo'].isin(['credito', 'debito'])

  # 5. Validar 'valor': deve ser numérico e maior que zero
  dados_limpos['valor_numerico'] = pd.to_numeric(dados_limpos['valor'], errors='coerce')
  condicao_valor = (dados_limpos['valor_numerico'].notna()) & (dados_limpos['valor_numerico'] > 0)

  # Combinar todas as condições para identificar linhas válidas
  condicoes_validas = condicao_id & condicao_cliente_id & condicao_data & condicao_tipo & condicao_valor

  # Filtrar o DataFrame para manter apenas linhas válidas
  dados_validos = dados_limpos[condicoes_validas].copy()

  # Converter colunas para os tipos finais desejados após a filtragem
  dados_validos['id'] = dados_validos['id_numerico'].astype(int)
  dados_validos['data'] = dados_validos['data_dt']
  dados_validos['valor'] = dados_validos['valor_numerico'].astype(float)

  # Criar a coluna 'mes_ref' (AAAA-MM)
  dados_validos['mes_ref'] = dados_validos['data'].dt.strftime('%Y-%m')

  # Manter apenas as colunas originais mais 'mes_ref'
  colunas_finais = [
      'id', 'cliente_id', 'data', 'tipo', 'valor', 'descricao', 'categoria', 'mes_ref'
  ]

  return dados_validos[colunas_finais]


dados_validos = limpar_dados(dados)
print(f"Total de linhas antes da limpeza: {len(dados)}")
print(f"Total de linhas válidas após a limpeza: {len(dados_validos)}")

# Calcular o saldo mensal (crédito - débito)
def saldo_mensal():
  saldo_mensal = dados_validos.copy()
  saldo_mensal['valor_ajustado'] = np.where(saldo_mensal['tipo'] == 'credito', saldo_mensal['valor'], -saldo_mensal['valor'])
  return saldo_mensal.groupby('mes_ref')['valor_ajustado'].sum().reset_index()

# Transações do tipo débito
def dados_debito():
  return dados_validos[dados_validos['tipo'] == 'debito']

plt.figure(figsize=(12, 6))
sns.barplot(x='mes_ref', y='valor_ajustado', data=saldo_mensal())
plt.title('Saldo Mensal (Crédito - Débito) por Mês')
plt.xlabel('Mês de Referência')
plt.ylabel('Saldo (Crédito - Débito)')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
# Calcular o total de débito por mês
total_debito_por_mes = dados_debito().groupby('mes_ref')['valor'].sum().reset_index()

plt.figure(figsize=(12, 6))
sns.lineplot(x='mes_ref', y='valor', data=total_debito_por_mes, marker='o')
plt.title('Evolução do Total de Débito ao Longo dos Meses')
plt.xlabel('Mês de Referência')
plt.ylabel('Total de Débito')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
plt.figure(figsize=(12, 6))
sns.countplot(x='mes_ref', hue='tipo', data=dados_validos)
plt.title('Crédito e Débito por Mês')
plt.xlabel('Mês de Referência')
plt.ylabel('Quantidade')
plt.show()


fig, axes = plt.subplots(2, 2, figsize=(20, 15))
fig.suptitle('Análise Consolidada das Transações', fontsize=20, y=1.02, fontweight='bold')

# Gráfico 1: Saldo Mensal por Tipo de Transação
sns.barplot(x='mes_ref', y='valor_ajustado', data=saldo_mensal(), ax=axes[0, 0])
axes[0, 0].set_title('Saldo Mensal por Tipo de Transação', fontweight='bold')
axes[0, 0].set_xlabel('Mês de Referência')
axes[0, 0].set_ylabel('Saldo')

# Gráfico 2: Evolução do Total de Débito ao Longo dos Meses
total_debito_por_mes = dados_debito().groupby('mes_ref')['valor'].sum().reset_index()
sns.lineplot(x='mes_ref', y='valor', data=total_debito_por_mes, ax=axes[0, 1], marker='o')
axes[0, 1].set_title('Evolução do Total de Débito ao Longo dos Meses', fontweight='bold')
axes[0, 1].set_xlabel('Mês de Referência')
axes[0, 1].set_ylabel('Total de Débito')


# Gráfico 3: Crédito e Débito por Mês
sns.countplot(x='mes_ref', hue='tipo', data=dados_validos, ax=axes[1, 0], palette='pastel')
axes[1, 0].set_title('Crédito e Débito por Mês', fontweight='bold')
axes[1, 0].set_xlabel('Mês de Referência')
axes[1, 0].set_ylabel('Quantidade')

# Gráfico 4: Proporção de Gastos por Categoria (Débito)
gastos_por_categoria = dados_debito().groupby('categoria')['valor'].sum()
axes[1, 1].pie(gastos_por_categoria, labels=gastos_por_categoria.index, autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
axes[1, 1].set_title('Proporção de Gastos por Categoria (Débito)', fontweight='bold')
axes[1, 1].set_ylabel('')
axes[1, 1].axis('equal')

plt.tight_layout()
fig.subplots_adjust(hspace=0.4)
plt.show()
