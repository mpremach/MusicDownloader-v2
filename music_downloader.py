# Standard library imports
import os  # For working with file paths and directories

# Third-party imports
from pydub import AudioSegment  # For converting audio files to mp3
from yt_dlp import YoutubeDL  # For downloading audio from YouTube/SoundCloud
from mutagen.easyid3 import EasyID3  # For editing mp3 metadata
from mutagen.id3 import ID3, APIC, error  # For adding album art to mp3

# Setup FFmpeg/FFprobe paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Current script directory
FFMPEG_DIR = os.path.join(BASE_DIR, "ffmpeg")  # Folder containing ffmpeg.exe and ffprobe.exe

# Add FFmpeg folder to PATH so subprocess can find it
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# Tell pydub explicitly where ffmpeg and ffprobe are
AudioSegment.converter = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(FFMPEG_DIR, "ffprobe.exe")

# Setup download folder
MUSIC_FOLDER = os.path.join(os.path.expanduser("~"), "Music")  # Default music folder
DOWNLOAD_FOLDER = os.path.join(MUSIC_FOLDER, "MusicDownloader")  # Folder to save downloaded music
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # Create folder if it doesn't exist
COVERS_FOLDER = os.path.join(DOWNLOAD_FOLDER, "Covers")  # Folder to save album covers
os.makedirs(COVERS_FOLDER, exist_ok=True)  # Create folder if it doesn't exist
print(f"Download folder set to: {DOWNLOAD_FOLDER}")

# Function to download and convert audio
def download_audio():
    print("Welcome to the Music Downloader! Before proceeding please make sure you have placed any cover images you want to use in the 'Covers' folder located in the MusicDownloader folder found in Music.")
    url = input("Paste YouTube or SoundCloud URL here: ").strip()  # Ask user for URL

    ydl_opts = {
        'format': 'bestaudio/best',  # Get best quality audio
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),  # Save template (title, file type)
        'noplaylist': True,  # Only download single videos even if URL is a playlist
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)  # Download audio
        filename = ydl.prepare_filename(info)  # Get the downloaded file path
        print(f"Downloaded file: {filename}")

        mp3_filename = os.path.splitext(filename)[0] + '.mp3'  # Change file extension to .mp3
        sound = AudioSegment.from_file(filename)  # Load downloaded file
        sound.export(mp3_filename, format="mp3")  # Export as mp3
        print(f"Converted to mp3: {mp3_filename}")
        os.remove(filename)  # Remove original downloaded file
        print(f"Removed original file: {filename}")


        add_metadata(mp3_filename)  # Add metadata to mp3 file
        choose_cover(mp3_filename)  # Allow user to choose a cover for the mp3 file
            

#Function to allow for choosing a cover
def choose_cover(mp3_file):
    covers = [f for f in os.listdir(COVERS_FOLDER) 
              if os.path.isfile(os.path.join(COVERS_FOLDER, f))]
    if not covers:
        print("No covers available.")
        return None
    print("Available covers:")  # List available covers
    for i in range(len(covers)):
        print(f"{i + 1}: {covers[i]}")
        
    choice = (input("Choose the cover you would like to use corresponding to the number or click enter for no cover: ")).strip()
    if choice == "":
        print("No cover selected.")
        return None

    try: #Retreive the selected cover and add it to the mp3 file if found in covers folder
        choice_num = int(choice)
        if 1 <= choice_num <= len(covers):
            selected_cover = os.path.join(COVERS_FOLDER, covers[choice_num - 1])
            print(f"Selected cover: {covers[choice_num - 1]}")


            audio = ID3(mp3_file) # Load mp3 file for ID3 editing and then add the cover
            with open(selected_cover, 'rb') as img:
                audio['APIC'] = APIC(
                    encoding=3,
                    mime=f"image/{selected_cover.split('.')[-1].lower()}",
                    type=3,
                    data=img.read()
                )
            audio.save()
            print("Cover added to mp3 file.")
        else:
            print("Invalid number, keeping existing cover.")
    except ValueError:
        print("Invalid input, keeping existing cover.")

# Function to add metadata to mp3 file
def add_metadata(mp3_file):
    try:
        audio = EasyID3(mp3_file)  # Load mp3 file for metadata editing
    except error:
        audio = ID3()  # Create new ID3 tag if none exists
        audio.save(mp3_file)
        audio = EasyID3(mp3_file)

    # Ask user for metadata
    title = input("Enter song title or press enter for none: ").strip()
    artist = input("Enter artist name or press enter for none: ").strip()
    album = input("Enter album name or press enter for none: ").strip()
    year = input("Enter year or press enter for none: ").strip()

    # Update metadata if provided
    if title:
        audio['title'] = title
    if artist:
        audio['artist'] = artist
    if album:
        audio['album'] = album
    if year:
        audio['date'] = year

    audio.save(mp3_file, v2_version=3)  # Save changes to mp3 file
    print("Metadata added to mp3 file.")
    

# Run the download function
try:
    download_audio()
except Exception as e:
    print(f"An error occurred: {e}")
    print("It is possible a library is out of date, please contact https://github.com/mpremach for a new version if the issue persists.")
finally: #Prevent program from closing immediately
    print("\nProcess complete.")
    input("Press Enter to exit...")
