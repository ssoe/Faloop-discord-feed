# Faloop-discord-feed

A Discord feed using webhooks from faloop.app

This is part of a larger project that I decided to make public. The larger project is called Honeyhunts, where this is used as a backup S rank feed for my hunt discord.
Hunts.db is a snapshop of database from larger project. It uses zone_positions table to map internal faloop positions (zonePoiIds) to X/Y coords as the faloop feed does not have X/Y coords.

I also included a standalone faloop db with this table.

Example spawn event:

{"type":"mob","subType":"report","data":{"action":"spawn","id":{"mobId":"zona_seeker","worldId":"shiva"},"data":{"zoneId2":"western_thanalan","zonePoiIds":[162],"timestamp":"2025-12-29T14:34:23.353Z","window":1,"stage":null}}}

Example death event:

{"type":"mobworldkill","subType":"recentAdd","data":{"id":2102789,"mobId2":"thousand_cast_theda","worldId2":"phoenix","zoneInstance":null,"spawnedAt":"2025-12-29T13:31:18.078Z","killedAt":"2025-12-29T13:35:25.081Z","zoneId2":"north_shroud","isFailed":false}}

faloopApiLogin.py handles login and token logic.

faloopSocketIO.py uses faloopAPiLogin to create a token for authing the socketio feed. Due to faloop limitations, you can only get S rank spawns from your own region. I am from Light and get from both Light and Chaos. Your mileage may vary.
The bot will ping different roles, change these to fit your server.
If you dont want to have pings based on expansion, remove

        if zone_id in arr:
            srank_exp = arr_srank
        elif zone_id in hw:
            srank_exp = hw_srank
        elif zone_id in sb:
            srank_exp = sb_srank
        elif zone_id in shb:
            srank_exp = shb_srank
        elif zone_id in ew:
            srank_exp = ew_srank

and <@&{srank_exp}> from content strings.
