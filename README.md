# Dashboard Compras Sem Disputa

Dashboard em Streamlit para analise de compras sem disputa dos dados da Lei 14133/23.

## Requisitos

- Python 3.12+

## Configuracao do ambiente

O projeto ja possui `.venv` criado na raiz.

Ative o ambiente virtual:

```bash
source .venv/bin/activate
```

Instale as dependencias:

```bash
pip install -r requirements.txt
```

## Executar o dashboard

```bash
streamlit run Dashboard.py
```

## Publicacao no Streamlit Cloud

O dashboard foi ajustado para usar por padrao o arquivo leve `dados/compras_sem_disputa(2).csv`, que e adequado para publicar online.

Se quiser apontar para outro arquivo local, defina a variavel `DASHBOARD_DATASET_PATH` antes de iniciar a app:

```bash
export DASHBOARD_DATASET_PATH=/caminho/para/seu/arquivo.csv
streamlit run Dashboard.py
```

Para subir no Streamlit Cloud, conecte o repositório no GitHub, selecione `Dashboard.py` como arquivo principal e mantenha `requirements.txt` na raiz.

## Estrutura principal

- `Dashboard.py`: aplicacao Streamlit
- `dados/compras_sem_disputa(2).csv`: base usada no dashboard por padrao
- `requirements.txt`: dependencias do projeto

## Funcionalidades

- Paginas: Visao Geral, Itens, Compradores e Dados Brutos
- Filtros por esfera e modalidade
- Opcao para manter apenas compra direta (Dispensa/Inexigibilidade)
- Paginacao dinamica de 20 itens e 20 UASG por pagina