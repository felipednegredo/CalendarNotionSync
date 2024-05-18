
# Integração Notion-Google Calendar para Gerenciamento de Eventos

Este projeto visa criar uma integração entre o Notion e o Google Calendar para facilitar o gerenciamento de projetos. A ideia é sincronizar informações relevantes de um banco de dados no Notion com eventos no Google Calendar.

## Algumas das funcionalidades do projeto

- Autenticação com o Google Calendar usando OAuth 2.0
- Integração entre as APIs do Notion e do Google Calendar
- Leitura dos dados de um banco de dados específico no Notion usando a API.

## Rodando localmente

Clone o projeto

```bash
 git clone https://github.com/felipednegredo/CalendarNotionSync.git
```

Entre no diretório do projeto

```bash
 cd CalendarNotionSync
```

Instale as dependências

```bash
 pip install -r requirements.txt
```

Rodando o projeto

```bash
 python main.py
```

## Variáveis de Ambiente

Para rodar esse projeto, você vai precisar adicionar as seguintes variáveis de ambiente, podendo fazer via terminal.

`SET NOTION_TOKEN = 'NOTION_TOKEN'`

`SET NOTION_DATABASE_ID = 'NOTION_DATABASE_ID'`

## Licença
[![AGPL v3](https://img.shields.io/badge/License-AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)



