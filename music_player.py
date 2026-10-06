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
        self.seek_offset = 0  # detik posisi terakhir kali play()/seek() dipanggil
        self.initialize_sql()

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
            Path TEXT UNIQUE
        )
        """)
        conn.commit()
        conn.close()

    def add_song(self, music_file):
        path = os.path.abspath(music_file)

        if not os.path.isfile(path):
            raise FileNotFoundError(f"Music file '{path}' not found.")
        try:
            audio = mutagen.File(path, easy=True)
            if audio is None:
                raise ValueError(f"File '{path}' tidak dikenali.")
            if audio.tags is None:

                title_ext = os.path.basename(path)
                title, ext = os.path.splitext(title_ext)
                artist = "Unknown Artist"

            else:
                tags = audio.tags
                if 'title' in tags and tags['title']:
                    title = tags['title'][0]
                else:
                    title = os.path.splitext(os.path.basename(path))[0]
                if 'artist' in tags and tags['artist']:
                    artist = tags['artist'][0]
                else:
                   artist = "Unknown Artist"

        except mutagen.MutagenError as e:
            raise ValueError(f"File '{path}' tidak dapat dibaca.") from e

        conn = sqlite3.connect("Musikku.db")
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO laguku (Title,Artist,Path,Favorit) VALUES(?, ?, ?, 0)", (title, artist, path))

            song_id = cur.lastrowid
            conn.commit()
            self.playlist.append((song_id, path))
            return "Musik Berhasil dimasukkan"
        except sqlite3.IntegrityError as e:
            raise ValueError("Lagu dengan path ini sudah ada di database.") from e

        finally:
            conn.close()

    def load_from_db(self):
        conn = sqlite3.connect("Musikku.db")
        cur = conn.cursor()

        cur.execute("SELECT ID,Path FROM laguku")

        row = cur.fetchall()
        self.playlist = []
        for ID, Path in row:
            if Path and os.path.exists(Path):
                self.playlist.append((ID, Path))
            else:
                continue

        conn.close()

    def get_all_songs(self):
        """Ambil semua lagu lengkap (ID, Title, Artist, Path, Favorit), buat ditampilkan di UI."""
        conn = sqlite3.connect("Musikku.db")
        try:
            cur = conn.cursor()
            cur.execute("SELECT ID, Title, Artist, Path, Favorit FROM laguku ORDER BY Title ASC")
            return cur.fetchall()
        finally:
            conn.close()

    def toggle_favorite(self, id_lagu):
        """Balik status favorit (0 jadi 1, atau sebaliknya) untuk satu lagu. Return nilai baru, atau None kalau lagu tidak ketemu."""
        conn = sqlite3.connect("Musikku.db")
        try:
            cur = conn.cursor()
            cur.execute("SELECT Favorit FROM laguku WHERE ID = ?", (id_lagu,))
            row = cur.fetchone()
            if row is None:
                return None
            current = row[0] or 0
            new_value = 0 if current == 1 else 1
            cur.execute("UPDATE laguku SET Favorit = ? WHERE ID = ?", (new_value, id_lagu))
            conn.commit()
            return new_value
        finally:
            conn.close()

    def play(self, index):
        if 0 <= index < len(self.playlist):
               self.index = index
               pygame.mixer.music.load(self.playlist[index][1])
               pygame.mixer.music.play()
               self.seek_offset = 0
        else:
             return "Index tidak valid"

    def pause(self):
        pygame.mixer.music.pause()

    def resume(self):
        pygame.mixer.music.unpause()

    def stop(self):
        pygame.mixer.music.stop()

    def replay(self):
        pygame.mixer.music.rewind()

    def seek(self, seconds):
        """Lompat ke posisi tertentu (dalam detik) di lagu yang sedang dimuat.
        Catatan: tidak semua format didukung pygame untuk seek (umumnya MP3/OGG aman)."""
        if seconds < 0:
            seconds = 0
        pygame.mixer.music.play(start=seconds)
        self.seek_offset = seconds

    def volume(self, volume):
        pygame.mixer.music.set_volume(volume)

    def duration_audio(self, index):

        audio = mutagen.File(self.playlist[index][1])

        if audio is None:
            print("Unsupported or corrupted file format")
            return

        audio_info = audio.info
        length_audio = audio_info.length

        return length_audio

    def progress_bar(self):
        if pygame.mixer.music.get_busy():
            duration = self.duration_audio(self.index)
            if duration is None or duration == 0:
                return 0
            current_position = (pygame.mixer.music.get_pos() // 1000) + self.seek_offset
            current_position = min(current_position, duration)  # jaga-jaga jangan sampai lewat 100%
            return (current_position / duration) * 100
        return 0

    def next_song(self):
        self.index += 1

        if self.index >= len(self.playlist):
            self.index = 0

        self.play(self.index)

    def previous_song(self):
        self.index -= 1

        if self.index < 0:
            self.index = len(self.playlist) - 1

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

    def delete_song(self, id_lagu, pilihan):

        conn = sqlite3.connect("Musikku.db")
        try:
            cur = conn.cursor()

            cur.execute("SELECT Path FROM laguku WHERE ID = ?", (id_lagu,))
            row = cur.fetchone()

            if row is None or len(row) == 0:
                return "Gagal: lagu tidak ditemukan!"

            path = row[0]

            cur.execute("DELETE FROM laguku WHERE ID = ?", (id_lagu,))
            if cur.rowcount == 0:
                return "Gagal: lagu tidak ditemukan!"

            conn.commit()
        finally:
            conn.close()

        self.playlist = [item for item in self.playlist if item[1] != path]

        if pilihan == 1:
            return "Lagu Berhasil di hapus"

        elif pilihan == 2:
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