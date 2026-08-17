import time
import pygame
import mutagen
import os

class MusicPlayer():

    def __init__(self):
        pygame.mixer.init()
        self.playlist = []

    def add_song(self, music_file): # Method menerima data dari luar memalui parameter
        # Python memvalidasi apakah path/file yang ditunjuk oleh parameter music_file memang ada di file system
        if os.path.exists(music_file): # jika python cek dan ada path dalam systemfile
            self.playlist.append(music_file) # maka masukkan file ke playlist
        else: # jika tidak ada dalam filesystem
            raise FileNotFoundError (f"Music file '{music_file}' not found.") # menghentikan proses dan munculkan FileNotFoundError



    def play(self, index):
        pygame.mixer.music.load(self.playlist[index])
        pygame.mixer.music.play()

    def pause():
        pygame.mixer.music.pause()

    def resume():
        pygame.mixer.music.unpause()
