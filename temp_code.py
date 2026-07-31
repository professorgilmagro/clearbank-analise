# Configurações gerais
def setup():
    global LIMITE_SUSPEITO
    global CSV_PATH

    LIMITE_SUSPEITO = 10000.00
    CSV_PATH = '/content/transacoes.csv'

import csv

def ler_transacoes(csv_path):
    transactions = []
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                transactions.append(row)
        print(f"Arquivo '{csv_path}' lido com sucesso!")
        return transactions
    except FileNotFoundError:
        print(f"Erro: O arquivo '{csv_path}' não foi encontrado. Por favor, verifique o caminho e tente novamente.")
        return []
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo CSV com csv.DictReader na função ler_transacoes(): {e}")
        return []

from datetime import datetime

def validar_data(date):
    if not isinstance(date, str):
        return False, None, None
    try:
        dt_object = datetime.strptime(date, "%Y-%m-%d")
        mes_aaaa_mm = dt_object.strftime("%Y-%m")
        return True, dt_object, mes_aaaa_mm
    except ValueError:
        return False, None, None

def validar_valor(valor):
    if not isinstance(valor, str):
        return False, None
    try:
        valor_float = float(valor)
        if valor_float > 0:
            return True, valor_float
        else:
            return False, None # Valor deve ser maior que zero
    except ValueError:
        return False, None # Não é um número decimal válido

def validar_transacao(transacao_linha):
    erros = []
    transacao_limpa = {}

    # Validar 'id'
    transacao_id = transacao_linha.get('id')
    if not transacao_id or not transacao_id.isdigit():
        erros.append("ID da transação vazio ou não numérico.")
    else:
        transacao_limpa['id'] = int(transacao_id)

    # Validar 'cliente_id'
    cliente_id = transacao_linha.get('cliente_id')
    if not cliente_id:
        erros.append("cliente_id vazio.")
    else:
        transacao_limpa['cliente_id'] = cliente_id

    # Validar 'data'
    data_texto = transacao_linha.get('data')
    data_valida, data_objeto, mes_formatado = validar_data(data_texto)
    if not data_valida:
        erros.append("Data em formato inválido (deve ser AAAA-MM-DD).")
    else:
        transacao_limpa['data'] = data_objeto # Armazena como objeto datetime
        transacao_limpa['mes_ref'] = mes_formatado # Armazena o mês AAAA-MM

    # Validar 'tipo'
    tipo = transacao_linha.get('tipo')
    if tipo not in ['credito', 'debito']:
        erros.append("Tipo de transação inválido (deve ser 'credito' ou 'debito').")
    else:
        transacao_limpa['tipo'] = tipo

    # Validar 'valor'
    valor_texto = transacao_linha.get('valor')
    valor_valido, valor_numerico = validar_valor(valor_texto)
    if not valor_valido:
        erros.append("Valor não numérico ou menor ou igual a zero.")
    else:
        transacao_limpa['valor'] = valor_numerico

    transacao_limpa['descricao'] = transacao_linha.get('descricao', '')
    transacao_limpa['categoria'] = transacao_linha.get('categoria', '')

    if erros:
        # Se houver erros, retorna None e a lista de erros para debug
        transacao_linha['erros'] = erros
        transacao_linha['is_valida'] = False
        return transacao_linha

    transacao_limpa['is_valida'] = True
    return transacao_limpa
from collections import defaultdict

def _inicializar_dados_mes():
    return {
        'quantidade_transacoes': 0,
        'total_credito': 0.0,
        'total_debito': 0.0,
        'maior_valor': 0.0,
        'menor_valor': float('inf'),
        'valores_para_media': []
    }

def _processar_transacao_mensal(transacao, relatorio_mes_atual):
    valor = transacao['valor']
    tipo = transacao['tipo']

    relatorio_mes_atual['quantidade_transacoes'] += 1
    relatorio_mes_atual['valores_para_media'].append(valor)

    if tipo == 'credito':
        relatorio_mes_atual['total_credito'] += valor
    else:  # tipo == 'debito'
        relatorio_mes_atual['total_debito'] += valor

    relatorio_mes_atual['maior_valor'] = max(relatorio_mes_atual['maior_valor'], valor)
    relatorio_mes_atual['menor_valor'] = min(relatorio_mes_atual['menor_valor'], valor)

def _identificar_transacao_suspeita(transacao, transacoes_suspeitas):
    valor = transacao['valor']
    if valor > LIMITE_SUSPEITO:
        transacoes_suspeitas.append({
            'id': transacao['id'],
            'cliente_id': transacao['cliente_id'],
            'data': transacao['data'].strftime("%Y-%m-%d"),
            'valor': valor
        })

def _finalizar_calculos_mensais(relatorio_mensal):
    for mes, dados in relatorio_mensal.items():
        dados['saldo_mes'] = dados['total_credito'] - dados['total_debito']
        if dados['quantidade_transacoes'] > 0:
            dados['valor_medio'] = sum(dados['valores_para_media']) / dados['quantidade_transacoes']
        else:
            dados['valor_medio'] = 0.0
        del dados['valores_para_media']

def gerar_relatorio(transacoes):
    relatorio_mensal = {}
    transacoes_suspeitas = []

    for transacao in transacoes:
        mes_ref = transacao['mes_ref']

        if mes_ref not in relatorio_mensal:
            relatorio_mensal[mes_ref] = _inicializar_dados_mes()

        _processar_transacao_mensal(transacao, relatorio_mensal[mes_ref])
        _identificar_transacao_suspeita(transacao, transacoes_suspeitas)

    _finalizar_calculos_mensais(relatorio_mensal)

    return {'mensal': relatorio_mensal, 'suspeitas': transacoes_suspeitas}

def formatar_moeda_br(valor):
    return f"R$ {valor:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

def _gerar_titulo_secao(titulo):
    print(f"\n" + "=" * 20 + f" {titulo} " + "=" * 20 + "\n")

def exibir_relatorio(relatorios):
    _gerar_titulo_secao("RELATÓRIO MENSAL")
    if not relatorios['mensal']:
        print("Nenhum dado mensal disponível para o relatório.")
    else:
        for mes in sorted(relatorios['mensal'].keys()):
            dados = relatorios['mensal'][mes]
            print(f"Mês: {mes}")
            print(f"  Transações: {dados['quantidade_transacoes']}")
            print(f"  Total crédito: {formatar_moeda_br(dados['total_credito'])}")
            print(f"  Total débito:  {formatar_moeda_br(dados['total_debito'])}")
            print(f"  Saldo:         {formatar_moeda_br(dados['saldo_mes'])}")
            print(f"  Média:         {formatar_moeda_br(dados['valor_medio'])}")
            print(f"  Maior valor:   {formatar_moeda_br(dados['maior_valor'])}")
            print(f"  Menor valor:   {formatar_moeda_br(dados['menor_valor'])}")
            print() # Linha em branco para separar os meses

    _gerar_titulo_secao("TRANSAÇÕES SUSPEITAS")
    if not relatorios['suspeitas']:
        print("Nenhuma transação suspeita identificada.")
    else:
        for transacao in relatorios['suspeitas']:
            print(f"ID: {transacao['id']} | Cliente: {transacao['cliente_id']} | Data: {transacao['data']} | Valor: {formatar_moeda_br(transacao['valor'])}")
import json
from datetime import date

def salvar_json(summary_data, report_data, filename='relatorio.json'):
    output_data = {
        "gerado_em": date.today().strftime("%Y-%m-%d"),
        "total_transacoes_validas": summary_data['validas'],
        "total_transacoes_invalidas": summary_data['invalidas'],
        "resumo_mensal": {},
        "transacoes_suspeitas": []
    }

    for mes, dados_mes in report_data['mensal'].items():
        output_data["resumo_mensal"][mes] = {
            "quantidade": dados_mes['quantidade_transacoes'],
            "total_credito": round(dados_mes['total_credito'], 2),
            "total_debito": round(dados_mes['total_debito'], 2),
            "saldo": round(dados_mes['saldo_mes'], 2),
            "media": round(dados_mes['valor_medio'], 2),
            "maior_valor": round(dados_mes['maior_valor'], 2),
            "menor_valor": round(dados_mes['menor_valor'], 2)
        }

    for transacao_suspeita in report_data['suspeitas']:
        output_data["transacoes_suspeitas"].append({
            "id": transacao_suspeita['id'],
            "cliente_id": transacao_suspeita['cliente_id'],
            "data": transacao_suspeita['data'],
            "valor": round(transacao_suspeita['valor'], 2)
        })

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"Relatório salvo com sucesso em '{filename}'")
    except IOError as e:
        print(f"Erro ao salvar o relatório em '{filename}': {e}")
from tqdm.notebook import tqdm

setup()
csv_data = ler_transacoes(CSV_PATH)

transacoes = []
suspeitas = []
summary = {"lidas": 0, "invalidas": 0, "validas": 0}

# Adiciona a barra de progresso usando tqdm
for linha in tqdm(csv_data, desc="Processando transações"):
    summary['lidas'] += 1
    transacao_processada = validar_transacao(linha)

    if transacao_processada and transacao_processada.get('is_valida'):
        summary['validas'] += 1
        transacoes.append(transacao_processada)
    else:
        summary['invalidas'] += 1

# Resumo de limpeza e tratamento de dados
_gerar_titulo_secao("RESUMO DE LIMPEZA")
print(f"Total de linhas lidas: {summary['lidas']}")
print(f"Linhas válidas: {summary['validas']}")
print(f"Linhas inválidas: {summary['invalidas']}")

# Relatório
report = gerar_relatorio(transacoes)
exibir_relatorio(report)


# Salvar relatório em arquivo
print()
salvar_json(summary, report)
