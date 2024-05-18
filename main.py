import json
import os
import pickle

# Importando módulos necessários para fazer requisições HTTP e manipular datas
import requests
from dateutil.parser import parse
from google.auth.exceptions import RefreshError

# Importando módulos para autenticação e interação com APIs do Google
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# Função para ler as credenciais armazenadas num arquivo JSON para uso com a API do Notion
def ler_notion_secrets():
    # Extrai o token, o ID do banco de dados e os cabeçalhos necessários para as requisições
    TOKEN = os.getenv('NOTION_TOKEN')
    DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
    HEADERS = {
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2021-05-13"
    }
    # Retorna as credenciais extraídas
    return TOKEN, DATABASE_ID, HEADERS


# Função para ler dados de um banco de dados do Notion usando a API
def ler_database_notion(database_id, headers):
    # Constrói a URL para a requisição da API
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    # Faz uma requisição POST para a API do Notion e armazena a resposta
    response = requests.post(url, headers=headers)
    # Se a resposta não for bem-sucedida, levanta uma exceção
    if response.status_code != 200:
        raise Exception(f"Erro ao consultar a base de dados do Notion: {response.status_code}")
    # Retorna os dados da resposta em formato JSON
    return response.json()


# Função para adicionar itens de um JSON do Notion numa lista existente
def adicionar_em_lista(database_json, lista_existente):
    # Itera sobre cada página de resultados do JSON do Notion
    for page in database_json['results']:
        properties = {}
        # Gera um link direto para a página no Notion
        page_id = page.get("id")
        properties['link'] = f"https://www.notion.so/{page_id.replace('-', '')}"
        # Extrai propriedades específicas das páginas
        for key, value in page['properties'].items():
            # Extrai o nome, status e outras propriedades relevantes
            if 'title' in value:
                properties['Name'] = value['title'][0]['text']['content']
            elif 'select' in value and value['select']:
                properties['Status'] = value['select']['name']
            elif 'multi_select' in value:
                properties[key] = [option['name'] for option in value['multi_select']]
            elif 'date' in value and value['date']:
                properties['Data inicial'] = value['date']['start']

        # Define o status como 'Não Iniciado' se não estiver definido
        if properties.get('Status') is None:
            properties['Status'] = 'Não Iniciado'

        # Adiciona a propriedade à lista se o status não for 'Completo' e não estiver na lista existente
        if properties.get('Status') != 'Completo' and not any(
                event['Name'] == properties['Name'] and
                ('Data inicial' in event and event['Data inicial'] == properties['Data inicial']) and
                event['Status'] == properties['Status'] for event in lista_existente):
            lista_existente.append(properties)
    # Retorna a lista atualizada
    return lista_existente


# Função para verificar se um evento já existe no Google Calendar
def event_exists(service, calendar_id, event_to_check):
    # Obtém a lista de eventos do calendário
    events_result = service.events().list(calendarId=calendar_id, singleEvents=True).execute()
    events = events_result.get('items', [])
    # Verifica se o evento já existe comparando o resumo e a data de início
    for event in events:
        if 'dateTime' in event['start'] and 'dateTime' in event_to_check['start']:
            if event['summary'] == event_to_check['summary'] and event['start']['dateTime'] == event_to_check['start'][
                'dateTime']:
                return True
    # Retorna False se o evento não existir
    return False


# Função para deletar eventos duplicados no Google Calendar
def deleta_eventos_repetidos(service, calendar_id, title):
    # Obtém a lista de eventos do calendário
    events_result = service.events().list(calendarId=calendar_id, singleEvents=True).execute()
    events = events_result.get('items', [])
    # Deleta eventos que têm o mesmo título
    for event in events:
        if event['summary'] == title:
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            print(f"Deleted event: {title}")


# Função para adicionar eventos ao Google Calendar
def adiciona_eventos_calendarios(service, calendar_id, lista_de_itens):
    # Itera sobre a lista de itens para adicionar como eventos
    for item in lista_de_itens:
        if 'Data inicial' in item:
            # Cria um dicionário representando o evento
            event = {
                'summary': item.get('Name'),
                'description': item.get('link') + f"\n\n{item.get('Status')}",
                'start': {
                    'dateTime': (parse(item.get('Data inicial')).replace(hour=19)).isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': (parse(item.get('Data inicial')).replace(hour=22, minute=30)).isoformat(),
                    'timeZone': 'America/Sao_Paulo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},
                    ],
                },
            }

            # Deleta eventos repetidos antes de adicionar um novo
            deleta_eventos_repetidos(service, calendar_id, item.get('Name'))

            # Insere o novo evento no calendário
            event = service.events().insert(calendarId=calendar_id, body=event).execute()
            print('Evento adicionado no calendário: %s' % (event.get('htmlLink')))


# Ponto de entrada principal do script
if __name__ == "__main__":
    # Define os escopos necessários para a autenticação com a API do Google Calendar
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    # Verifica se o arquivo token.“pickle” existe, que armazena as credenciais do usuário
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # Se não houver credenciais válidas, solicita que o usuário faça “login”
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                creds = None
        if not creds:
            client_secrets_path = "client_secrets.json"
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_path,
                SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

    # Constrói o serviço do Google Calendar com as credenciais autenticadas
    service = build('calendar', 'v3', credentials=creds)
    # Utiliza as funções definidas anteriormente para interagir com o Notion e o Google Calendar
    TOKEN, DATABASE_ID, HEADERS = ler_notion_secrets()
    print(os.getenv('NOTION_TOKEN'))
    database_json = ler_database_notion(DATABASE_ID, HEADERS)
    lista_de_itens = adicionar_em_lista(database_json, lista_existente=[])
    print(lista_de_itens)
    adiciona_eventos_calendarios(service, 'primary', lista_de_itens)
