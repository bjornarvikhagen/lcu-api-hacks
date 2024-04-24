from lcu_driver import Connector
import threading
import asyncio

connector = Connector()


async def get_summoner_data(connection):
    data = await connection.request('GET', '/lol-summoner/v1/current-summoner')
    summoner = await data.json()
    print(f"displayName:    {summoner['displayName']}")
    print(f"summonerId:     {summoner['summonerId']}")
    print(f"puuid:          {summoner['puuid']}")
    print("-")
    return summoner['summonerId'] 

async def create_custom_lobby(connection):
  custom = {
    'customGameLobby': {
      'configuration': {
        'gameMode': 'PRACTICETOOL',
        'gameMutator': '',
        'gameServerRegion': '',
        'mapId': 11,
        'mutators': {'id': 1},
        'spectatorPolicy': 'AllAllowed',
        'teamSize': 5
      },
      'lobbyName': 'PRACTICETOOL',
      'lobbyPassword': ''
    },
    'isCustom': True
  }
  await connection.request('POST', '/lol-lobby/v2/lobby', data=custom)

async def add_bots_team1(connection):
    team1_bots = [
        {'championId': 16, 'botDifficulty': 'EASY', 'teamId': '100'},  # Soraka
        {'championId': 86, 'botDifficulty': 'EASY', 'teamId': '100'},  # Garen
        {'championId': 12, 'botDifficulty': 'EASY', 'teamId': '100'},  # Alistar
        {'championId': 99, 'botDifficulty': 'EASY', 'teamId': '100'}   # Lux
    ]
    for bot in team1_bots:
        await connection.request('POST', '/lol-lobby/v1/lobby/custom/bots', data=bot)

async def add_bots_team2(connection):
    team2_bots = [
        {'championId': 16, 'botDifficulty': 'EASY', 'teamId': '200'},  # Soraka
        {'championId': 86, 'botDifficulty': 'EASY', 'teamId': '200'},  # Garen
        {'championId': 12, 'botDifficulty': 'EASY', 'teamId': '200'},
        {'championId': 122, 'botDifficulty': 'EASY', 'teamId': '200'},  # Alistar
        {'championId': 99, 'botDifficulty': 'EASY', 'teamId': '200'}   # Lux
    ]
    for bot in team2_bots:
        await connection.request('POST', '/lol-lobby/v1/lobby/custom/bots', data=bot)

async def launch_game(connection):

    await connection.request('POST', '/lol-lobby/v1/lobby/custom/start-champ-select', data={})
    
async def get_champion_select_session(connection):
    try:
        response = await connection.request('GET', '/lol-champ-select/v1/session')
        if response.status == 200:
            session_data = await response.json()
            return session_data
        else:
            print(f"Failed to fetch champion select session: {await response.text()}")
            return None
    except Exception as e:
        print(f"An error occurred while fetching champion select session: {str(e)}")
        return None
    
async def display_available_actions(connection):
    session_data = await get_champion_select_session(connection)
    if session_data:
        actions = session_data.get('actions', [])
        for round_actions in actions: 
            for action in round_actions:
                print(f"Action ID: {action['id']}, Type: {action['type']}, Champion ID: {action.get('championId', 'None')}, Completed: {action['completed']}")

async def pick_champion(connection, actionIndex, championId):
    try:
        # Pick a champion using the correct action index and champion ID
        pick_response = await connection.request('PATCH', f'/lol-champ-select/v1/session/actions/{actionIndex}', json={'championId': championId})
        if pick_response.status != 200:
            print(f"Failed to pick champion: {await pick_response.text()}")
            return

    except Exception as e:
        print(f"An error occurred: {str(e)}")

async def lock_champion(connection, actionId):
    try:
        # Lock in the champion using the same action index
        lock_response = await connection.request('POST', f'/lol-champ-select/v1/session/actions/{actionId}/complete', json={})
        if lock_response.status != 200:
            print(f"Failed to lock champion: {await lock_response.text()}")
            return
        print("Champion locked successfully.")
    except Exception as e:
        print(f"An error occurred while locking the champion: {str(e)}")

#todo:
# retrieve game version: GET https://127.0.0.1/lol-patch/v1/game-version

# Quit your current gameflow
# Get these values through LCU requests:
# Game version
# RSO Inventory JWT
# RSO Id token
# RSO Access token
# League Session token
# Generate custom lobby based on your gotten values
# Send custom lobby to the client
# Start champion selection stage in this custom lobby
# Wait some time (12-15 seconds is enough I guess)
# Again, quit your current gameflow
# Send setClientReceivedGameMessage LCDS request to gameService destination
@connector.ready
async def connect(connection):
    championId = 1
    summonerId = await get_summoner_data(connection)
    actionId = 10
    await create_custom_lobby(connection)
    await add_bots_team1(connection)
    await add_bots_team2(connection)
    await asyncio.sleep(8)
    await launch_game(connection)
    await asyncio.sleep(8)
    await display_available_actions(connection)
    await pick_champion(connection, actionIndex=10, championId=1)
    await asyncio.sleep(5)
    await lock_champion(connection, actionId)

connector.start()