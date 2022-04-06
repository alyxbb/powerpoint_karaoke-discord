import os
import random
import re
import sqlite3

import discord
from discord import app_commands

import web

client = discord.Client()
conn = sqlite3.connect('identifier.sqlite')
cur = conn.cursor()


@client.event
async def on_ready():
    commandTree = discord.app_commands.CommandTree(client)
    commandTree.add_command(add_powerpoint)
    commandTree.add_command(get_powerpoint)
    commandTree.add_command(my_powerpoints)
    commandTree.add_command(remaing_ppts)
    commandTree.add_command(delete_powerpoint)
    commandTree.add_command(refresh_powerpoints)
    commandTree.add_command(list_all_ppts)
    commandTree.add_command(admin_delete_powerpoint)
    commandTree.add_command(test_powerpoints)
    await commandTree.sync()
    print("bot online")


@app_commands.command(name="test_ppts", description="same as /get_ppt but gives you a dummy link so you can test")
async def test_powerpoints(interaction: discord.Interaction):
    url = "http://127.0.0.1:5000/checkpoint/?link=" + "https://google.com+&username=" + interaction.user.name
    await interaction.response.send_message(
        "please click here to view the powerpoint: " + url + "\n created by " + "tester mc test face")


@app_commands.command(name="admin_list_ppts", description="lists all powerpoints")
async def list_all_ppts(interaction: discord.Interaction):
    if interaction.channel.permissions_for(
            interaction.user).administrator or interaction.user.id == "407294176158547980":

        cur.execute("SELECT Link,user_id FROM powerpoints WHERE  guild_id=? ORDER BY Link", (interaction.guild_id,))
        links = cur.fetchall()
        if len(links) == 0:
            await interaction.response.send_message("you have no powerpoints")
        else:
            linkstr = ""
            for count, link in enumerate(links):
                uname = await client.fetch_user(link[1])
                linkstr += str(count) + ". " + link[0] + " by " + uname.name + "\n"
            await interaction.response.send_message(f"there are {str(len(links))} powerpoints\n{linkstr}")
    else:
        await interaction.response.send_message("you are not an admin")


@app_commands.command(name="admin_delete_ppt", description="deletes a powerpoint you dont own")
@app_commands.describe(number="the number of the powerpoint to delete as returned by /admin_list_ppts")
async def admin_delete_powerpoint(interaction: discord.Interaction, number: int):
    if interaction.channel.permissions_for(
            interaction.user).administrator or interaction.user.id == "407294176158547980":

        cur.execute("SELECT Link,guild_id FROM powerpoints WHERE guild_id=? ORDER BY Link", (interaction.guild_id,))
        links = cur.fetchall()
        if len(links) == 0:
            await interaction.response.send_message("no powerpoints found in this server")

        else:
            if number >= len(links):
                await interaction.response.send_message("invalid number")
            elif number < 0:
                await interaction.response.send_message("invalid number")
            else:
                link = links[number]
                cur.execute("DELETE FROM powerpoints WHERE Link=? and guild_id=?", (link[0], link[1]))
                conn.commit()
                await interaction.response.send_message("powerpoint deleted")
    else:
        await interaction.response.send_message("you are not an admin")


@app_commands.command(name="refresh_ppts", description="resets the powerpoints you have used")
@app_commands.checks.has_permissions(administrator=True)
async def refresh_powerpoints(interaction: discord.Interaction):
    if interaction.channel.permissions_for(
            interaction.user).administrator or interaction.user.id == "407294176158547980":
        cur.execute("UPDATE powerpoints SET used=0 WHERE guild_id=?", (interaction.guild_id,))
        conn.commit()
        await interaction.response.send_message("powerpoints refreshed")
    else:
        await interaction.response.send_message("you are not an admin")


@app_commands.command(name="delete_ppt", description="deletes a powerpoint")
@app_commands.describe(number="the number of the powerpoint to delete as returned by /my_ppts")
async def delete_powerpoint(interaction: discord.Interaction, number: int):
    cur.execute("SELECT Link,guild_id FROM powerpoints WHERE user_id=? and guild_id=? ORDER BY Link",
                (interaction.user.id, interaction.guild_id))
    links = cur.fetchall()
    if len(links) == 0:
        await interaction.response.send_message("you have no powerpoints")

    else:
        if number >= len(links):
            await interaction.response.send_message("invalid number")
        elif number < 0:
            await interaction.response.send_message("invalid number")
        else:
            link = links[number]
            cur.execute("DELETE FROM powerpoints WHERE Link=? and guild_id=?", (link[0], link[1]))
            conn.commit()
            await interaction.response.send_message("powerpoint deleted")


@app_commands.command(name="add_ppt", description="adds a powerpoint to the game with given link")
@app_commands.describe(allowself="whether you can be required to present this powerpoint, default is false")
@app_commands.describe(link="the link to the powerpoint")
@app_commands.describe(creator="the creator of the powerpoint, default is you")
async def add_powerpoint(interaction: discord.Interaction, link: str, allowself: bool = False,
                         creator: discord.User = None):
    if creator is None:
        creator = interaction.user
    if re.search("\Ahttps://docs.google.com/presentation/d/.+", link) is not None:
        try:
            cur.execute("INSERT INTO powerpoints (guild_id,Link,user_id,allowself,used) VALUES (?,?,?,?,0)",
                        (interaction.guild_id, link, creator.id, allowself))
            conn.commit()
            await interaction.response.send_message("Powerpoint added")
        except sqlite3.IntegrityError:
            await interaction.response.send_message("Powerpoint already exists")
    else:
        await interaction.response.send_message("not a valid link")


@app_commands.command(name="get_ppt", description="picks a random powerpoint")
async def get_powerpoint(interaction: discord.Interaction):
    cur.execute(
        "SELECT Link,user_id,guild_id FROM powerpoints WHERE guild_id=? and (user_id!=? or allowself=1) and used=0",
        (interaction.guild_id, interaction.user.id))
    links = cur.fetchall()
    if len(links) == 0:
        await interaction.response.send_message("No valid powerpoints in this server")
    else:
        row = random.choice(links)
        link = row[0]
        creator = await client.fetch_user(row[1])
        guild_id = row[2]
        url = "http://127.0.0.1:5000/checkpoint/?link=" + link + "&username=" + interaction.user.name
        await interaction.response.send_message(
            "please click here to view the powerpoint: " + url + "\n created by " + creator.name)
        cur.execute("UPDATE powerpoints SET used=1 WHERE Link=? and guild_id=?", (link, guild_id))
        conn.commit()


@app_commands.command(name="my_ppts", description="shows all powerpoints you have created")
async def my_powerpoints(interaction: discord.Interaction):
    cur.execute("SELECT Link FROM powerpoints WHERE user_id=? and guild_id=? ORDER BY Link",
                (interaction.user.id, interaction.guild_id))
    links = cur.fetchall()
    if len(links) == 0:
        await interaction.response.send_message("you have no powerpoints")
    else:
        linkstr = "\n".join(str(count) + ". " + link[0] for count, link in enumerate(links))
        await interaction.response.send_message(f"you have {str(len(links))} powerpoints\n{linkstr}")


@app_commands.command(name="remaing_ppts", description="shows stats about many powerpoints are left")
async def remaing_ppts(interaction: discord.Interaction):
    cur.execute("SELECT * FROM powerpoints WHERE guild_id=?", (interaction.guild_id,))
    alllinks = cur.fetchall()
    cur.execute("SELECT * FROM powerpoints WHERE guild_id=? and used=0", (interaction.guild_id,))
    unusedlinks = cur.fetchall()
    userunusedcount = countbyuser(unusedlinks)
    usertotcount = countbyuser(alllinks)
    userstatlist = []
    for user in usertotcount:
        usertot = usertotcount[user]
        userunused = 0
        if user in userunusedcount:
            userunused = userunusedcount[user]
        username = await client.fetch_user(user)
        userstatlist.append(f"{userunused}/{usertot} by {username.name}")

    if len(alllinks) == 0:
        await interaction.response.send_message("No powerpoints in this server")
    else:
        individualuserdata = "\n".join(userstatlist)
        await interaction.response.send_message(embed=discord.Embed(title="Powerpoints left",
                                                                    description=f"{len(unusedlinks)}/{len(alllinks)} powerpoints left\n\n{individualuserdata}"))


def countbyuser(links):
    users = {}
    for link in links:
        if link[2] in users:
            users[link[2]] += 1
        else:
            users[link[2]] = 1
    return users


web.runserver()
client.run(os.getenv("TOKEN"))
