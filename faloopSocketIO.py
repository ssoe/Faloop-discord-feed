import socketio
from faloopApiLogin import getJWTsessionID, login
from dotenv import load_dotenv
import os
load_dotenv()
from discord import SyncWebhook
import discord
import requests
import sqlite3
import time
import json
import re

sio = socketio.Client(reconnection=True, reconnection_delay=5, reconnection_attempts=0)

username = os.getenv('FALOOP_USERNAME')
password = os.getenv('FALOOP_PASSWORD')
webhook_url = os.getenv('FALOOP_WEBHOOK')
faloopWebhook = SyncWebhook.from_url(webhook_url)

# Load local hunt dictionary
with open('huntDic.json', 'r', encoding='utf-8') as f:
    huntDic = json.load(f)

srank_role_id = os.getenv("SRANK_ROLE_ID")
csrank_role_id = os.getenv("CSRANK_ROLE_ID")
arr_srank = os.getenv("ARR_SRANK")
hw_srank = os.getenv("HW_SRANK")
sb_srank = os.getenv("SB_SRANK")
shb_srank = os.getenv("SHB_SRANK")
ew_srank = os.getenv("EW_SRANK")
c_arr_srank = os.getenv("C_ARR_SRANK")
c_hw_srank = os.getenv("C_HW_SRANK")
c_sb_srank = os.getenv("C_SB_SRNAK")
c_shb_srank = os.getenv("C_SHB_SRANK")
c_ew_srank = os.getenv("C_EW_SRANK")

mobs = huntDic['MobDictionary']
worlds = huntDic['EUWorldDictionary']
lightWorlds = huntDic['WorldDictionary']
chaosWorlds = huntDic['CWorldDictionary']
zones = huntDic['zoneDictionary']

def normalize_name(name):
    # Remove all non-alphanumeric characters and lowercase
    return re.sub(r'[^a-z0-9]', '', name.lower())

# Create reverse mapping for Zone Name -> ID 
# zones structure: {"134": ["Middle La Noscea"], ...}
zone_name_to_id = {}
for z_id, z_names in zones.items():
    if z_names:
        name = z_names[0]
        # Map normalized name "middlelanoscea" -> 134
        normalized_key = normalize_name(name)
        zone_name_to_id[normalized_key] = int(z_id)

# Create reverse mapping for Mob Name -> ID
# mobs structure: {"2957": ["Zona Seeker"], ...}
mob_name_to_id = {}
for m_id, m_names in mobs.items():
    if m_names:
        name = m_names[0]
        normalized_key = normalize_name(name)
        mob_name_to_id[normalized_key] = int(m_id)

ss = [8815, 8916, 10615, 10616] #to filter out SS ranks and minions
zoneIds = {} #dictionary for storing zone_id on spawn to use again on death because faloop doesnt send zone_id on death
arr = [134, 135, 137, 138, 139, 140, 141, 145, 146, 147, 148, 152, 153, 154, 155, 156, 180]
hw = [397, 198, 399, 400, 401, 402]
sb = [612, 613, 614, 620, 621, 622]
shb = [813, 814, 815, 816, 817, 818]
ew = [956, 957, 958, 959, 960, 961]
message_ids = {}

@sio.event
def connect():
    print("I'm connected!")

@sio.event
def connect_error(data):
    print("The connection failed!")

@sio.event
def disconnect():
    print("I'm disconnected!")

@sio.on('message')
def catch_all(data):
    filter_data(data)

def connectFaloopSocketio(session_id, jwt_token):
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://faloop.app/",
        "Origin": "https://faloop.app",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    }
    
    print(f"Connecting to SocketIO with Session ID: {session_id}")
    
    try:
        sio.connect(
            'https://faloop.app',
            socketio_path='/comms/socket.io',
            headers=headers,
            transports=['polling', 'websocket'],
            auth={'sessionid': session_id},
            wait=True
        )
    except Exception as e:
        print(f"SocketIO Connection Exception: {e}")
    
    sio.wait()

def filter_data(data): 
    # Filter out known noisy 'mob' reports to pinpoint relevant new events
    if not (data.get('type') == 'mob' and data.get('subType') == 'report'):
        print(f"DEBUG Event received: {data}")

    event_type = data.get('type')
    event_data = data.get('data', {})
    
    # Handle the nested 'id' object if present
    # Structure: data -> id -> {mobId, worldId}
    # WARNING: 'id' can also be an integer (event ID). Check type.
    nested_id = event_data.get('id')
    
    nested_mob = None
    nested_world = None
    if isinstance(nested_id, dict):
        nested_mob = nested_id.get('mobId')
        nested_world = nested_id.get('worldId')
    
    # Extract identifiers (Names)
    mob_name = nested_mob if nested_mob else (event_data.get('mobId2') or event_data.get('mobId'))
    world_name = nested_world if nested_world else (event_data.get('worldId2') or event_data.get('worldId'))
    
    # Validate Mob Name against Dictionary (if it's a string)
    if isinstance(mob_name, str):
        normalized_mob = normalize_name(mob_name)
        if normalized_mob not in mob_name_to_id:
            # Skip unknown mobs silently
            return
    
    # Extract Zone ID (string)
    # Handle cases where nested keys might not be dicts
    nested_inner_data = event_data.get('data')
    zone_name_string = None
    
    if isinstance(nested_inner_data, dict):
        zone_name_string = nested_inner_data.get('zoneId2')
    
    if not zone_name_string:
        zone_name_string = event_data.get('zoneId2')
    
    # Attempt to resolve Zone ID to integer
    zone_id = None
    if zone_name_string and isinstance(zone_name_string, str):
        normalized_name = normalize_name(zone_name_string)
        zone_id = zone_name_to_id.get(normalized_name)
    
    if zone_name_string and not zone_id:
        print(f"WARNING: Could not resolve Zone '{zone_name_string}' (normalized: '{normalize_name(str(zone_name_string))}') to ID.")

    # Fallback to old path if zone_id not found or field different
    if not zone_id and isinstance(nested_inner_data, dict):
        zone_id = nested_inner_data.get('zoneId')
        
    instance = event_data.get('zoneInstance')
    if instance is None:
        instance = 0

    # Filter out SS ranks and minions if mob_name is integer (legacy)
    if isinstance(mob_name, int) and mob_name in ss:
        return

    # Check if world_name is valid (int check)
    if isinstance(world_name, int) and str(world_name) not in worlds:
        return

    if event_type == 'mobworldspawn' or (event_type == 'mob' and event_data.get('action') == 'spawn'):
        pos_id = 0
        if 'data' in event_data and 'zonePoiIds' in event_data['data']:
             pois = event_data['data']['zonePoiIds']
             if pois:
                 pos_id = int(pois[0])

        if mob_name and world_name:
             # Pass zone_id (int) if resolved, else zone_name_string or whatever we found
             final_zone_id = zone_id if zone_id else (zone_name_string or 0)
             sendSpawn(data, mob_name, world_name, final_zone_id, pos_id, instance)

    elif event_type == 'mobworldkill' or (event_type == 'mob' and event_data.get('action') == 'death'):
        if mob_name and world_name:
            sendDeath(data, mob_name, world_name, instance)
    
def sendSpawn(data, mob_name, world_name, zone_id, pos_id, instance):
    # Handle string vs int IDs for display
    display_world = [world_name.replace('_', ' ').title()] if isinstance(world_name, str) else worlds.get(str(world_name), [str(world_name)])

    display_mob = [mob_name.replace('_', ' ').title()] if isinstance(mob_name, str) else mobs.get(str(mob_name), [str(mob_name)])
    
    display_zone = [zone_id.replace('_', ' ').title()] if isinstance(zone_id, str) else zones.get(str(zone_id), [str(zone_id)])

    # getCoords expects integer zone_id. If zone_id is a string, it will likely fail.
    # For now, we pass it as is, and getCoords will return None if it can't find it.
    coords = getCoords(pos_id, zone_id)
    timer = int(time.time())
    
    # Map Expansion roles (Legacy int logic skipped if string zone_id)
    srank_role = srank_role_id # Default
    srank_exp = arr_srank # Default to ARR if expansion cannot be determined

    # Only attempt expansion-specific role logic if zone_id is an integer
    if isinstance(zone_id, int):
        if str(world_name) in lightWorlds:
            srank_role = srank_role_id
            if zone_id in arr: srank_exp = arr_srank
            elif zone_id in hw: srank_exp = hw_srank
            elif zone_id in sb: srank_exp = sb_srank
            elif zone_id in shb: srank_exp = shb_srank
            elif zone_id in ew: srank_exp = ew_srank
        elif str(world_name) in chaosWorlds:
             srank_role = csrank_role_id
             if zone_id in arr: srank_exp = c_arr_srank
             elif zone_id in hw: srank_exp = c_hw_srank
             elif zone_id in sb: srank_exp = c_sb_srank
             elif zone_id in shb: srank_exp = c_shb_srank
             elif zone_id in ew: srank_exp = c_ew_srank  
            
    # If we have coords (which needs int pos_id and zone_id for lookup), use them. Else default to 0,0
    x, y = "0", "0"
    if coords:
        x, y = [value.strip() for value in coords.split(',')]
    
    # mapurl expects integer zoneid. If zone_id is a string, this URL might be invalid.
    mapurl = f"https://api.ffxivsonar.com/render/map?zoneid={zone_id}&flagx={x}&flagy={y}"
    contentstring = f"<@&{srank_role}> <@&{srank_exp}> on **[{display_world[0]}]** - **{display_mob[0]}** in instance: {instance}, spawned <t:{timer}:R>"
    
    # Key for dicts using new IDs (can be strings or ints)
    zoneIds[(mob_name, world_name, instance)] = zone_id
    
    embed=discord.Embed(title=f"{display_world[0]}  - {display_mob[0]} - x {x} y {y}", color=0xe1e100)
    embed.add_field(name="Zone: ", value=f"{display_zone[0]}", inline=False)
    embed.add_field(name="Teleporter: ", value=f"/ctp {x} {y} : {display_zone[0]}", inline=False)
    embed.set_image(url=mapurl)
    try:
        message = faloopWebhook.send(embed=embed, wait=True, content=contentstring)
        message_ids[(mob_name, world_name, instance)] = (message.id, timer, x, y)
    except Exception as e:
        print(f"Webhook send failed: {e}")

def sendDeath(data, mob_name, world_name, instance):
    # Check if the spawn message was successfully sent and stored
    if (mob_name, world_name, instance) not in message_ids:
        print(f"No message ID found for {mob_name} on {world_name} instance {instance}. Cannot edit message.")
        return

    # Retrieve stored zone_id, message_id, timer, x, y from spawn event
    zone_id = zoneIds.get((mob_name, world_name, instance))
    if zone_id is None:
        print(f"No zone_id found for {mob_name} on {world_name} instance {instance}. Cannot process death.")
        return

    message_id, timer, x, y = message_ids[(mob_name, world_name, instance)]
    
    # Handle string vs int names for display
    display_zone = [zone_id.replace('_', ' ').title()] if isinstance(zone_id, str) else zones.get(str(zone_id), [str(zone_id)])

    display_world = [world_name.replace('_', ' ').title()] if isinstance(world_name, str) else worlds.get(str(world_name), [str(world_name)])

    display_mob = [mob_name.replace('_', ' ').title()] if isinstance(mob_name, str) else mobs.get(str(mob_name), [str(mob_name)])
        
    # Role mentions for the strikethrough message (defaulting as expansion cannot be determined from string zone_id)
    srank_role = srank_role_id
    srank_exp = arr_srank # Default to ARR if expansion cannot be determined
    
    # Only attempt expansion-specific role logic if zone_id is an integer
    if isinstance(zone_id, int):
        if str(world_name) in lightWorlds:
            srank_role = srank_role_id
            if zone_id in arr: srank_exp = arr_srank
            elif zone_id in hw: srank_exp = hw_srank
            elif zone_id in sb: srank_exp = sb_srank
            elif zone_id in shb: srank_exp = shb_srank
            elif zone_id in ew: srank_exp = ew_srank
        elif str(world_name) in chaosWorlds:
             srank_role = csrank_role_id
             if zone_id in arr: srank_exp = c_arr_srank
             elif zone_id in hw: srank_exp = c_hw_srank
             elif zone_id in sb: srank_exp = c_sb_srank
             elif zone_id in shb: srank_exp = c_shb_srank
             elif zone_id in ew: srank_exp = c_ew_srank

    embeddead=discord.Embed(title=f"~~{display_world[0]}  - {display_mob[0]} - x {x} y {y}~~", color=0xb83535)
    embeddead.add_field(name="~~Zone: ~~", value=f"~~{display_zone[0]}~~", inline=False)
    embeddead.add_field(name="~~Teleporter: ~~", value=f"~~/ctp {x} {y} : {display_zone[0]}~~", inline=False)           
    editcontentstring = f"~~<@&{srank_role}> <@&{srank_exp}> on **[{display_world[0]}]** - **{display_mob[0]}** spawned <t:{timer}:R>~~ **Killed**"
    
    try:
        faloopWebhook.edit_message(message_id, embed=embeddead, content=editcontentstring)
    except Exception as e:
        print(f"Webhook edit failed: {e}")
    
    sRankDead = f"Srank {display_mob[0]} on {display_world[0]} in instance: {instance} died"
    faloopWebhook.send(sRankDead)


    rawX = 0 # Default if x is "0" or cannot be parsed
    rawY = 0
    if x != "0": 
         try:
            rawX = ((float(x) - 1) / 41) * 2048 - 1024
            rawY = ((float(y) - 1) / 41) * 2048 - 1024
         except ValueError:
            print(f"Could not parse coordinates x={x}, y={y} for rawX/rawY calculation.")

    deathtimer = str(int(time.time()))

    # Clean up stored data
    if (mob_name, world_name, instance) in zoneIds:
        del zoneIds[(mob_name, world_name, instance)]    
    if (mob_name, world_name, instance) in message_ids:
        del message_ids[(mob_name, world_name, instance)]
    
def getCoords(pos_id, zone_id):
    # This function expects zone_id to be an integer for DB lookup.
    # If zone_id is a string, this query will likely fail or return no results.
    if not isinstance(zone_id, int):
        print(f"Warning: getCoords received non-integer zone_id: {zone_id}. Skipping DB lookup.")
        return None
    try:
        with sqlite3.connect('hunts.db') as conn:
            cursor = conn.cursor()
            query = "SELECT coords FROM zone_positions WHERE posId = ? AND zoneId = ?"
            cursor.execute(query, (pos_id, zone_id))
            result = cursor.fetchone()
            return result[0] if result else None
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

try:
    with requests.Session() as session:
        responseJWTsessionID = getJWTsessionID(session)
        
        # The API returns {"success": true, "data": {...}}
        response_data = responseJWTsessionID.get("data", {})
        
        session_id = response_data.get("sessionId")
        jwt_token = response_data.get("token")
        
        if not session_id or not jwt_token:
            print("Error: Could not retrieve session ID or token from refresh response.")
            print(f"Full response: {responseJWTsessionID}")
        else:
            login_response = login(session, session_id, jwt_token, username, password)
            print("Login successful.")
            
            connectFaloopSocketio(session_id, jwt_token)
except Exception as e:
    print(f"Main loop exception: {e}")
