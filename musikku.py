import sys
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

import customtkinter as ctk

from music_player import MusicPlayer

try:
    import pywinstyles  # cuma dipakai buat efek blur acrylic di Windows
except ImportError:
    pywinstyles = None

customtkinter_appearance = "Dark"  # dikunci ke Dark dulu, toggle light/dark lagi bermasalah
customtkinter_theme = "blue"

ctk.set_appearance_mode(customtkinter_appearance)
ctk.set_default_color_theme(customtkinter_theme)


def format_time(seconds):
    if seconds is None:
        seconds = 0
    seconds = int(seconds)
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"


class MusicPlayerApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.player = MusicPlayer()
        self.player.load_from_db()

        self.title("Musikku")
        self.geometry("480x640")
        self.minsize(380, 520)
        self._apply_blur_effect()

        self.song_rows = {}       # id_lagu -> frame row, buat update cepat tanpa rebuild semua
        self.current_song_id = None
        self.is_playing = False
        self.is_seeking = False   # True selagi user lagi nge-drag slider progress
        self.songs_cache = []     # hasil get_all_songs() yang lagi ditampilkan

        self._build_top_bar()
        self._build_song_list()
        self._build_player_bar()

        self.refresh_song_list()
        self._update_loop()

    def _apply_blur_effect(self):
        """Efek blur ala Windows 11 (acrylic) di background window.
        Cuma jalan di Windows, butuh 'pip install pywinstyles'.
        Di OS lain atau kalau library belum terpasang, window tetap jalan normal tanpa blur."""
        if pywinstyles is None:
            print("[info] pywinstyles belum terpasang, blur dilewati. Install: pip install pywinstyles")
            return
        if not sys.platform.startswith("win"):
            print("[info] Blur effect cuma didukung di Windows, dilewati di OS ini.")
            return
        try:
            pywinstyles.apply_style(self, "acrylic")
        except Exception as e:
            print(f"[info] Gagal apply efek blur: {e}")

    # ---------- UI: bagian atas (search + tambah lagu) ----------

    def _build_top_bar(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 8))

        self.search_entry = ctk.CTkEntry(top, placeholder_text="Cari judul atau artis...")
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_song_list())

        add_btn = ctk.CTkButton(top, text="+ Tambah", width=90, command=self.add_song_dialog)
        add_btn.pack(side="left", padx=(0, 8))

        # Tombol toggle tema disembunyikan sementara, soalnya light mode masih berantakan.
        # Tinggal un-comment 2 baris di bawah ini kalau udah mau diaktifin lagi.
        # theme_btn = ctk.CTkButton(top, text="🌓", width=36, command=self._toggle_theme)
        # theme_btn.pack(side="left")

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        # kasih jeda dikit biar window sempat gambar ulang pakai warna baru,
        # baru efek blur di-apply ulang biar nggak glitch/berantakan
        self.after(50, self._apply_blur_effect)

    # ---------- UI: daftar lagu ----------

    def _build_song_list(self):
        self.song_list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.song_list_frame.pack(fill="both", expand=True, padx=16, pady=8)

    def refresh_song_list(self):
        keyword = self.search_entry.get().strip().lower()

        all_songs = self.player.get_all_songs()
        if keyword:
            all_songs = [
                s for s in all_songs
                if keyword in s[1].lower() or keyword in s[2].lower()
            ]

        self.songs_cache = all_songs

        for child in self.song_list_frame.winfo_children():
            child.destroy()
        self.song_rows = {}

        if not all_songs:
            empty_label = ctk.CTkLabel(self.song_list_frame, text="Belum ada lagu. Klik '+ Tambah' buat mulai.")
            empty_label.pack(pady=20)
            return

        for song_id, title, artist, path, favorit in all_songs:
            self._add_song_row(song_id, title, artist, favorit)

    def _add_song_row(self, song_id, title, artist, favorit):
        row = ctk.CTkFrame(self.song_list_frame, corner_radius=8)
        row.pack(fill="x", pady=4)

        is_current = (song_id == self.current_song_id)
        label_color = ("#1f6aa5", "#4aa3ff") if is_current else None

        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, padx=(10, 4), pady=8)

        title_label = ctk.CTkLabel(
            text_frame, text=title, anchor="w", font=ctk.CTkFont(weight="bold"),
            text_color=label_color
        )
        title_label.pack(fill="x")

        artist_label = ctk.CTkLabel(text_frame, text=artist, anchor="w", text_color=("gray40", "gray65"))
        artist_label.pack(fill="x")

        # klik judul/artist buat langsung play lagu itu
        for widget in (text_frame, title_label, artist_label):
            widget.bind("<Button-1>", lambda e, sid=song_id: self.play_song_by_id(sid))

        fav_symbol = "♥" if favorit == 1 else "♡"
        fav_btn = ctk.CTkButton(
            row, text=fav_symbol, width=32, fg_color="transparent",
            text_color=("#d6336c", "#ff6b9d") if favorit == 1 else ("gray50", "gray60"),
            hover_color=("gray85", "gray25"),
            command=lambda sid=song_id: self.toggle_favorite_ui(sid)
        )
        fav_btn.pack(side="left", padx=2)

        del_btn = ctk.CTkButton(
            row, text="🗑", width=32, fg_color="transparent",
            text_color=("gray50", "gray60"), hover_color=("gray85", "gray25"),
            command=lambda sid=song_id, t=title: self.delete_song_ui(sid, t)
        )
        del_btn.pack(side="left", padx=(2, 10))

        self.song_rows[song_id] = row

    def toggle_favorite_ui(self, song_id):
        self.player.toggle_favorite(song_id)
        self.refresh_song_list()

    def delete_song_ui(self, song_id, title):
        pilihan = self._confirm_delete_dialog(title)
        if pilihan is None:
            return
        pesan = self.player.delete_song(song_id, pilihan)
        self.refresh_song_list()
        if pesan:
            messagebox.showinfo("Hapus lagu", pesan)

    def _confirm_delete_dialog(self, title):
        """Dialog konfirmasi custom dengan 3 tombol bertulisan sendiri.
        Return 1 (hapus dari playlist saja), 2 (hapus + file asli), atau None (batal)."""
        result = {"pilihan": None}

        dialog = ctk.CTkToplevel(self)
        dialog.title("Hapus lagu")
        dialog.geometry("360x200")
        dialog.resizable(False, False)
        dialog.transient(self)   # nempel di atas window utama
        dialog.grab_set()        # modal, window utama nggak bisa diklik selagi dialog ini kebuka

        label = ctk.CTkLabel(
            dialog, text=f"Hapus '{title}' dari mana?",
            font=ctk.CTkFont(weight="bold"), wraplength=320
        )
        label.pack(pady=(20, 16), padx=16)

        def pilih(nilai):
            result["pilihan"] = nilai
            dialog.destroy()

        btn_playlist = ctk.CTkButton(
            dialog, text="Hapus Dari Playlist", command=lambda: pilih(1)
        )
        btn_playlist.pack(fill="x", padx=24, pady=4)

        btn_permanen = ctk.CTkButton(
            dialog, text="Hapus Permanen (termasuk file)",
            fg_color="#c0392b", hover_color="#962d22",
            command=lambda: pilih(2)
        )
        btn_permanen.pack(fill="x", padx=24, pady=4)

        btn_batal = ctk.CTkButton(
            dialog, text="Batal", fg_color="transparent",
            border_width=1, command=lambda: pilih(None)
        )
        btn_batal.pack(fill="x", padx=24, pady=(4, 16))

        # Posisikan dialog di tengah window utama
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 180
        y = self.winfo_y() + (self.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")

        dialog.wait_window()   # tunggu sampai dialog ditutup sebelum lanjut
        return result["pilihan"]

    # ---------- UI: tambah lagu ----------

    def add_song_dialog(self):
        filetypes = [("File audio", "*.mp3 *.flac *.wav *.m4a"), ("Semua file", "*.*")]
        paths = filedialog.askopenfilenames(title="Pilih file musik", filetypes=filetypes)
        if not paths:
            return

        gagal = []
        for p in paths:
            try:
                self.player.add_song(p)
            except (FileNotFoundError, ValueError) as e:
                gagal.append(str(e))

        self.refresh_song_list()
        if gagal:
            messagebox.showwarning("Sebagian gagal ditambahkan", "\n".join(gagal))

    # ---------- UI: kontrol player ----------

    def _build_player_bar(self):
        bar = ctk.CTkFrame(self, corner_radius=12)
        bar.pack(fill="x", padx=16, pady=16)

        self.now_playing_label = ctk.CTkLabel(bar, text="Belum ada lagu diputar", font=ctk.CTkFont(weight="bold"))
        self.now_playing_label.pack(pady=(12, 4))

        progress_row = ctk.CTkFrame(bar, fg_color="transparent")
        progress_row.pack(fill="x", padx=16)

        self.time_now_label = ctk.CTkLabel(progress_row, text="0:00", width=40)
        self.time_now_label.pack(side="left")

        self.progress_slider = ctk.CTkSlider(
            progress_row, from_=0, to=1, command=self._on_seek_drag
        )
        self.progress_slider.set(0)
        self.progress_slider.pack(side="left", fill="x", expand=True, padx=8)
        self.progress_slider.bind("<ButtonRelease-1>", self._on_seek_release)

        self.time_total_label = ctk.CTkLabel(progress_row, text="0:00", width=40)
        self.time_total_label.pack(side="left")

        controls_row = ctk.CTkFrame(bar, fg_color="transparent")
        controls_row.pack(pady=12)

        prev_btn = ctk.CTkButton(controls_row, text="⏮", width=44, command=self.prev_song_ui)
        prev_btn.grid(row=0, column=0, padx=6)

        self.play_pause_btn = ctk.CTkButton(controls_row, text="▶", width=52, command=self.toggle_play_pause)
        self.play_pause_btn.grid(row=0, column=1, padx=6)

        next_btn = ctk.CTkButton(controls_row, text="⏭", width=44, command=self.next_song_ui)
        next_btn.grid(row=0, column=2, padx=6)

        volume_row = ctk.CTkFrame(bar, fg_color="transparent")
        volume_row.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(volume_row, text="🔈", width=20).pack(side="left")
        self.volume_slider = ctk.CTkSlider(volume_row, from_=0, to=1, command=self._on_volume_change)
        self.volume_slider.set(0.5)
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=8)
        self.player.volume(0.5)

    def _on_volume_change(self, value):
        self.player.volume(float(value))

    def _on_seek_drag(self, value):
        """Dipanggil terus-menerus selagi slider di-klik/digeser. Cuma update label waktu,
        belum beneran mindahin posisi lagu (itu baru kejadian pas tombol mouse dilepas)."""
        self.is_seeking = True
        if self.current_song_id is None:
            return
        duration = self.player.duration_audio(self.player.index) or 0
        current_seconds = float(value) * duration
        self.time_now_label.configure(text=format_time(current_seconds))

    def _on_seek_release(self, event):
        """Dipanggil pas tombol mouse dilepas dari slider. Di sinilah lagu beneran dipindah posisinya."""
        if self.current_song_id is not None:
            duration = self.player.duration_audio(self.player.index) or 0
            seconds = self.progress_slider.get() * duration
            self.player.seek(seconds)
            self.is_playing = True
            self._update_play_pause_icon()
        self.is_seeking = False

    def play_song_by_id(self, song_id):
        for i, (sid, path) in enumerate(self.player.playlist):
            if sid == song_id:
                self.player.play(i)
                self.current_song_id = song_id
                self.is_playing = True
                self._update_now_playing()
                self.refresh_song_list()
                return

    def toggle_play_pause(self):
        if self.current_song_id is None:
            if self.player.playlist:
                self.play_song_by_id(self.player.playlist[0][0])
            return

        if self.is_playing:
            self.player.pause()
            self.is_playing = False
        else:
            self.player.resume()
            self.is_playing = True
        self._update_play_pause_icon()

    def next_song_ui(self):
        if not self.player.playlist:
            return
        self.player.next_song()
        self.current_song_id = self.player.playlist[self.player.index][0]
        self.is_playing = True
        self._update_now_playing()
        self.refresh_song_list()

    def prev_song_ui(self):
        if not self.player.playlist:
            return
        self.player.previous_song()
        self.current_song_id = self.player.playlist[self.player.index][0]
        self.is_playing = True
        self._update_now_playing()
        self.refresh_song_list()

    def _update_play_pause_icon(self):
        self.play_pause_btn.configure(text="⏸" if self.is_playing else "▶")

    def _update_now_playing(self):
        for sid, title, artist, path, favorit in self.songs_cache:
            if sid == self.current_song_id:
                self.now_playing_label.configure(text=f"{title} — {artist}")
                break
        self._update_play_pause_icon()

    # ---------- loop update progress bar ----------

    def _update_loop(self):
        if self.current_song_id is not None and not self.is_seeking:
            percent = self.player.progress_bar()
            self.progress_slider.set(percent / 100)

            duration = self.player.duration_audio(self.player.index) or 0
            current_seconds = (percent / 100) * duration if duration else 0
            self.time_now_label.configure(text=format_time(current_seconds))
            self.time_total_label.configure(text=format_time(duration))

            import pygame
            if self.is_playing and not pygame.mixer.music.get_busy():
                # lagu abis, otomatis next
                self.next_song_ui()

        self.after(500, self._update_loop)


if __name__ == "__main__":
    app = MusicPlayerApp()
    app.mainloop()