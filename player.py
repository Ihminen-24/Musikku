import os
import sqlite3

import mutagen
import pygame
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wave import WAVE


class MusicPlayer():

    def __init__(self):
        pygame.mixer.init()
        self.playlist = []
        self.index = 0

    def initialize_sql(self):
        conn = sqlite3.connect("Musikku.db")
        cur = conn.cursor()
        cur.execute(""" CREATE TABLE IF NOT EXISTS laguku (

            ID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            Title TEXT,
            Artist TEXT,
            Album TEXT,
            Duration TEXT,
            Favorit INTEGER,
            Path TEXT
        )
        """)
        conn.commit()
        conn.close()

    def add_song(self, music_file):
        if os.path.exists(music_file):
            self.playlist.append(music_file)
        else:
            raise FileNotFoundError(f"Music file '{music_file}' not found.")

        audio = mutagen.File(music_file, easy=True)
        if audio is None or audio.tags is None:
            raise ValueError(f"File '{music_file}' tidak memiliki metadata yang bisa dibaca.")

        tags = audio.tags
        title = tags['title'][0] if 'title' in tags else os.path.splitext(os.path.basename(music_file))[0]
        artist = tags['artist'][0] if 'artist' in tags else "Unknown Artist"
        path = music_file
        conn = sqlite3.connect("Musikku.db")
        cur = conn.cursor()
        try:
            cur.execute("SELECT ID FROM laguku WHERE Title = ?", (title,))
            if cur.fetchone():
                return "Gagal Masukkan lagu"

            cur.execute("INSERT INTO laguku (Title,Artist,Path) VALUES(?, ?, ?)", (title, artist,path))
            conn.commit()
            return "Musik Berhasil dimasukkan"
        finally:
            conn.close()




    def play(self, index):
        pygame.mixer.music.load(self.playlist[index])
        pygame.mixer.music.play()

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()

    def replay(self):
        pygame.mixer.music.rewind()

    def volume(self, volume):
        pygame.mixer.music.set_volume(volume)


    def duration_audio(self,index):
        audio=mutagen.File(self.playlist[index])

        if audio is None:
            print("Unsupported or corrupted file format")
            return

        audio_info = audio.info
        length_audio = audio_info.length

        return length_audio



    def progress_bar(self):
        if pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            duration = self.duration_audio(self.index)
            if duration is None:
                return 0
            current_position = pygame.mixer.music.get_pos() // 1000
            return (current_position / duration) * 100
        return 0



    def next_song(self):
        self.index += 1

        if self.index >= len(self.playlist):
            self.index=0

        self.play(self.index)

    def previous_song(self):
        self.index -= 1

        if self.index < 0:
            self.index = len(self.playlist)-1

        self.play(self.index)

    def search(self, kata_kunci):
        conn = sqlite3.connect("Musikku.db")
        try:
            cur = conn.cursor()
            keyword = f"%{kata_kunci}%"
            cur.execute(
                "SELECT ID, Title, Artist FROM laguku WHERE Title LIKE ? OR Artist LIKE ? ORDER BY Title ASC",
                (keyword, keyword)
            )
            return cur.fetchall()
        except sqlite3.Error as e:
            print(f"Terjadi error saat mencari: {e}")
            return []
        finally:
            conn.close()

    def delete_song(self,id_lagu,pilihan):

        if pilihan == 1:
            
            conn = sqlite3.connect("Musikku.db")
            cur = conn.cursor()
            
            cur.execute("SELECT Path FROM laguku WHERE ID = ?",(id_lagu,))

            row = cur.fetchone()

            if row is not None and len(row) > 0:
                path = row[0]
            else:
                return "Gagal: lagu tidak ditemukan!"


 
            cur.execute("DELETE FROM laguku WHERE ID = ?",(id_lagu,))
            if cur.rowcount == 0:
                    conn.close()
                    return "Gagal: lagu tidak ditemukan!"

            
            conn.commit()
            conn.close()

            if path in self.playlist:
                self.playlist.remove(path)
            
            return "Lagu Berhasil di hapus"

        elif pilihan == 2:

            conn = sqlite3.connect("Musikku.db")
            cur = conn.cursor()

            cur.execute("SELECT Path FROM laguku WHERE ID = ?", (id_lagu,))

            row = cur.fetchone()

            if row is not None and len(row) > 0:
                path = row[0]
            else:
                 return "Gagal: lagu tidak ditemukan!"

            cur.execute("DELETE FROM laguku WHERE ID = ?",(id_lagu,))
            if cur.rowcount == 0:
                    conn.close()
                    return "Gagal: lagu tidak ditemukan!"

            conn.commit()
            conn.close()

            if path in self.playlist:
                self.playlist.remove(path)

            try:
                if not os.path.exists(path):
                    return f"Error: File '{path}' does not exist."

                if not os.path.isfile(path):
                    return f"Error: '{path}' is not a file."

                os.remove(path)
                return f"File '{path}' deleted successfully."

            except PermissionError:
                    return f"Error: Permission denied to delete '{path}'."
            except OSError as e:
                    return f"Error: {e.strerror} - '{path}'"

                   

            
            

            





player = MusicPlayer()

player.initialize_sql()

player.add_song("Music/Hivi-Pelangi.mp3")

print(player.playlist)

player.play(0)

input("Tekan Enter untuk menghentikan program...")
