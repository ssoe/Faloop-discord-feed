# Faloop-discord-feed
A Discord feed using webhooks from faloop.app

This is part of a larger project that I decided to make public. The larger project is currently private, where this is used as a backup S rank feed for my hunt discord HoneyHunts (light).

faloopApiLogin.py handles login and token logic. 

faloopSocketIO.py uses faloopAPiLogin to create a token for authing the socketio feed. Due to faloop limitations, you can only get S rank spawns from your own region. I am from Light and get from both Light and Chaos. Your mileage may vary.
.env-example has a link to the hunt dictionary I use. Edit as see you fit to your usecase.
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

Fork and PRs welcome.
