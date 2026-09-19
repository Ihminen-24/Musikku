import customtkinter as ctk
import player


app = ctk.CTk()
# Window
app.title("Musikku")
app.geometry("400x550")
app.resizable(False,False)
app.configure(fg_color="black")

# Frame Atas
frame_atas = ctk.CTkFrame(app, fg_color="white")
frame_atas.grid(row=0,column=0, pady=20, padx=20, sticky="n")
# Frame Bawah

# Button
#button_play = ctk.CTkButton(frame_atas,text="Play",fg_color="white")
#button_play.grid(row=1,column=2)






app.mainloop()
