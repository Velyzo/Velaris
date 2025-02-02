import discord
from discord.ext import commands
from discord import Intents, app_commands
from discord.ui import Modal, TextInput, View, Button, Select
import os
import datetime
import pytz
import uuid
import asyncio
from datetime import date, timedelta

TOKEN = os.getenv('TOKEN')

if TOKEN:
    print(f"Bot started with TOKEN: {token}")
else:
    print("TOKEN environment variable is not set.")

MAX_REQUESTS_PER_HOUR = 60

user_requests = {}

text_files = {}

start_time = datetime.datetime.now()

intents = discord.Intents.default()
intents.message_content = True
intents.bans = True

file_storage_dir = "saved_files"
os.makedirs(file_storage_dir, exist_ok=True)

def link_button(text, link):
    link_button = Button(label=text, url=link)
    view_button_link = View()
    view_button_link.add_item(link_button)
    return view_button_link
        
def is_admin(user_id):
    admin_file = os.path.join(os.path.dirname(__file__), "admin.txt")
    if not os.path.exists(admin_file):
        with open(admin_file, "w") as file:
            file.write("")
        print("admin.txt Datei wurde erstellt.")
        return False
    
    with open(admin_file, "r") as file:
        admin_ids = [int(line.strip()) for line in file.readlines()]
    return user_id in admin_ids

def can_user_make_request(user_id):
    now = datetime.datetime.now()
    if user_id in user_requests:
        request_info = user_requests[user_id]
        request_count = request_info['count']
        first_request_time = request_info['first_request_time']
        
        if now - first_request_time > timedelta(hours=1):
            user_requests[user_id] = {'count': 1, 'first_request_time': now}
            return True
        elif request_count < MAX_REQUESTS_PER_HOUR:
            user_requests[user_id]['count'] += 1
            return True
        else:
            return False
    else:
        user_requests[user_id] = {'count': 1, 'first_request_time': now}
        return True
    
timezone_mapping = {
    "New York": "America/New_York",
    "Los Angeles": "America/Los_Angeles",
    "London": "Europe/London",
    "Tokyo": "Asia/Tokyo",
    "Berlin": "Europe/Berlin",
    "Sydney": "Australia/Sydney",
    "Paris": "Europe/Paris",
    "UTC": "UTC",
    "Japan": "Asia/Tokyo",
    "Germany": "Europe/Berlin",
    "USA": "America/New_York",
    "Chicago": "America/Chicago",
    "Toronto": "America/Toronto",
    "Mexico City": "America/Mexico_City",
    "SÃ£o Paulo": "America/Sao_Paulo",
    "Moscow": "Europe/Moscow",
    "Dubai": "Asia/Dubai",
    "Hong Kong": "Asia/Hong_Kong",
    "Singapore": "Asia/Singapore",
    "Mumbai": "Asia/Kolkata",
    "Johannesburg": "Africa/Johannesburg",
    "Cairo": "Africa/Cairo",
    "Stockholm": "Europe/Stockholm",
    "Madrid": "Europe/Madrid",
}

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='.', intents=Intents().all())
        self.activity = discord.Activity(
            type=discord.ActivityType.watching,
            name='VelisCore',
            details='v25.1.27',
            state='Loading...',
            start=datetime.datetime.now()
        )

    async def on_ready(self):
        print("Logged in as " + self.user.name)
        synced = await self.tree.sync()
        print("Slash CMDs Synced " + str(len(synced)) + " Commands")

    async def on_member_join(self, member):
        channel_id = 1333416134740807772
        channel = self.get_channel(channel_id)
        if channel:
            await channel.send(f'**Welcome**, {member.mention}, to **Velis**!')

client = Client()

@client.tree.context_menu(name="Report")
async def resend(interaction: discord.Interaction, message: discord.Message):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message(
            "You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour, try to contact us.", 
            ephemeral=True
        )
        return

    feedback_directory = "feedback"

    if not os.path.exists(feedback_directory):
        os.makedirs(feedback_directory)

    files = os.listdir(feedback_directory)
    numbers = [int(os.path.splitext(file)[0]) for file in files if file.endswith(".txt") and os.path.splitext(file)[0].isdigit()]

    feedback_number = max(numbers, default=0) + 1
    file_path = os.path.join(feedback_directory, f'{feedback_number}.txt')

    today_date = date.today().isoformat()
    user_id = interaction.user.id
    reported_user_id = message.author.id
    reported_user_name = message.author.name
    channel_name = message.channel.name
    channel_id = message.channel.id
    reported_message = message.content

    feedback_text = (
        '# Feedback Submission\n\n'
        f'- **Program:** The program you provided feedback on.\n'
        f'- **Submitted by (USER-ID):** {user_id}\n'
        f'- **Submission Date and Time:** {today_date}\n'
        f'- **Reported Message:** `{reported_message}`\n'
        f'- **Author of the Reported Message (USER-ID):** {reported_user_id}\n'
        f'- **Author of the Reported Message (NAME):** {reported_user_name}\n'
        f'- **Channel Name:** {channel_name}\n'
        f'- **Channel ID:** {channel_id}\n'
    )

    try:
        with open(file_path, "w") as file:
            file.write(feedback_text)
    except IOError as e:
        await interaction.response.send_message(f"An error occurred while saving feedback: {e}", ephemeral=True)
        return

    response_message = (
        '# Feedback Submitted\n\n'
        f'Thank you! Feedback **#{feedback_number}** has been recorded.\n'
        f'**Reported Message:** `{reported_message}`\n'
        f'**Channel:** {channel_name} (ID: {channel_id})\n'
        f'**Submitted at:** {today_date}\n'
    )

    await interaction.response.send_message(response_message, ephemeral=True)

@client.tree.context_menu(name="Resend")
async def resend(interaction: discord.Interaction, message: discord.Message):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    escaped_message_content = discord.utils.escape_markdown(message.content)
    await interaction.response.send_message(
        f"`{escaped_message_content}` | **Resent by {interaction.user}** \n"
        "-# This message is temporary and will be deleted in 10 seconds..."
    )
    await asyncio.sleep(10)
    await interaction.delete_original_response()


class FeedbackModal(Modal):
    def __init__(self):
        super().__init__(title="Feedback")
        
        self.add_item(TextInput(label="Program", style=discord.TextStyle.short))
        self.add_item(TextInput(label="Rate your chosen Program", placeholder="Rate your experience from 1-10"))
        self.add_item(TextInput(label="Why?", placeholder="Why did you give this rating?", style=discord.TextStyle.short))
        self.add_item(TextInput(label="Feature Request", placeholder="What features would you like to see?", style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        program = self.children[0].value
        rating = self.children[1].value
        reason = self.children[2].value
        feature_request = self.children[3].value

        feedback_directory = "feedback"
        
        if not os.path.exists(feedback_directory):
            os.makedirs(feedback_directory)

        files = os.listdir(feedback_directory)
        numbers = []

        for file in files:
            if file.endswith(".txt"):
                filename_without_extension = os.path.splitext(file)[0]
                if filename_without_extension.isdigit():
                    numbers.append(int(filename_without_extension))

        try:
            if not numbers:
                feedback_number = 0
            else:
                feedback_number = max(numbers) + 1
        except ValueError:
            feedback_number = 0

        file_path = os.path.join(feedback_directory, f'{feedback_number}.txt')
        
        response_message = (
            '# Feedback\n\n'
            f'Program : {program}.\n'
            f'Given rating: {rating}.\n'
            f'Reason: {reason}\n'
            f'Feature request: {feature_request}\n\n'
            f'Feedback **#{feedback_number}** has been submitted.'
        )
        
        today_date = date.today().isoformat()
        user_id = interaction.user.id
        
        text_message = (
            '# Feedback\n\n'
            f'Program : {program}\n'
            f'Submitted by USER-ID : {user_id}\n'
            f'Submitted at: {today_date}\n'
            f'Given rating: {rating}.\n'
            f'Reason: {reason}\n'
            f'Feature request: {feature_request}\n\n'
            f'Feedback Number: **#{feedback_number}**.\n'
            f'Status: None.'
        )
        
        try:
            with open(file_path, "w") as file:
                file.write(text_message)
        except IOError as e:
            await interaction.response.send_message(f"An error occurred while saving feedback: {e}", ephemeral=True)
            return
        
        await interaction.response.send_message(response_message, ephemeral=True)

@app_commands.command(name='feedback', description="Give feedback for our Bot.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def feedback(interaction: discord.Interaction):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    modal = FeedbackModal()
    await interaction.response.send_modal(modal)

class HelpView(View):
    def __init__(self):
        super().__init__()
        self.add_item(HelpSelect())

class HelpSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Eulionline", description="Pick this if you need help with Eulionline!"),
            discord.SelectOption(label="Eulionline Android", description="Pick this if you need help with the Eulionline Android App!"),
            discord.SelectOption(label="Eulionline iOS/iPadOS", description="Pick this if you need help with the Eulionline iOS/iPadOS App!"),
            discord.SelectOption(label="Eulionline MacOS", description="Pick this if you need help with the Eulionline MacOS App!"),
            discord.SelectOption(label="Eulionline Preview", description="Pick this if you need help with the Eulionline Preview Page!"),
            discord.SelectOption(label="Eulionline Windows", description="Pick this if you need help with the Eulionline Windows App!"),
            discord.SelectOption(label="Ideora", description="Pick this if you need help with Ideora!"),
            discord.SelectOption(label="Ideora iOS/iPadOS", description="Pick this if you need help with the Ideora iOS/iPadOS App!"),
            discord.SelectOption(label="Devco", description="Pick this if you need help with Devco!"),
            discord.SelectOption(label="Devco API", description="Pick this if you need help with the Devco API!"),
            discord.SelectOption(label="Devco Linux", description="Pick this if you need help with the Devco Linux App!"),
            discord.SelectOption(label="Devco MacOS", description="Pick this if you need help with the Devco MacOS App!"),
            discord.SelectOption(label="Devco Windows", description="Pick this if you need help with the Devco Windows App!"),
            discord.SelectOption(label="Vocules", description="Pick this if you need help with Vocules!"),
            discord.SelectOption(label="Keylogger", description="Pick this if you need help with our Keylogger!"),
            discord.SelectOption(label="InsightLog", description="Pick this if you need help with InsightLog!"),
            discord.SelectOption(label="ReturnTime", description="Pick this if you need help with ReturnTime!"),
            discord.SelectOption(label="diec", description="Pick this if you need help with diec!"),
            discord.SelectOption(label="BetterTkinter", description="Pick this if you need help with BetterTkinter!"),
            discord.SelectOption(label="OpenAlways", description="Pick this if you need help with OpenAlways!"),
            discord.SelectOption(label="githubinformation", description="Pick this if you need help with githubinformation!"),
            discord.SelectOption(label="Connecto", description="Pick this if you need help with Connecto!"),
            discord.SelectOption(label="devplaceo", description="Pick this if you need help with devplaceo!"),
            discord.SelectOption(label="D&I Bot", description="Pick this if you need help with our Discord Bot!"),
            discord.SelectOption(label="diec", description="Pick this if you need help with our PyPi Package *diec*!"),
            discord.SelectOption(label="Destor", description="Pick this if you need help with our Program Destor!"),
            discord.SelectOption(label="ChatBox", description="Pick this if you need help with our Program ChatBox!"),
        ]
        super().__init__(placeholder="Choose your software!", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_help = self.values[0]
        di_bot_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Velaris/wiki")
        diec_button = link_button(text="Show 📩", link="https://github.com/VelisCore/diec")
        destor_button = link_button(text="Show 📩", link="https://github.com/VelisCore/destor")
        discordbotmanager_button = link_button(text="Show 📩", link="https://github.com/VelisCore/DiscordBotManager/wiki")
        eulionline_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Eulionline")
        ideora_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Ideora")
        devco_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Devco")
        vocules_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Vocules")
        keylogger_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Keylogger")
        insightlog_button = link_button(text="Show 📩", link="https://github.com/VelisCore/InsightLog")
        returntime_button = link_button(text="Show 📩", link="https://github.com/VelisCore/ReturnTime")
        bettertkinter_button = link_button(text="Show 📩", link="https://github.com/VelisCore/BetterTkinter")
        openalways_button = link_button(text="Show 📩", link="https://github.com/VelisCore/OpenAlways")
        githubinformation_button = link_button(text="Show 📩", link="https://github.com/VelisCore/githubinformation")
        connecto_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Connecto")
        devplaceo_button = link_button(text="Show 📩", link="https://github.com/VelisCore/devplaceo")

        if selected_help == "D&I Bot":
            await interaction.response.send_message(f"Here you can read more about our [Discord Bot](https://github.com/VelisCore/Velaris/wiki). If you have any more questions, run `/feedback`.", view=di_bot_button, ephemeral=True)
        elif selected_help == "diec":
            await interaction.response.send_message(f"Here you can read more about our PyPi Package [diec](https://github.com/VelisCore/diec). If you have any more questions, run `/feedback`.", view=diec_button, ephemeral=True)
        elif selected_help == "Destor":
            await interaction.response.send_message(f"Here you can read more about our Program [Destor](https://github.com/VelisCore/destor). If you have any more questions, run `/feedback`.", view=destor_button, ephemeral=True)
        elif selected_help == "ChatBox":
            await interaction.response.send_message(f"Here you can read more about our Program [ChatBox](https://github.com/VelisCore/ChatBox/wiki). If you have any more questions, run `/feedback`.", view=discordbotmanager_button, ephemeral=True)
        elif selected_help == "Eulionline":
            await interaction.response.send_message(f"Here you can read more about [Eulionline](https://github.com/VelisCore/Eulionline). If you have any more questions, run `/feedback`.", view=eulionline_button, ephemeral=True)
        elif selected_help == "Eulionline Android":
            await interaction.response.send_message(f"Here you can read more about the [Eulionline Android App](https://github.com/VelisCore/Eulionline-Android). If you have any more questions, run `/feedback`.", view=eulionline_button, ephemeral=True)
        elif selected_help == "Eulionline iOS/iPadOS":
            await interaction.response.send_message(f"Here you can read more about the [Eulionline iOS/iPadOS App](https://github.com/VelisCore/Eulionline-iOS). If you have any more questions, run `/feedback`.", view=eulionline_button, ephemeral=True)
        elif selected_help == "Eulionline MacOS":
            await interaction.response.send_message(f"Here you can read more about the [Eulionline MacOS App](https://github.com/VelisCore/Eulionline-MacOS). If you have any more questions, run `/feedback`.", view=eulionline_button, ephemeral=True)
        elif selected_help == "Eulionline Preview":
            await interaction.response.send_message(f"Here you can read more about the [Eulionline Preview](https://github.com/VelisCore/Eulionline-Preview). If you have any more questions, run `/feedback`.", view=eulionline_button, ephemeral=True)
        elif selected_help == "Eulionline Windows":
            await interaction.response.send_message(f"Here you can read more about the [Eulionline Windows App](https://github.com/VelisCore/Eulionline-Windows). If you have any more questions, run `/feedback`.", view=eulionline_button, ephemeral=True)
        elif selected_help == "Ideora":
            await interaction.response.send_message(f"Here you can read more about [Ideora](https://github.com/VelisCore/Ideora). If you have any more questions, run `/feedback`.", view=ideora_button, ephemeral=True)
        elif selected_help == "Ideora iOS/iPadOS":
            await interaction.response.send_message(f"Here you can read more about the [Ideora iOS/iPadOS App](https://github.com/VelisCore/Ideora-iOS). If you have any more questions, run `/feedback`.", view=ideora_button, ephemeral=True)
        elif selected_help == "Devco":
            await interaction.response.send_message(f"Here you can read more about [Devco](https://github.com/VelisCore/Devco). If you have any more questions, run `/feedback`.", view=devco_button, ephemeral=True)
        elif selected_help == "Devco API":
            await interaction.response.send_message(f"Here you can read more about the [Devco API](https://github.com/VelisCore/Devco-API). If you have any more questions, run `/feedback`.", view=devco_button, ephemeral=True)
        elif selected_help == "Devco Linux":
            await interaction.response.send_message(f"Here you can read more about the [Devco Linux App](https://github.com/VelisCore/Devco-Linux). If you have any more questions, run `/feedback`.", view=devco_button, ephemeral=True)
        elif selected_help == "Devco MacOS":
            await interaction.response.send_message(f"Here you can read more about the [Devco MacOS App](https://github.com/VelisCore/Devco-MacOS). If you have any more questions, run `/feedback`.", view=devco_button, ephemeral=True)
        elif selected_help == "Devco Windows":
            await interaction.response.send_message(f"Here you can read more about the [Devco Windows App](https://github.com/VelisCore/Devco-Windows). If you have any more questions, run `/feedback`.", view=devco_button, ephemeral=True)
        elif selected_help == "Vocules":
            await interaction.response.send_message(f"Here you can read more about [Vocules](https://github.com/VelisCore/Vocules). If you have any more questions, run `/feedback`.", view=vocules_button, ephemeral=True)
        elif selected_help == "Keylogger":
            await interaction.response.send_message(f"Here you can read more about [Keylogger](https://github.com/VelisCore/Keylogger). If you have any more questions, run `/feedback`.", view=keylogger_button, ephemeral=True)
        elif selected_help == "InsightLog":
            await interaction.response.send_message(f"Here you can read more about [InsightLog](https://github.com/VelisCore/InsightLog). If you have any more questions, run `/feedback`.", view=insightlog_button, ephemeral=True)
        elif selected_help == "ReturnTime":
            await interaction.response.send_message(f"Here you can read more about [ReturnTime](https://github.com/VelisCore/ReturnTime). If you have any more questions, run `/feedback`.", view=returntime_button, ephemeral=True)
        elif selected_help == "BetterTkinter":
            await interaction.response.send_message(f"Here you can read more about [BetterTkinter](https://github.com/VelisCore/BetterTkinter). If you have any more questions, run `/feedback`.", view=bettertkinter_button, ephemeral=True)
        elif selected_help == "OpenAlways":
            await interaction.response.send_message(f"Here you can read more about [OpenAlways](https://github.com/VelisCore/OpenAlways). If you have any more questions, run `/feedback`.", view=openalways_button, ephemeral=True)
        elif selected_help == "githubinformation":
            await interaction.response.send_message(f"Here you can read more about [githubinformation](https://github.com/VelisCore/githubinformation). If you have any more questions, run `/feedback`.", view=githubinformation_button, ephemeral=True)
        elif selected_help == "Connecto":
            await interaction.response.send_message(f"Here you can read more about [Connecto](https://github.com/VelisCore/Connecto). If you have any more questions, run `/feedback`.", view=connecto_button, ephemeral=True)
        elif selected_help == "devplaceo":
            await interaction.response.send_message(f"Here you can read more about [devplaceo](https://github.com/VelisCore/devplaceo). If you have any more questions, run `/feedback`.", view=devplaceo_button, ephemeral=True)
            
@app_commands.command(name="help", description="A command that helps you!")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def help_command(interaction: discord.Interaction):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    await interaction.response.send_message(f"Select the software with that you need help with.", view=HelpView(), ephemeral=True)

class PingView(View):
    def __init__(self):
        super().__init__()
        
        check_again_button = Button(label="Check again", style=discord.ButtonStyle.success)
        check_again_button.callback = self.check_again
        self.add_item(check_again_button)

    async def check_again(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"**Pong! {round(interaction.client.latency * 1000)}ms**", view=self)

@app_commands.command(name="ping", description="Show you the current Ping of the Bot!")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def ping(interaction: discord.Interaction):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    await interaction.response.send_message(f"**Pong! {round(interaction.client.latency * 1000)}ms**", ephemeral=True, view=PingView())

class ImportantView(View):
    def __init__(self):
        super().__init__()
        self.add_item(ImportantSelect())

class ImportantSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Terms of Service", description="Sends a link to the Terms of Service Page."),
            discord.SelectOption(label="Privacy Policy", description="Sends a link to the Privacy Policy Page."),
            discord.SelectOption(label="GitHub", description="Sends a link to the GitHub Page of the Bot."),
            discord.SelectOption(label="Discord", description="Sends a link to our Discord Server."),
            discord.SelectOption(label="Version", description="Sends Info about the current version of the Bot for feedback and stuff."),
        ]
        super().__init__(placeholder="Choose the Information you are Interested in!", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        selected_important = self.values[0]
        terms_of_service_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Velaris/blob/main/terms_of_service.md")
        privacy_policy_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Velaris/blob/main/privacy_policy.md")
        github_page_button = link_button(text="Open 📩" , link="https://github.com/VelisCore/Velaris")
        discord_join_button = link_button(text="Join 📩", link="https://discord.gg/5NDYmBVdSA")
        version_button = link_button(text="Show 📩", link="https://github.com/VelisCore/Velaris/releases/tag/v25.1.27")
        if selected_important == "Terms of Service":
            await interaction.response.send_message(f"Here you can take a look at our [Terms of Service](https://github.com/VelisCore/Velaris/blob/main/terms_of_service.md)!", view=terms_of_service_button, ephemeral=True)
        elif selected_important == "Privacy Policy":
            await interaction.response.send_message(f"Here you can take a look at our [Privacy Policy](https://github.com/VelisCore/Velaris/blob/main/privacy_policy.md)!", view=privacy_policy_button, ephemeral=True)
        elif selected_important == "GitHub":
            await interaction.response.send_message(f"You can finde the Source Code and stuff under our [GitHub Page](https://github.com/VelisCore/Velaris)!", view=github_page_button, ephemeral=True)
        elif selected_important == "Discord":
            await interaction.response.send_message(f"**A link to our [Discord Server](https://discord.gg/5NDYmBVdSA)**!", view=discord_join_button, ephemeral=True)
        elif selected_important == "Version":
            await interaction.response.send_message(f"**Current version : [v25.1.27](https://github.com/VelisCore/Velaris/releases/tag/v25.1.27)**", view=version_button ,ephemeral=True)

@app_commands.command(name="important", description="Important Links for the Discord Bot.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def important(interaction: discord.Interaction):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    await interaction.response.send_message("Select the Informations you need here.", view=ImportantView(), ephemeral=True)

@app_commands.command(name="time", description="Shows the current time in the specified timezone.")
async def time_command(interaction: discord.Interaction, location: str):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    try:
        timezone = timezone_mapping.get(location, None)
        if timezone:
            tz = pytz.timezone(timezone)
            current_time = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            await interaction.response.send_message(f"The current time in **{location}** ({timezone}) is **{current_time}**.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Unknown location: **{location}**. Please provide a valid city, country, or timezone.", ephemeral=True)
    except pytz.UnknownTimeZoneError:
        await interaction.response.send_message(f"Unknown timezone for location: **{location}**. Please provide a valid city, country, or timezone.", ephemeral=True)

@time_command.autocomplete('location')
async def location_autocomplete(interaction: discord.Interaction, current: str) -> list:
    locations = list(timezone_mapping.keys())
    return [
        app_commands.Choice(name=loc, value=loc)
        for loc in locations if current.lower() in loc.lower()
    ]

class UpTimeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        
        check_again_button = discord.ui.Button(label="Check again", style=discord.ButtonStyle.success)
        check_again_button.callback = self.check_again
        self.add_item(check_again_button)

    async def check_again(self, interaction: discord.Interaction):
        current_time = datetime.datetime.now()
        uptime_duration = current_time - start_time
        uptime_days = uptime_duration.days
        uptime_seconds = uptime_duration.seconds
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_message = f"Uptime: {uptime_days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        
        await interaction.response.edit_message(content=uptime_message, view=self)

@app_commands.command(name="uptime", description="Shows the bot's uptime.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def uptime_command(interaction: discord.Interaction):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    current_time = datetime.datetime.now()
    uptime_duration = current_time - start_time
    uptime_days = uptime_duration.days
    uptime_seconds = uptime_duration.seconds
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    uptime_message = f"Uptime: {uptime_days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
    await interaction.response.send_message(uptime_message, ephemeral=True, view=UpTimeView())


@app_commands.command(name="savefile", description="Saves a text file.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def save_file_command(interaction: discord.Interaction, content: str):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    unique_id = str(uuid.uuid4())
    file_path = os.path.join(file_storage_dir, f"{unique_id}.txt")
    with open(file_path, 'w') as file:
        file.write(content)
    text_files[unique_id] = {'file_path': file_path}
    await interaction.response.send_message(f"File saved with ID **{unique_id}**.", ephemeral=True)

@app_commands.command(name="getfile", description="Retrieves a saved text file.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def get_file_command(interaction: discord.Interaction, file_id: str):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    file_data = text_files.get(file_id, None)
    if file_data:
        file_path = file_data['file_path']
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                file_content = file.read()
            await interaction.response.send_message(f"File **{file_id}** content:\n```{file_content}```\n", ephemeral=True)
        else:
            await interaction.response.send_message(f"File **{file_id}** is no longer available.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No file found with ID **{file_id}**.", ephemeral=True)
        
@app_commands.command(name="deletefile", description="Deletes a saved text file.")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def delete_file_command(interaction: discord.Interaction, file_id: str):
    if not can_user_make_request(interaction.user.id):
        await interaction.response.send_message("You have exceeded the maximum number of requests per hour (100). Please try again later. If this issue still exists after an hour try to contact us.", ephemeral=True)
        return
    file_data = text_files.get(file_id, None)
    if file_data:
        file_path = file_data['file_path']
        if os.path.exists(file_path):
            os.remove(file_path)
            del text_files[file_id]
            await interaction.response.send_message(f"File **{file_id}** deleted successfully.", ephemeral=True)
        else:
            await interaction.response.send_message(f"File **{file_id}** is already deleted.", ephemeral=True)
    else:
        await interaction.response.send_message(f"No file found with ID **{file_id}**.", ephemeral=True)

client.tree.add_command(help_command)
client.tree.add_command(ping)
client.tree.add_command(important)
client.tree.add_command(time_command)
client.tree.add_command(uptime_command)
client.tree.add_command(save_file_command)
client.tree.add_command(get_file_command)
client.tree.add_command(delete_file_command)
client.tree.add_command(feedback)

client.run(TOKEN)
