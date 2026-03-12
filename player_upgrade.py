# Código mejorado del reproductor de audio
# Reemplazar desde línea 550 hasta línea 582

        audio_path = self.get_audio_path(memory)
        if audio_path:
            audio_frame = ctk.CTkFrame(content, fg_color=Colors.SURFACE, corner_radius=12)
            audio_frame.pack(fill="x", pady=10)
            
            # Variables de control
            play_var = ctk.StringVar(value="▶️ Play")
            time_var = ctk.StringVar(value="0:00")
            volume_var = ctk.DoubleVar(value=0.7)
            
            # Configurar volumen inicial
            pygame.mixer.music.set_volume(0.7)
            
            # Funciones de control
            def update_time():
                if self.playing and pygame.mixer.music.get_busy():
                    try:
                        pos = pygame.mixer.music.get_pos() / 1000
                        current_time = f"{int(pos//60)}:{int(pos%60):02d}"
                        time_var.set(current_time)
                        dialog.after(500, update_time)
                    except:
                        pass
            
            def toggle_play():
                if self.playing:
                    pygame.mixer.music.pause()
                    self.playing = False
                    play_var.set("▶️ Play")
                else:
                    try:
                        if pygame.mixer.music.get_busy():
                            pygame.mixer.music.unpause()
                        else:
                            pygame.mixer.music.load(audio_path)
                            pygame.mixer.music.play()
                            update_time()
                        self.playing = True
                        play_var.set("⏸️ Pause")
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo reproducir: {e}")
            
            def stop_audio():
                pygame.mixer.music.stop()
                self.playing = False
                play_var.set("▶️ Play")
                time_var.set("0:00")
            
            def on_volume_change(value):
                pygame.mixer.music.set_volume(value)
            
            # Frame de controles
            controls = ctk.CTkFrame(audio_frame, fg_color="transparent")
            controls.pack(padx=15, pady=15, fill="x")
            
            # Botones Play/Stop
            btn_frame = ctk.CTkFrame(controls, fg_color="transparent")
            btn_frame.pack(fill="x", pady=(0, 10))
            
            ctk.CTkButton(
                btn_frame,
                textvariable=play_var,
                width=120,
                fg_color=Colors.GOLD,
                hover_color="#D4B06A",
                text_color=Colors.BLACK,
                command=toggle_play
            ).pack(side="left", padx=(0, 10))
            
            ctk.CTkButton(
                btn_frame,
                text="⏹️ Stop",
                width=100,
                fg_color=Colors.CARD_BG,
                hover_color=Colors.BORDER,
                text_color=Colors.TEXT_PRIMARY,
                command=stop_audio
            ).pack(side="left")
            
            ctk.CTkLabel(
                btn_frame,
                textvariable=time_var,
                font=("Roboto", 12),
                text_color=Colors.TEXT_SECONDARY
            ).pack(side="right")
            
            # Control de volumen
            vol_frame = ctk.CTkFrame(controls, fg_color="transparent")
            vol_frame.pack(fill="x")
            
            ctk.CTkLabel(
                vol_frame,
                text="🔊",
                font=("Roboto", 14),
                text_color=Colors.TEXT_SECONDARY
            ).pack(side="left", padx=(0, 10))
            
            ctk.CTkSlider(
                vol_frame,
                from_=0,
                to=1,
                variable=volume_var,
                button_color=Colors.GOLD,
                button_hover_color="#D4B06A",
                progress_color=Colors.GOLD,
                fg_color=Colors.BORDER,
                command=on_volume_change
            ).pack(side="left", fill="x", expand=True)
