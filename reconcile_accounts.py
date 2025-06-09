import csv
from pathlib import Path
from pprint import pprint
from datetime import datetime
from collections import defaultdict

# -------------------------
# Funções auxiliares
# -------------------------

def parse_date(date_str):
    """
    Tenta converter uma string no formato 'YYYY-MM-DD' em um objeto de data.
    Retorna None se a data for inválida ou malformada.
    """
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def normalize_row(row):
    """
    Normaliza uma linha de entrada para garantir que:
    - Tenha exatamente 4 colunas.
    - Espaços em branco sejam removidos.
    - None seja substituído por string vazia.
    """
    if not isinstance(row, (list, tuple)):
        row = []
    padded_row = (list(row) + [""] * 4)[:4]
    return tuple(str(cell).strip() if cell is not None else "" for cell in padded_row)


# -------------------------
# Função principal de conciliação
# -------------------------

def reconcile_accounts(transactions_a, transactions_b):
    """
    Compara duas listas de transações financeiras.
    Cada transação tem: [data, departamento, valor, beneficiário].
    Retorna duas listas com o campo extra 'FOUND' ou 'MISSING', indicando se foi conciliada.
    """

    # Pré-processamento: normaliza as linhas e adiciona metadados
    processed_a = [{'original_row': list(normalize_row(row)), 'status': 'MISSING', 'matched': False}
                   for row in transactions_a]
    processed_b = [{'original_row': list(normalize_row(row)), 'status': 'MISSING', 'matched': False}
                   for row in transactions_b]

    # Função que cria uma chave de indexação com base em (departamento, valor normalizado, beneficiário)
    def create_index_key(row):
        try:
            normalized_value_str = f"{float(row[2]):.6f}"  # padroniza valor float com 6 casas decimais
        except ValueError:
            normalized_value_str = row[2]
        return (
            row[1].lower(),
            normalized_value_str,
            row[3].lower()
        )

    # Criação dos índices ordenados por data para busca eficiente
    indexed_b = defaultdict(list)
    for idx, entry_b in enumerate(processed_b):
        row_b = entry_b['original_row']
        date_b = parse_date(row_b[0])
        if date_b is not None:
            key = create_index_key(row_b)
            indexed_b[key].append((date_b, idx))
    for key in indexed_b:
        indexed_b[key].sort(key=lambda x: x[0])

    indexed_a = defaultdict(list)
    for idx, entry_a in enumerate(processed_a):
        row_a = entry_a['original_row']
        date_a = parse_date(row_a[0])
        if date_a is not None:
            key = create_index_key(row_a)
            indexed_a[key].append((date_a, idx))
    for key in indexed_a:
        indexed_a[key].sort(key=lambda x: x[0])

    # Função que busca e marca a melhor correspondência de acordo com os critérios
    def find_and_mark(source_entry, target_indexed_data, target_processed_list):
        source_row = source_entry['original_row']
        source_date = parse_date(source_row[0])
        if source_date is None:
            return 'MISSING'

        key = create_index_key(source_row)
        if key not in target_indexed_data:
            return 'MISSING'

        for target_date, target_idx in target_indexed_data[key]:
            if not target_processed_list[target_idx]['matched']:
                date_diff = abs((source_date - target_date).days)
                if date_diff <= 1:  # permite diferença de até 1 dia
                    source_entry['status'] = 'FOUND'
                    source_entry['matched'] = True
                    target_processed_list[target_idx]['status'] = 'FOUND'
                    target_processed_list[target_idx]['matched'] = True
                    return 'FOUND'
        return 'MISSING'

    # 1ª Passagem: tenta casar cada transação de A com B
    for a_entry in processed_a:
        if not a_entry['matched']:
            find_and_mark(a_entry, indexed_b, processed_b)

    # 2ª Passagem: tenta casar cada transação de B com A
    for b_entry in processed_b:
        if not b_entry['matched']:
            find_and_mark(b_entry, indexed_a, processed_a)

    # Geração do resultado final com a coluna de status
    result_a = [entry['original_row'] + [entry['status']] for entry in processed_a]
    result_b = [entry['original_row'] + [entry['status']] for entry in processed_b]

    return result_a, result_b


# -------------------------
# Leitura dos arquivos CSV
# -------------------------

def read_csv_file(file_path):
    """
    Lê um arquivo CSV ignorando:
    - Linhas em branco
    - Linhas iniciadas com '#'
    - Erros de codificação leve
    """
    rows = []
    try:
        with file_path.open(encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip().startswith('#'):
                    continue
                normalized = normalize_row(row)
                if all(cell == "" for cell in normalized):
                    continue
                rows.append(normalized)
    except (IOError, csv.Error) as e:
        print(f"Erro ao ler o arquivo CSV {file_path}: {e}")
        return []
    return rows


# -------------------------
# Execução principal
# -------------------------

if __name__ == "__main__":
    path1 = Path("transactions1.csv")
    path2 = Path("transactions2.csv")

    transactions1 = read_csv_file(path1)
    transactions2 = read_csv_file(path2)

    out1, out2 = reconcile_accounts(transactions1, transactions2)

    print("Resultado para transactions1:")
    pprint(out1)

    print("\nResultado para transactions2:")
    pprint(out2)