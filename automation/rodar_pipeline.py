"""
Roda o pipeline completo em sequência: atualiza o banco, recalcula reposição,
exporta os dados pro Power BI e gera o resumo do dia.

Uso manual:
    python rodar_pipeline.py

Pra automatizar de verdade (rodar sozinho todo dia), agende esse script:
  - Windows: Agendador de Tarefas (Task Scheduler) -> nova tarefa básica ->
    ação "Iniciar um programa" -> aponte pro python.exe e pro caminho deste arquivo.
  - Linux/Mac: crontab -e e adicione uma linha como
    0 8 * * * /usr/bin/python3 /caminho/completo/rodar_pipeline.py
    (roda todo dia às 8h)
"""

import subprocess
import sys
from datetime import datetime

PASSOS = [
    ("Recalculando reposição e exportando dados", ["python", "../analytics/reposicao.py"]),
    ("Gerando resumo executivo", ["python", "../ai/assistente.py"]),
]


def main():
    print(f"=== Pipeline iniciado em {datetime.now().strftime('%d/%m/%Y %H:%M')} ===")
    for descricao, comando in PASSOS:
        print(f"\n> {descricao}")
        resultado = subprocess.run(comando, capture_output=True, text=True)
        print(resultado.stdout)
        if resultado.returncode != 0:
            print(f"Erro em '{descricao}':\n{resultado.stderr}", file=sys.stderr)
            sys.exit(1)
    print("\n=== Pipeline concluído ===")


if __name__ == "__main__":
    main()
