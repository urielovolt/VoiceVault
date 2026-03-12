# REPRODUCTOR MEJORADO - Reemplazar función show_detail completa
# Desde línea ~525 hasta ~705

    def show_detail(self, memory: Dict):
        # Cerrar dialog anterior si existe
        if self.current_dialog and self.current_dialog.winfo_exists():
            try:
                pygame.mixer.music.stop()
                self.playing = False
                self.current_dialog.destroy()
            except:
                pass
        
        dialog = ctk.CTkToplevel(self)
        dialog.title(memory.get("name", "Recuerdo"))
        dialog.geometry("650x550")  # Más ancho para layout horizontal
        dialog.configure(fg_color=Colors.DARK_BG)
        dialog.transient(self)
        
        # Guardar referencia
        self.current_dialog = dialog
        
        content = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Foto
        photo_path = self.get_photo_path(memory)
        if photo_path:
            try:
                img = Image.open(photo_path)
                img = img.resize((300, 300), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(300, 300))
                ctk.CTkLabel(content, image=photo, text="").pack(pady=10)
            except:
                pass
        
        # Nombre
        ctk.CTkLabel(
            content,
            text=memory.get("name", ""),
            font=("Roboto", 22, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(pady=(10, 5))
        
        # Categoría y fecha
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack()
        
        cat_frame = ctk.CTkFrame(info_frame, fg_color=Colors.CARD_BG, corner_radius=15)
        cat_frame.pack(side="left", padx=5)
        ctk.CTkLabel(cat_frame, text=memory.get("category", ""), text_color=Colors.GOLD, font=("Roboto", 11)).pack(padx=10, pady=5)
        
        ctk.CTkLabel(info_frame, text=memory.get("date", ""), text_color=Colors.TEXT_SECONDARY, font=("Roboto", 11)).pack(side="left", padx=5)
        
        # Nota
        note = memory.get("note", "").strip()
        if note:
            note_frame = ctk.CTkFrame(content, fg_color=Colors.CARD_BG, corner_radius=8)
            note_frame.pack(fill="x", pady=15)
            ctk.CTkLabel(note_frame, text=f'"{note}"', text_color=Colors.TEXT_SECONDARY, wraplength=580, font=("Roboto", 13, "italic")).pack(padx=10, pady=10)
        
        # Reproductor HORIZONTAL con barra de progreso
        audio_path = self.get_audio_path(memory)
        if audio_path:
            player_frame = ctk.CTkFrame(content, fg_color=Colors.SURFACE, corner_radius=12)
            player_frame.pack(fill="x", pady=10)
            
            # Variables
            play_var = ctk.StringVar(value="▶️")
            time_var = ctk.StringVar(value="0:00")
            progress_var = ctk.DoubleVar(value=0)
            volume_var = ctk.DoubleVar(value=0.7)
            song_length = [0]  # Duración estimada
            
            pygame.mixer.music.set_volume(0.7)
            
            # Actualizar tiempo Y barra de progreso
            def update_time():
                if self.playing and pygame.mixer.music.get_busy():
                    try:
                        pos = pygame.mixer.music.get_pos() / 1000
                        time_var.set(f"{int(pos//60)}:{int(pos%60):02d}")
                        
                        # Actualizar barra de progreso
                        if song_length[0] > 0:
                            progress_var.set(pos / song_length[0])
                        
                        dialog.after(500, update_time)
                    except:
                        pass
                elif self.playing and not pygame.mixer.music.get_busy():
                    # Canción terminó - RESETEAR
                    self.playing = False
                    play_var.set("▶️")
                    time_var.set("0:00")
                    progress_var.set(0)
            
            def toggle_play():
                if self.playing:
                    pygame.mixer.music.pause()
                    self.playing = False
                    play_var.set("▶️")
                else:
                    try:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.unpause()
                        else:
                            # Estimar duración (pygame no da duración exacta fácilmente)
                            from mutagen.mp3 import MP3
                            try:
                                audio_info = MP3(audio_path)
                                song_length[0] = audio_info.info.length
                            except:
                                song_length[0] = 180  # Fallback 3 min
                            
                            pygame.mixer.music.load(audio_path)
                            pygame.mixer.music.play()
                            update_time()
                        self.playing = True
                        play_var.set("⏸️")
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo reproducir: {e}")
            
            def stop():
                pygame.mixer.music.stop()
                self.playing = False
                play_var.set("▶️")
                time_var.set("0:00")
                progress_var.set(0)
            
            def on_volume(val):
                pygame.mixer.music.set_volume(val)
            
            # Layout HORIZONTAL
            controls = ctk.CTkFrame(player_frame, fg_color="transparent")
            controls.pack(padx=20, pady=20, fill="both")
            
            # Fila 1: Botones y tiempo
            row1 = ctk.CTkFrame(controls, fg_color="transparent")
            row1.pack(fill="x", pady=(0, 10))
            
            # Botones a la izquierda
            btn_container = ctk.CTkFrame(row1, fg_color="transparent")
            btn_container.pack(side="left")
            
            ctk.CTkButton(
                btn_container,
                textvariable=play_var,
                width=60,
                height=40,
                fg_color=Colors.GOLD,
                hover_color="#D4B06A",
                text_color=Colors.BLACK,
                font=("Roboto", 20),
                command=toggle_play
            ).pack(side="left", padx=(0, 8))
            
            ctk.CTkButton(
                btn_container,
                text="⏹️",
                width=50,
                height=40,
                fg_color=Colors.CARD_BG,
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                font=("Roboto", 16),
                command=stop
            ).pack(side="left")
            
            # Volumen en el medio
            vol_container = ctk.CTkFrame(row1, fg_color="transparent")
            vol_container.pack(side="left", padx=20, fill="x", expand=True)
            
            ctk.CTkLabel(vol_container, text="🔊", font=("Roboto", 14)).pack(side="left", padx=(0, 8))
            ctk.CTkSlider(
                vol_container,
                from_=0,
                to=1,
                variable=volume_var,
                button_color=Colors.GOLD,
                progress_color=Colors.GOLD,
                fg_color=Colors.BORDER,
                command=on_volume,
                width=150
            ).pack(side="left")
            
            # Tiempo a la derecha
            ctk.CTkLabel(
                row1,
                textvariable=time_var,
                font=("Roboto", 13),
                text_color=Colors.TEXT_SECONDARY
            ).pack(side="right")
            
            # Fila 2: Barra de progreso
            ctk.CTkProgressBar(
                controls,
                progress_color=Colors.GOLD,
                fg_color=Colors.BORDER,
                variable=progress_var,
                height=8
            ).pack(fill="x")
        
        # Botones
        buttons = ctk.CTkFrame(content, fg_color="transparent")
        buttons.pack(fill="x", pady=(20, 0))
        
        def delete():
            if messagebox.askyesno("Confirmar", "¿Eliminar este recuerdo?"):
                if self.playing:
                    pygame.mixer.music.stop()
                    self.playing = False
                self.dm.delete(memory.get("id"))
                dialog.destroy()
                self.refresh_grid()
        
        def close():
            if self.playing:
                pygame.mixer.music.stop()
                self.playing = False
            dialog.destroy()
        
        ctk.CTkButton(
            buttons,
            text="🗑️ Eliminar",
            fg_color=Colors.ERROR,
            hover_color="#B54A5A",
            command=delete
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ctk.CTkButton(
            buttons,
            text="Cerrar",
            fg_color="transparent",
            border_width=1,
            border_color=Colors.BORDER,
            command=close
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))
