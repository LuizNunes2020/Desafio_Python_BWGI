import io
import os
import tempfile

def last_lines(filename, buffer_size=io.DEFAULT_BUFFER_SIZE):
    """
    Gera linhas de um arquivo em ordem reversa, como o comando 'tac' no Unix.
    Suporta arquivos grandes e codificação UTF-8.
    """
    with open(filename, 'rb') as f:
        # Vai para o final do arquivo
        f.seek(0, os.SEEK_END)
        file_size = remaining = f.tell()  # Tamanho total do arquivo em bytes
        carry = b''  # Acumula dados incompletos de linha ou caracteres

        # Lê o arquivo de trás para frente em blocos
        while remaining > 0:
            read_size = min(buffer_size, remaining)  # Tamanho do bloco atual
            remaining -= read_size
            f.seek(remaining)  # Move o ponteiro para trás
            chunk = f.read(read_size)  # Lê o bloco
            full_chunk = chunk + carry  # Adiciona o que sobrou do bloco anterior

            try:
                # Tenta decodificar todo o bloco como UTF-8
                decoded = full_chunk.decode('utf-8')
            except UnicodeDecodeError:
                # Se falhar, guarda o bloco para tentar novamente com mais dados
                carry = full_chunk
                continue

            # Divide em linhas mantendo os terminadores (\n, \r\n, \r)
            lines = decoded.splitlines(keepends=True)

            # Mantém linhas vazias reais (que terminam com \n ou \r)
            lines = [line for line in lines if line.endswith(('\n', '\r')) or line.strip()]

            # Se a primeira linha do chunk foi cortada no meio (sem \n ou \r)
            if lines and not lines[0].endswith(('\n', '\r')):
                carry = lines[0].encode('utf-8')  # Salva para juntar com o próximo bloco
                lines = lines[1:]  # Remove essa linha da lista atual
            else:
                carry = b''  # Nada a carregar

            # Processa as linhas em ordem reversa
            for line in reversed(lines):
                # Normaliza terminadores de linha para '\n'
                if line.endswith('\r\n'):
                    line = line[:-2] + '\n'
                elif line.endswith('\r'):
                    line = line[:-1] + '\n'

                # Garante que todas as linhas terminem com '\n'
                if not line.endswith('\n'):
                    line += '\n'

                yield line  # Devolve a linha

        # Processa o que sobrou no carry após o loop
        if carry:
            try:
                line = carry.decode('utf-8')
                # Normaliza quebras de linha
                line = line.replace('\r\n', '\n').replace('\r', '\n')
                if not line.endswith('\n'):
                    line += '\n'
                yield line
            except UnicodeDecodeError:
                pass  # Se não puder decodificar, ignora

# Bloco de teste simples que imprime as linhas de um arquivo ao contrário
if __name__ == "__main__":
    for line in last_lines("my_file.txt"):
        print(line, end='')