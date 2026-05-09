# Standard library imports
import os  # For working with file paths and directories
import threading  # For running the download process in a separate thread

# Third-party imports
from pydub import AudioSegment  # For converting audio files to mp3
from yt_dlp import YoutubeDL  # For downloading audio from YouTube/SoundCloud
from mutagen.easyid3 import EasyID3  # For editing mp3 metadata
from mutagen.id3 import ID3, APIC, error  # For adding album art to mp3
import customtkinter as ctk  # For creating the GUI
from PIL import Image  # For handling album cover images

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
    status_label.configure(text="Downloading... (Check console for progress)", text_color="orange")
    url = url_entry.get().strip()  # Get URL from entry field


    ydl_opts = {
        'format': 'bestaudio/best',  # Get best quality audio
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),  # Save template (title, file type)
        'noplaylist': True,  # Only download single videos even if URL is a playlist
    }

    try:
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
            status_label.configure(text="Process Complete! Ready for next URL.", text_color="green")
            print("\nProcess complete.")
    except Exception as e:
        status_label.configure(text=f"Error: {str(e)[:60]}", text_color="red")
        print(f"An error occurred: {e}")
    finally:
        download_btn.configure(state='normal')  # Re-enable the download button after process is complete
            

#Function to allow for choosing a cover
def choose_cover(mp3_file):
    choice = cover_dropdown.get()  # Get the selected cover from the dropdown

    if choice == "None" or choice == "":
        print("No cover selected.")
        return

    try: #Retreive the selected cover and add it to the mp3 file if found in covers folder
        selected_cover = os.path.join(COVERS_FOLDER, choice)
        print(f"Selected cover: {choice}")

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
    except Exception as e:
        print("Error adding cover: {e}")

# Function to add metadata to mp3 file
def add_metadata(mp3_file):
    try:
        audio = EasyID3(mp3_file)  # Load mp3 file for metadata editing
    except error:
        audio = ID3()  # Create new ID3 tag if none exists
        audio.save(mp3_file)
        audio = EasyID3(mp3_file)

    # Metadata input from user
    title = title_entry.get().strip()
    artist = artist_entry.get().strip()
    album = album_entry.get().strip()
    year = year_entry.get().strip()


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


def start_download_thread():
    download_btn.configure(state='disabled')  # Disable the download button to prevent multiple clicks
    threading.Thread(target=download_audio,  daemon=True).start()  # Start the download process in a separate thread

    
# Function to update the image preview on the screen
def update_cover_preview(choice):
    if choice == "None" or choice == "":
        cover_preview_label.configure(image="", text="No Cover\nSelected")
        return
    
    try:
        img_path = os.path.join(COVERS_FOLDER, choice)
        img = Image.open(img_path)
        
        # Create a CustomTkinter image and scale it to a square
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(360, 360))
        
        # Put the image on the label and hide placeholder text
        cover_preview_label.configure(image=ctk_img, text="")
    except Exception as e:
        cover_preview_label.configure(image="", text="Error loading\nimage")
        print(f"Preview error: {e}")


# GUI Setup
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("Music Downloader v2")
app.geometry("550x800") 

# Header & URL 
ctk.CTkLabel(app, text="🎵 Music Downloader", font=("Arial", 22, "bold")).pack(pady=(20, 10))
url_entry = ctk.CTkEntry(app, width=450, height=35, placeholder_text="Paste YouTube or SoundCloud URL here...")
url_entry.pack(pady=(0, 20))

#  Metadata Card 
meta_frame = ctk.CTkFrame(app, corner_radius=10)
meta_frame.pack(pady=10, padx=25, fill="x")

ctk.CTkLabel(meta_frame, text="Metadata (Optional)", font=("Arial", 14, "bold")).pack(pady=(10, 5))

grid_frame = ctk.CTkFrame(meta_frame, fg_color="transparent")
grid_frame.pack(pady=(0, 10))

title_entry = ctk.CTkEntry(grid_frame, width=220, placeholder_text="Song Title")
title_entry.grid(row=0, column=0, padx=10, pady=10)

artist_entry = ctk.CTkEntry(grid_frame, width=220, placeholder_text="Artist Name")
artist_entry.grid(row=0, column=1, padx=10, pady=10)

album_entry = ctk.CTkEntry(grid_frame, width=220, placeholder_text="Album Name")
album_entry.grid(row=1, column=0, padx=10, pady=10)

year_entry = ctk.CTkEntry(grid_frame, width=220, placeholder_text="Year")
year_entry.grid(row=1, column=1, padx=10, pady=10)

# Cover Art & Download Button
cover_frame = ctk.CTkFrame(app, fg_color="transparent")
cover_frame.pack(pady=15, fill="x", padx=25)

# Cover Art Preview
cover_preview_label = ctk.CTkLabel(cover_frame, text="No Cover\nSelected", width=360, height=360, fg_color="gray", corner_radius=10)
cover_preview_label.pack(padx=(0, 10))

# Dropdown Label & Menu
ctk.CTkLabel(cover_frame, text="Cover Art:", font=("Arial", 12, "bold")).pack(padx=(0, 10))

available_covers = ["None"] + [f for f in os.listdir(COVERS_FOLDER) if os.path.isfile(os.path.join(COVERS_FOLDER, f))]
cover_dropdown = ctk.CTkOptionMenu(cover_frame, values=available_covers, command=update_cover_preview, width=200)
cover_dropdown.pack(pady=(15, 0))

# Action Button
download_btn = ctk.CTkButton(cover_frame, text="Download & Convert", command=start_download_thread, height=40, font=("Arial", 12, "bold"))
download_btn.pack(pady=(15,0))

# Status Label 
status_label = ctk.CTkLabel(app, text="Ready", text_color="gray", font=("Arial", 12))
status_label.pack(pady=(10, 0))

if __name__ == "__main__":
    app.mainloop()