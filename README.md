NB : If your not using a bot container :
You will need to install python and git (must be 3.7+)
(https://www.youtube.com/watch?v=XF_rklW9XkU&ab_channel=CBTNuggets)

Also might need to install git if you get an error like this (https://i.imgur.com/1Cl6whB.png)
https://www.linode.com/docs/guides/how-to-install-git-on-linux-mac-and-windows/


1. Go to https://discord.com/developers/applications, create a new bot application

2. Create a bot & enable all intents -> https://imgur.com/sZtM5N3

3. Go to O2Auth - > URL Generator -> Select bot & invite the bot to your discord

4. Go back to the "Bot" page & grab the token, go to the config.json file and fill in everything except from your mongo url.

Example Config
```
{
  "Misc":{
    "Bot_Prefix":"!",
    "Bot_Token":"TOKENHERE", <- discord bot token
    "Server_Name":"Skizzy Rust",
    "Embed_Hex_Color":"#FFFFFF" <- hex code (https://htmlcolorcodes.com/)
  },
  "Mongo_Config":{ 
    "MONGO_URL": "" <- Mongo string
  },
  "Discord_Config":{
    "Guild_ID":822170791579877468, <- Guild id of the server you want to run the bot in
    "StaffRole_ID":895995833382748241 <- Staff role id of the role you want to be able to manage the bot
  }
}
```

5. Create an account @ https://www.mongodb.com/cloud/atlas/register

6. Create a "Shared" Free cluster & select a region close to where the bot will be hosted (not insanely important) https://imgur.com/undefined

7. Create a username and password - > Note the password down will be needed later, give permissions (Read and write to any database)

8. Go to "Network Access" & whitelist the ip of where the bot will be hosted from. https://imgur.com/ddG362e

8. Go to the Database page & click connect https://imgur.com/a/3rRV9ly
"Connect your application" then Driver : Python & 3.7 or later  https://imgur.com/undefined

9. Replace <db_username> with the username you created
10. Replace <db_password> with your password 
NB. Yes you must also remove the <> 

String should look something like this

mongodb+srv://alexskizzy:mypasswordhere@cluster0.randomidhere.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

11. Enter the entire string in the config.json file under "MONGO_URL"

12. If not being installed in a bot container you must install the required python packages run

pip install -r requirements.txt

In the console then run the main.py file

----

For a container double check your startup file is main.py not bot.py and ur requirements file is requirements.txt not something else.

Upon startup and the bot is alive use **{prefix}create** to make a new embed/server use **{prefix}help** for a list of commands

For any issues message me at alexskizzy(307862931213778946) or reach out to me via lone design / codefling tickets etc.

Suggested hosts -> https://serverstarter.host/ or anything offering a simple bot container - Python is key!
Support Discord -> https://discord.gg/G7BgXntn7S
# wipecountdownbot
