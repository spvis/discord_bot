import discord
from discord.ext import commands
import webserver
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Intents required for member roles and message content
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Replace these with your actual channel IDs and role name
INTRO_CHANNEL_ID = 1387811472863920258  # <-- Your #introductions channel ID
LOG_CHANNEL_ID = 1390683642078036089  # <-- Your #log channel ID
VERIFIED_ROLE_NAME = "Verified"


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    
    # Set a stupid custom status
    await bot.change_presence(activity=discord.Game(name="something idfk"))
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


@bot.tree.command(name="hello", description="Say hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")


@bot.event
async def on_member_join(member):
    # Get the introductions channel
    intro_channel = member.guild.get_channel(INTRO_CHANNEL_ID)
    if intro_channel:
        # Send a welcome message tagging the new member
        await intro_channel.send(
            f"👋 Welcome to the server, {member.mention}! "
            f"Please introduce yourself here to get verified and gain access to the rest of the server."
        )
        print(f"Welcomed new member: {member}")


@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author.bot:
        return

    # Check if the message is in the introductions channel
    if message.channel.id == INTRO_CHANNEL_ID:
        guild = message.guild
        member = message.author

        # Give the Verified role if they don't already have it
        role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        if role and role not in member.roles:
            await member.add_roles(role)
            print(f"Gave {member} the Verified role.")

        # Forward the message to the log channel
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="📥 New Introduction",
                                  description=message.content,
                                  color=discord.Color.blue())
            embed.set_author(name=str(member),
                             icon_url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id}")
            await log_channel.send(embed=embed)

    await bot.process_commands(message)


# Simple HTTP handler for health checks
class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')

    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


# Start HTTP server in a separate thread
def start_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
    server.serve_forever()


# Start the HTTP server
threading.Thread(target=start_server, daemon=True).start()
print("HTTP server started on port 8080")

bot_token = os.environ["DISCORD_BOT_TOKEN"]
webserver.keep_alive()
bot.run(bot_token)
