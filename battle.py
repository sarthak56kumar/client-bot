import discord
from discord.ext import commands
import random
import json
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
from prettytable import PrettyTable


load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

data_file_path = 'C:/Users/sarth/OneDrive/Desktop/sarangi.bot/sarangi-discord-bot/data.json'

def load_data_from_json():
    try:
        with open(data_file_path, 'r') as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

def get_user_cards(user_id):
    data = load_data_from_json()
    user_data = data.get("users", {}).get(str(user_id)) 

    if user_data:
        return user_data.get('cards', [])
    else:
        print(f"No data found for user {user_id}")
        return []


data = load_data_from_json()
active_battles = {}

async def send_card_images(user, selected_cards):
    """Send each card as a separate embed."""
    for card in selected_cards:
        embed = discord.Embed(
            title=f"{card.get('name')}",
            description=f"Rating: {card.get('rating')}",
            color=discord.Color.blue()
        )
        image_url = card.get('image_url')
        if image_url:
            embed.set_image(url=image_url)
        await user.send(embed=embed)


async def send_card(user, card_name):
    user_data = data.get('users', {}).get(str(user.id)) 

    if not user_data:
        await user.send("Sorry, user data not found.")
        return

    found_card = None
    for card in user_data.get("cards", []):  
        if card["name"].lower() == card_name.lower():
            found_card = card
            break

    if not found_card:
        await user.send(f"Sorry, I couldn't find any information for the card '{card_name}'.")
        return

    embed = discord.Embed(
        title=found_card["name"],
        description=(
            f"Rating: {found_card['rating']}\n"
            f"Price: {found_card['price']}\n"
            f"AGR: {found_card['agr']}\n"
            f"Apps: {found_card.get('APPS', 'N/A')}"
        ),
        color=discord.Color.blue()
    )

    image_url = found_card.get("image_url")
    if image_url:
        embed.set_image(url=image_url)

    await user.send(embed=embed)



@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')


@bot.command(name="roll")
async def give_daily_cards(ctx):
    user_id = str(ctx.author.id)
    today = datetime.now().date().strftime("%Y-%m-%d")

    # Load data
    data = load_data_from_json()
    user_data = data.get("users", {})
    available_cards = data.get("available_cards", [])

    if user_id in user_data:
        user_profile = user_data[user_id]
    else:
        user_profile = {
            "user_id": user_id,
            "name": ctx.author.name,
            "date": "", 
            "points": 0,
            "cards": [],
            "visit_count": 0  
        }
        user_data[user_id] = user_profile

    if user_profile.get("date") != today:
        user_profile["visit_count"] = 0  
        user_profile["date"] = today
        save_user_data(data)


    if user_profile.get("date") == today:
        if user_profile["visit_count"] == 0:
            daily_card = random.sample(available_cards, 1)[0]
            user_profile["cards"] = [daily_card]
            user_profile["visit_count"] += 1
            save_user_data(data)
            await ctx.author.send(f"Here is your first card for today:\n{daily_card['image_url']}")
        elif user_profile["visit_count"] == 1:
            daily_card = random.sample(available_cards, 1)[0]
            user_profile["cards"].append(daily_card)  
            user_profile["visit_count"] += 1 
            data["users"] = user_data  
            save_user_data(data)
            await ctx.author.send(f"Here is your second card for today:\n{daily_card['image_url']}")
        else:
            await ctx.author.send("You’ve already received your cards today. Check this link for more info: https://www.BeingSarangi.com")
        return
    else:
        user_profile["date"] = today
        user_profile["visit_count"] = 1
        daily_card = random.sample(available_cards, 1)[0]
        user_profile["cards"] = [daily_card]
        data["users"] = user_data
        save_user_data(data)
        await ctx.author.send(f"Here is your first card for today:\n{daily_card['image_url']}")




def save_user_data(user_data):
    try:
        with open(data_file_path, 'w') as file:
            json.dump(user_data, file, indent=4)
    except Exception as e:
        print(f"Error saving user data: {e}")


@bot.command()
async def battle(ctx: commands.Context, opponent: str):
    try:
        opponent_user = await commands.UserConverter().convert(ctx, opponent)

        userA_id = ctx.author.id
        userB_id = opponent_user.id
        print(f"UserA ID: {userA_id}, UserB ID: {userB_id}")

        userA_cards = get_user_cards(userA_id)
        userB_cards = get_user_cards(userB_id)

        # print(f"UserA cards: {userA_cards}")
        # print(f"UserB cards: {userB_cards}") 


        if len(userA_cards) < 3 or len(userB_cards) < 3:
            await ctx.send("One of the players doesn't have enough cards to battle! Both players need at least 3 cards.")
            return

        bot_selected_A = random.sample(userA_cards, 3)
        bot_selected_B = random.sample(userB_cards, 3)

        battle_data = {
            "userA_id": userA_id,
            "userB_id": userB_id,
            "userA_cards": bot_selected_A,
            "userB_cards": bot_selected_B,
            "status": "pending"
        }
        active_battles[userA_id] = battle_data
        active_battles[userB_id] = battle_data  

        active_battles[userA_id] = battle_data

        await ctx.send(f"{ctx.author.mention} challenged {opponent_user.mention} to a battle! Type `!accept` to join.")
        await ctx.author.send(f"Your selected cards: {bot_selected_A}")
        await opponent_user.send(f"Your selected cards: {bot_selected_B}")

    except commands.CommandError as e:
        await ctx.send(f"An error occurred: {e}")
 
 
        print(f"Error in battle command: {e}")

@bot.command()
async def accept(ctx):
    """Accept a pending battle and retrieve player card info."""
    user_id = ctx.author.id
    battle_found = False
    battle_data = None

    for battle_key, battle in active_battles.items():
        if battle.get('userB_id') == user_id and battle.get('status') == 'pending':
            battle_found = True
            battle_data = battle
            break

    if battle_found and battle_data:
        await ctx.send(f"Battle found for acceptance! UserA ID: {battle_data.get('userA_id')}, UserB ID: {battle_data.get('userB_id')}")

        userA = bot.get_user(battle_data.get("userA_id"))
        userB = bot.get_user(battle_data.get("userB_id"))
        await ctx.send(f"Battle accepted between {userA.mention} and {userB.mention}!")

        await send_card_images(userA, battle_data.get('userA_cards'))
        await send_card_images(userB, battle_data.get('userB_cards'))

        await get_additional_cards(ctx, battle_data)

        del active_battles[battle_key]
    else:
        await ctx.send("No pending battle found.")



async def get_additional_cards(ctx, battle):
    userA_id = battle['userA_id']
    userB_id = battle['userB_id']

    userA_initial_cards = battle['userA_cards']
    userB_initial_cards = battle['userB_cards']

    userA = bot.get_user(userA_id)
    userB = bot.get_user(userB_id)

    await userA.send("Select two additional cards to complete your hand of five.")
    await userB.send("Select two additional cards to complete your hand of five.")

    def check_a(m):
        return m.author.id == userA_id

    def check_b(m):
        return m.author.id == userB_id

    try:
        userA_available_cards = [card['name'] for card in userA_initial_cards]
        await userA.send(f"Available cards: {', '.join(userA_available_cards)}")
        userA_msg1 = await bot.wait_for('message', check=check_a, timeout=1000.0)
        card_name1 = userA_msg1.content.strip()

        
        await send_card(userA, card_name1)
        
        userA_msg2 = await bot.wait_for('message', check=check_a, timeout=1000.0)
        card_name2 = userA_msg2.content.strip()  

        await send_card(userA, card_name2)

        
        userB_available_cards = [card['name'] for card in userB_initial_cards]
        await userB.send(f"Available cards: {', '.join(userB_available_cards)}")
        userB_msg1 = await bot.wait_for('message', check=check_b, timeout=2000.0)
        card_name1_b = userB_msg1.content.strip()

        await send_card(userB, card_name1_b)

        userB_msg2 = await bot.wait_for('message', check=check_b, timeout=2000.0)
        card_name2_b = userB_msg2.content.strip()

        await send_card(userB, card_name2_b)
        await ctx.send(f"Both players have selected their cards. Let the battle begin!")
        await start_battle(ctx, battle, userA_initial_cards, userB_initial_cards, card_name1, card_name2, card_name1_b, card_name2_b)

    except asyncio.TimeoutError:
        await ctx.send("A user took too long to select additional cards.")

async def start_battle(ctx, battle, userA_initial_cards, userB_initial_cards, card_name1, card_name2, card_name1_b, card_name2_b):
    await ctx.send(f"Both players have selected their cards. Let the battle begin!")

    def get_card_by_name(card_name, user_cards):
        for card in user_cards:
            if card['name'] == card_name:
                return card
        return None

    if isinstance(userA_initial_cards[0], str): 
        userA_initial_cards = [get_card_by_name(card_name, battle['userA'][0]['cards']) for card_name in userA_initial_cards]
    
    if isinstance(userB_initial_cards[0], str): 
        userB_initial_cards = [get_card_by_name(card_name, battle['userB'][0]['cards']) for card_name in userB_initial_cards]

    
    selected_card_a1 = get_card_by_name(card_name1, userA_initial_cards)
    selected_card_a2 = get_card_by_name(card_name2, userA_initial_cards)
    selected_card_b1 = get_card_by_name(card_name1_b, userB_initial_cards)
    selected_card_b2 = get_card_by_name(card_name2_b, userB_initial_cards)

    userA_hand = userA_initial_cards + [selected_card_a1, selected_card_a2]
    userB_hand = userB_initial_cards + [selected_card_b1, selected_card_b2]

    # print("-"*125)
    # print(userA_hand, type(userA_hand))
    # print("-" * 100)
    # print(userB_hand, type(userB_hand))
    # print("-"*125)

    await start_battle_rounds(ctx, userA_hand, userB_hand, battle)


async def start_battle_rounds(ctx, userA_hand, userB_hand, battle):
    # print("*"*125)
    # print(userA_hand, type(userA_hand))
    # print("*" * 100)
    # print(userB_hand, type(userB_hand))
    # print("*"*125)
    userA = bot.get_user(battle['userA_id'])
    userB = bot.get_user(battle['userB_id'])

    for round_num in range(1, 6):
        await ctx.send(f"Round {round_num} begins!")

        cards_message_a = "\n".join([f"{card['name']} - {card['rating']} rating, {card['APPS']} apps, {card['agr']} agr, {card.get('SV', 'N/A')} SV, {card.get('G/A', 'N/A')} G/A, {card.get('TW', 'N/A')} TW" for card in userA_hand if card is not None])

        cards_message_b = "\n".join([f"{card['name']} - {card['rating']} rating, {card['APPS']} apps, {card['agr']} agr, {card.get('SV', 'N/A')} SV, {card.get('G/A', 'N/A')} G/A, {card.get('TW', 'N/A')} TW" for card in userB_hand if card is not None])
        
        await userA.send(f"Choose a card and a stat (Rating, APPS, AGR, SV, G/A, TW):\n{cards_message_a}")
        await userB.send(f"Choose a card (same stat will be used for comparison for User B):\n{cards_message_b}")


        valid_stats = ['rating', 'apps', 'agr', 'sv', 'g/a', 'tw']
        def check_a(m):
            if m.author.id == userA.id:
                parts = m.content.split()
                
                if len(parts) >= 2:  
                    stat_name = parts[-1].lower()
                    card_name = ' '.join(parts[:-1]).lower() 
                    
                    if any(card['name'].lower() == card_name for card in userA_hand) and stat_name in valid_stats:
                        return True
                    else:
                        m.channel.send("Invalid input! Please enter the card name followed by the stat (e.g., 'Alexander Isak rating').")
            return False

        
        def check_b(m):
            if m.author.id == userB.id:
                card_name = m.content.strip().lower() 
                if any(card['name'].lower() == card_name for card in userB_hand):
                    return True
                else:
                    m.channel.send("Invalid input! Please enter the card name (e.g., 'Bruno Guimaraes').")
            return False


        try:
            message_a = await bot.wait_for('message', check=check_a, timeout=200.0)
            message_a_content = message_a.content.strip().split()
            if len(message_a_content) == 2:
                card_a, stat_a = message_a_content
            elif len(message_a_content) == 3:
                card_a = f"{message_a_content[0]} {message_a_content[1]}" 
                stat_a = message_a_content[2]
            else:
                await ctx.send("Invalid input. Please enter either two or three words.")
                return
            

            selected_card_a = next(card for card in userA_hand if card['name'] == card_a)
            await send_card_images(userB, [selected_card_a])

            message_b = await bot.wait_for('message', check=check_b, timeout=200.0)
            card_b = message_b.content.strip()
            
            selected_card_b = next(card for card in userB_hand if card['name'] == card_b)

            await send_card_images(userA, [selected_card_b])

            stat_value_a = selected_card_a[stat_a]  
            stat_value_b = selected_card_b[stat_a] 
            if(stat_value_a == "N/A"):
                stat_value_a = 0
            if(stat_value_b == "N/A"):
                stat_value_b = 0
            userA_score = 0
            userB_score = 0
            if stat_value_a > stat_value_b:
                round_winner = "User A"
                userA_score += 1  
                
            else:
                round_winner = "User B"
                userB_score += 1  
            

            userA_hand.remove(selected_card_a)
            userB_hand.remove(selected_card_b)



            await ctx.send(f"Round {round_num} winner: {round_winner}")

        except asyncio.TimeoutError:
            await ctx.send("A user took too long to select a card.")
            return

    await determine_final_winner(ctx, userA_score, userB_score, userA, userB, data)

async def determine_final_winner(ctx, userA_score, userB_score, userA, userB, data):
    if userA_score > userB_score:
        final_winner = f"<@{userA.id}> with {userA_score} points!"
        if userA.id in data["users"]:
            data["users"][userA.id]["points"] += 5
    elif userB_score > userA_score:
        final_winner = f"<@{userB.id}> with {userB_score} points!"
        if userB.id in data["users"]:
            data["users"][userB.id]["points"] += 5
    else:
        final_winner = "It's a draw! Both players have the same score."

    await ctx.send(f"The final winner is: {final_winner}")
    save_user_data(data)

@bot.command(name="team")
async def show_team_data(ctx):
    user_id = str(ctx.author.id) 

    data = load_data_from_json()
    user_data = data.get("users", {})

    if user_id not in user_data:
        await ctx.author.send("You have no data yet. Please get your cards first.")
        return

    user_profile = user_data[user_id]
    points = user_profile.get('points', 0) 
    cards = user_profile.get('cards', [])

    embed = discord.Embed(
        title=f"{ctx.author.name}'s Data",
        description=f"Points: {points}",
        color=discord.Color.green()
    )

    await ctx.author.send(embed=embed)

    if cards:
        for card in cards:
            card_embed = discord.Embed(
                title=f"{card.get('name')}",
                description=f"Rating: {card.get('rating')}\nPrice: {card.get('price')}",
                color=discord.Color.blue()
            )
            image_url = card.get('image_url')
            if image_url:
                card_embed.set_image(url=image_url)
            await ctx.author.send(embed=card_embed)
    else:
        await ctx.author.send("You don't have any cards yet.")

def save_data_to_json(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)


@bot.command(name="sell")
async def sell_card(ctx, *, card_name: str):
    user_id = str(ctx.author.id)
    data = load_data_from_json()

    user_data = data.get("users", {}).get(user_id)
    if not user_data:
        await ctx.send(f"{ctx.author.mention}, you do not have an account in the system.")
        return

    user_cards = user_data.get("cards", [])
    card_to_sell = next((card for card in user_cards if card["name"].lower() == card_name.lower()), None)

    if not card_to_sell:
        await ctx.send(f"{ctx.author.mention}, you don't own a card named '{card_name}'.")
        return


    card_points = card_to_sell.get("price", 0)
    user_points = user_data.get("points", 0)
    user_data["points"] = user_points + card_points


    user_cards.remove(card_to_sell)
    user_data["cards"] = user_cards


    data["available_cards"].append(card_to_sell)


    save_data_to_json(data)

    await ctx.send(
        f"{ctx.author.mention}, you have successfully sold the card '{card_name}' for {card_points} points!\n"
        f"Your new points total is {user_data['points']}."
    )


@bot.command(name="leaderboard")
async def dashboard(ctx):
    users_data = data.get("users", {})

    leaderboard = []
    for user_id, user_info in users_data.items():
        wins = user_info.get("Wins", 0)
        losses = user_info.get("losses", 0)
        matches_played = wins + losses  
        leaderboard.append({
            "name": user_info.get("name", "Unknown"),
            "wins": wins,
            "losses": losses,
            "matches_played": matches_played
        })

    leaderboard.sort(key=lambda x: x["wins"], reverse=True)

    table = PrettyTable()
    table.field_names = ["Rank", "User", "Wins", "Losses", "Matches Played"]

    for rank, user in enumerate(leaderboard, start=1): 
        table.add_row([rank, user["name"], user["wins"], user["losses"], user["matches_played"]])

    await ctx.send(f"```\n{table}\n```")


@bot.command(name="shop")
async def shop(ctx):
    website_url = "https://www.google.com"
    await ctx.author.send(f"Visit the shop: {website_url}")

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
