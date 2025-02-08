import discord, requests, os
from dotenv import load_dotenv
from discord.ext import commands
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN is missing in the .env file.")
if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY is missing in the .env file.")

TMDB_BASE_URL = "https://api.themoviedb.org/3/"
TMDB_ASSET_URL = "https://image.tmdb.org/t/p/w500"

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.tree.command(name="trending", description="Get the trending movies on TMDB.")
async def trending(interaction: discord.Interaction):
    try:
        movies = get_movies("trending/movie/day")
        if not movies:
            await interaction.response.send_message("No trending movies found.")
            return

        await build_and_send_message(movies, interaction)

    except ValueError as e:
        await interaction.response.send_message(f"Error: {e}")


@bot.tree.command(name="upcoming", description="Get a list of movies that are being released soon.")
async def upcoming(interaction: discord.Interaction):
    try:
        movies = get_movies("movie/upcoming")
        if not movies:
            await interaction.response.send_message("No upcoming movies found.")
            return

        await build_and_send_message(movies, interaction)

    except ValueError as e:
        await interaction.response.send_message(f"Error: {e}")


@bot.tree.command(name="nowplaying", description="Get a list of movies that are currently in theatres.")
async def nowplaying(interaction: discord.Interaction):
    try:
        movies = get_movies("movie/now_playing")
        if not movies:
            await interaction.response.send_message("No now-playing movies found.")
            return

        await build_and_send_message(movies, interaction)

    except ValueError as e:
        await interaction.response.send_message(f"Error: {e}")


@bot.tree.command(name="popular", description="Get a list of movies ordered by popularity.")
async def popular(interaction: discord.Interaction):
    try:
        movies = get_movies("movie/popular")
        if not movies:
            await interaction.response.send_message("No popular movies found.")
            return

        await build_and_send_message(movies, interaction)

    except ValueError as e:
        await interaction.response.send_message(f"Error: {e}")


@bot.tree.command(name="toprated", description="Get a list of movies ordered by rating.")
async def toprated(interaction: discord.Interaction):
    try:
        movies = get_movies("movie/top_rated")
        if not movies:
            await interaction.response.send_message("No top-rated movies found.")
            return

        await build_and_send_message(movies, interaction)

    except ValueError as e:
        await interaction.response.send_message(f"Error: {e}")


# Event to sync commands with Discord
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands with Discord.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    print(f"We have logged in as {bot.user}")

async def build_and_send_message(movies: dict, interaction):
    await interaction.response.defer()

    now = format_current_datetime_with_suffix()

    file_path = "assets/tmdb-logo.png"  # Adjust path based on your Docker setup

    # Send a separate message for each movie
    for movie in movies:
        file = discord.File(file_path, filename="tmdb-logo.png")

        embed = discord.Embed(
            title=movie["title"],
            description=movie["overview"],
            color=discord.Color.blue()
        )

        embed.add_field(
            name="More Info",
            value=f"[TMDB](https://www.themoviedb.org/movie/{movie['id']})",
            inline=True
        )

        embed.add_field(name="Release Date", value=f"{movie["release_date"]}", inline=True)
        embed.add_field(name="Genre", value=movie['genres'], inline=True)
        embed.add_field(name="Popularity", value=f"{movie["popularity"]}", inline=True)
        embed.set_image(url=f"{TMDB_ASSET_URL}{movie['backdrop_path']}")
        embed.set_thumbnail(url=f"{TMDB_ASSET_URL}{movie['poster_path']}")

        embed.set_footer(
            text=f"Fetched from The Movie Database (TMDB): {now}",
            icon_url="attachment://tmdb-logo.png"
        )

        await interaction.followup.send(embed=embed, file=file)

def get_movies(endpoint: str) -> dict:
    try:
        headers = {"accept": "application/json"}
        parameters = {"language": "en-US", "include_adult": "false", "api_key": TMDB_API_KEY}
        response = requests.get(TMDB_BASE_URL + endpoint, headers=headers, params=parameters, timeout=10)

        response.raise_for_status()  # Raise HTTPError for bad responses

        if response.status_code == 200:
            movies = response.json().get("results", [])

            return [
                {
                    "id": movie["id"],
                    "backdrop_path": movie["backdrop_path"],
                    "poster_path": movie["poster_path"],
                    "title": movie["title"],
                    "overview": movie["overview"],
                    "popularity": movie["popularity"],
                    "release_date": format_release_date(movie["release_date"]),
                    "genres": get_genre_names(movie["genre_ids"])
                }
                for movie in movies[:10]
            ]
        else:
            print("Error:", response.status_code, response.text)

    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch data: {e}") from e


def get_genre_names(genre_ids):
    genre_data = {
        "genres": [
            {"id": 28, "name": "Action"},
            {"id": 12, "name": "Adventure"},
            {"id": 16, "name": "Animation"},
            {"id": 35, "name": "Comedy"},
            {"id": 80, "name": "Crime"},
            {"id": 99, "name": "Documentary"},
            {"id": 18, "name": "Drama"},
            {"id": 10751, "name": "Family"},
            {"id": 14, "name": "Fantasy"},
            {"id": 36, "name": "History"},
            {"id": 27, "name": "Horror"},
            {"id": 10402, "name": "Music"},
            {"id": 9648, "name": "Mystery"},
            {"id": 10749, "name": "Romance"},
            {"id": 878, "name": "Science Fiction"},
            {"id": 10770, "name": "TV Movie"},
            {"id": 53, "name": "Thriller"},
            {"id": 10752, "name": "War"},
            {"id": 37, "name": "Western"}
        ]
    }

    # Create a dictionary mapping genre IDs to their names
    genre_dict = {genre['id']: genre['name'] for genre in genre_data['genres']}

    # If genre_ids is a list (multiple genres), return a list of names
    if isinstance(genre_ids, list):
            return ', '.join([genre_dict.get(genre_id, "Unknown Genre") for genre_id in genre_ids])

    # If it's a single genre ID, return the corresponding name
    return genre_dict.get(genre_ids, "Unknown Genre")


def format_release_date(date: str) -> str:
    parsed_date = datetime.strptime(date, "%Y-%m-%d")

    return parsed_date.strftime("%B %d, %Y")


def format_current_datetime_with_suffix() -> str:
    timezone = ZoneInfo("America/New_York")
    now = datetime.now(tz=timezone)

    # Determine the ordinal suffix
    day = now.day
    if 11 <= day <= 13:  # Special case for teens
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # Format the date
    return now.strftime(f"%A, %B {day}{suffix}, %Y at %I:%M:%S %p %Z")


# Run the bot
bot.run(DISCORD_TOKEN)