import os
import threading
import math
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinter.colorchooser import askcolor
import multiprocessing
import queue
import webbrowser
import psutil # Vous devrez peut-être installer cette librairie : pip install psutil
from concurrent.futures import ProcessPoolExecutor
import json # Ajout pour la sauvegarde des paramètres

# --- CONFIGURATION ---

# Palette de couleurs modernes et tendances 2025
MODERN_COLORS = {
    # Couleurs naturelles et organiques
    "Sage Moderne": "#87A96B", "Forest Green": "#2A9D8F", "Mint Glacé": "#B8E6B8",
    "Olive Doux": "#B5B682", "Eucalyptus": "#6B8E2B", "Bambou": "#9CAF88",

    # Bleus sophistiqués
    "Bleu Cosmic": "#1B263B", "Navy Deep": "#2F3E46", "Teal Profond": "#264653",
    "Slate Blue": "#6C5CE7", "Sky Mist": "#A8DADC", "Pétrole": "#2C5F2D",
    "Azur": "#007FFF", "Indigo Nuit": "#191970", "Cyan Électrique": "#00FFFF",

    # Roses et coraux élégants
    "Rose Poudré": "#F8D7DA", "Dusty Rose": "#D4A5A5", "Coral Sunset": "#FF6B6B",
    "Peach Cream": "#FFE5B4", "Saumon": "#FA8072", "Rose Gold": "#E8B4B8",
    "Fuchsia Doux": "#FF69B4", "Magenta Soft": "#DA70D6", "Cerise": "#DE3163",

    # Violets et mauves raffinés
    "Violet Luxe": "#6A4C93", "Lavande Soft": "#E6E6FA", "Berry Wine": "#774C60",
    "Améthyste": "#9966CC", "Lilas": "#B19CD9", "Prune": "#8E4585",
    "Orchidée": "#DA70D6", "Pervenche": "#CCCCFF", "Byzantin": "#702963",

    # Oranges et terres chaudes
    "Terracotta Chic": "#A0522D", "Amber Gold": "#F4A261", "Warm Taupe": "#A0826D",
    "Paprika": "#CC6000", "Cannelle": "#D2691E", "Safran": "#F4C430",
    "Orange Brûlé": "#CC5500", "Caramel": "#AF6E4D", "Cuivre": "#B87333",

    # Jaunes lumineux et dorés
    "Or Solaire": "#FFD700", "Miel": "#FFC649", "Citron Vert": "#CCFF00",
    "Jaune Moutarde": "#FFDB58", "Vanille": "#F3E5AB", "Champagne": "#F7E7CE",

    # Rouges puissants et énergiques
    "Rouge Carmin": "#DC143C", "Bordeaux": "#800020", "Vermillon": "#E34234",
    "Cerise Noire": "#722F37", "Rubis": "#AA4069", "Grenat": "#722F37",

    # Neutres modernes et sophistiqués
    "Gris Charbon": "#36454F", "Gris Perle": "#BCC6CC", "Beige Moderne": "#F5F5DC",
    "Taupe Clair": "#B8860B", "Gris Souris": "#696969", "Lin": "#FAF0E6",
    "Crème": "#FFFDD0", "Ivoire": "#FFFFF0", "Blanc Cassé": "#FDF6E3",

    # Couleurs vives et énergiques
    "Vert Lime": "#32CD32", "Turquoise": "#40E0D0", "Violet Néon": "#9400D3",
    "Rose Fluo": "#FF1493", "Orange Vif": "#FF4500", "Jaune Électrique": "#FFFF00"
}

# --- Fenêtre de sélection de couleurs réutilisable ---
class ColorPalettePicker(ctk.CTkToplevel):
    def __init__(self, master, callback, title="Choisissez une couleur"):
        super().__init__(master)
        self.callback = callback
        self.master_app = master

        self.title(title)
        self.geometry("800x650")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        hex_frame = ctk.CTkFrame(self, fg_color="#21262D", corner_radius=0)
        hex_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(hex_frame, text="Code couleur personnalisé :", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#F0F6FC").pack(side="left", padx=(20, 10), pady=15)
        
        self.hex_entry = ctk.CTkEntry(hex_frame, placeholder_text="#AABBCC", font=ctk.CTkFont(size=14),
            corner_radius=10, height=35, width=150)
        self.hex_entry.pack(side="left", padx=10, pady=15)
        
        ctk.CTkButton(hex_frame, text="✓ Valider", command=self._validate_and_select_hex,
            corner_radius=10, height=35, fg_color="#238636", hover_color="#2EA043").pack(side="left", padx=(10, 20), pady=15)
        
        colors_frame = ctk.CTkScrollableFrame(self, fg_color="#161B22")
        colors_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.master_app._create_color_palette_widgets(colors_frame, self._on_select)

    def _validate_and_select_hex(self):
        try:
            hex_value = self.hex_entry.get().strip()
            if not hex_value.startswith('#'):
                hex_value = '#' + hex_value
            _ = self.master_app.hex_to_rgb(hex_value)
            self._on_select(hex_value)
        except (ValueError, IndexError):
            self.hex_entry.delete(0, 'end')
            self.hex_entry.insert(0, "❌ Code Invalide")

    def _on_select(self, hex_color):
        self.callback(hex_color)
        self.destroy()

# --- Fonctions de traitement d'image ---
def calculate_ratio_process(x, y, width, height, direction_key):
    w_m1, h_m1 = max(1, width - 1), max(1, height - 1)
    if direction_key == "Haut-Droit vers Bas-Gauche": return ((w_m1 - x) / w_m1 + y / h_m1) / 2
    if direction_key == "Haut-Gauche vers Bas-Droit": return (x / w_m1 + y / h_m1) / 2
    if direction_key == "Gauche vers Droite": return x / w_m1
    if direction_key == "Haut vers Bas": return y / h_m1
    if direction_key == "Radial depuis le Centre":
        cx, cy = w_m1 / 2, h_m1 / 2
        dist = math.sqrt((x - cx)**2 + (y - cy)**2)
        max_dist = math.sqrt(cx**2 + cy**2)
        return dist / max_dist if max_dist > 0 else 0
    return 0

def create_rounded_mask_process(width, height, radius):
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, width, height), radius=radius, fill=255)
    return mask

def apply_overlay_effects_process(img, color_hex, invert):
    if invert:
        if img.mode == 'RGBA':
            r, g, b, a = img.split()
            rgb_img = Image.merge("RGB", (r, g, b))
            inverted_rgb = ImageOps.invert(rgb_img)
            r, g, b = inverted_rgb.split()
            img = Image.merge("RGBA", (r, g, b, a))
        else:
            img = ImageOps.invert(img)

    if color_hex:
        color_img = Image.new("RGBA", img.size, color_hex)
        if img.mode == 'RGBA':
            img.paste(color_img, (0, 0), mask=img.split()[-1])
        else:
            img = color_img
            
    return img

def generate_rounded_gradient_image(width, height, start_color, end_color_factor, direction, radius):
    img = Image.new("RGBA", (width, height))
    end_color = tuple(int(c * end_color_factor) for c in start_color)
    for y in range(height):
        for x in range(width):
            r = calculate_ratio_process(x, y, width, height, direction)
            color = tuple(int(sc * (1 - r) + ec * r) for sc, ec in zip(start_color, end_color))
            img.putpixel((x, y), color + (255,))
    
    if radius > 0:
        mask = create_rounded_mask_process(width, height, radius)
        img.putalpha(mask)
        
    return img

def create_gradient_image_manager(q, start_color, end_color_factor, width, height, file_format, direction, radius, save_path,
                                  overlay_path, overlay_scale, overlay_recolor, overlay_invert,
                                  background_layers, layer_padding):
    try:
        num_bg_layers = len(background_layers)
        final_width = width + num_bg_layers * 2 * layer_padding
        final_height = height + num_bg_layers * 2 * layer_padding
        
        final_image = Image.new("RGBA", (final_width, final_height), (0,0,0,0))

        for i in reversed(range(num_bg_layers)):
            layer_color = background_layers[i]['color']
            layer_width = width + (i + 1) * 2 * layer_padding
            layer_height = height + (i + 1) * 2 * layer_padding
            layer_radius = radius + (i + 1) * layer_padding
            
            layer_gradient = generate_rounded_gradient_image(layer_width, layer_height, layer_color, end_color_factor, direction, layer_radius)
            
            paste_x = (final_width - layer_width) // 2
            paste_y = (final_height - layer_height) // 2
            final_image.paste(layer_gradient, (paste_x, paste_y), layer_gradient)

        main_gradient = generate_rounded_gradient_image(width, height, start_color, end_color_factor, direction, radius)
        q.put(('progress', 100))
        
        main_paste_x = (final_width - width) // 2
        main_paste_y = (final_height - height) // 2
        final_image.paste(main_gradient, (main_paste_x, main_paste_y), main_gradient)

        if overlay_path:
            overlay_img = Image.open(overlay_path).convert("RGBA")
            ratio = min((width * overlay_scale) / overlay_img.width, (height * overlay_scale) / overlay_img.height)
            new_size = (int(overlay_img.width * ratio), int(overlay_img.height * ratio))
            resized_overlay = overlay_img.resize(new_size, Image.Resampling.LANCZOS)
            processed_overlay = apply_overlay_effects_process(resized_overlay, overlay_recolor, overlay_invert)
            
            paste_x = (final_width - processed_overlay.width) // 2
            paste_y = (final_height - processed_overlay.height) // 2
            final_image.paste(processed_overlay, (paste_x, paste_y), processed_overlay)

        save_options = {}
        if file_format == 'JPG':
            if final_image.mode == 'RGBA': 
                jpg_background = Image.new("RGB", final_image.size, (255, 255, 255))
                jpg_background.paste(final_image, mask=final_image.split()[3])
                final_image = jpg_background
            save_options['quality'] = 95
        elif file_format == 'WEBP':
            save_options['lossless'] = True

        final_image.save(save_path, **save_options)
        q.put(('done', save_path))
    except Exception as e:
        q.put(('error', f"ERREUR: {e}"))

# --- Classe principale de l'application ---
class GradientApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("✨ Générateur de Dégradés Premium")
        self.geometry("1200x800")
        self.minsize(1200, 800)
        self.resizable(True, True)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.SETTINGS_FILE = "settings.json"
        self.loaded_settings = self._load_settings()
        self.is_first_load = True # Pour charger les settings qu'une seule fois

        self.configure(fg_color="#0D1117")
        self.default_save_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
        self.container = ctk.CTkFrame(self, fg_color="#161B22", corner_radius=20)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.formats_with_alpha = ["PNG", "WEBP", "TIFF", "GIF", "ICO", "TGA"]
        self.formats_no_alpha = ["JPG", "BMP"]
        self.all_formats = self.formats_with_alpha + self.formats_no_alpha
        
        self.overlay_pil_image_original = None
        self.overlay_image_path = None
        self.overlay_recolor_hex = None
        self.overlay_invert = False
        self.preview_bg_is_dark = True
        
        self.background_layers = []
        
        self.is_generating = False
        self.process = None
        self.after_id_cpu = None
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.show_color_selection_frame()

    def on_closing(self):
        if hasattr(self, 'start_color'):
            self._save_settings()
        if self.is_generating and self.process and self.process.is_alive():
            self.process.terminate()
        self.destroy()

    def _save_settings(self):
        settings = {
            "base_color_hex": self.rgb_to_hex(self.start_color),
            "width": self.width_entry.get(),
            "height": self.height_entry.get(),
            "darkness": self.darkness_var.get(),
            "contours": [self.rgb_to_hex(layer['color']) for layer in self.background_layers],
            "contour_padding": self.layer_padding_var.get(),
            "radius": self.corner_radius_var.get(),
            "format": self.format_combo.get(),
            "direction": self.direction_combo.get(),
            "perfect_darkness": self.perfect_darkness_var.get(),
            "perfect_roundness": self.perfect_round_var.get(),
        }
        try:
            with open(self.SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres: {e}")

    def _load_settings(self):
        try:
            with open(self.SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def hex_to_rgb(self, hex_code):
        hex_code = hex_code.lstrip('#')
        return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

    def calculate_darker_color(self, rgb_color, factor=0.3):
        return tuple(int(c * factor) for c in rgb_color)

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def rgb_to_hex(self, rgb_color):
        return f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"

    def _create_color_palette_widgets(self, parent, on_color_select_callback):
        columns = 6
        for i, (name, hex_code) in enumerate(MODERN_COLORS.items()):
            row, col = divmod(i, columns)
            rgb = self.hex_to_rgb(hex_code)
            text_color = "#000000" if (sum(rgb) / 3) > 128 else "#FFFFFF"
            
            color_button = ctk.CTkButton(parent, text=name, fg_color=hex_code, hover_color=hex_code,
                text_color=text_color, font=ctk.CTkFont(size=12, weight="bold"), corner_radius=15, height=80,
                width=160, command=lambda h=hex_code: on_color_select_callback(h))
            color_button.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        
        for i in range(columns):
            parent.grid_columnconfigure(i, weight=1)
            
    def show_color_selection_frame(self):
        self.clear_container()
        self.is_first_load = True # Réinitialise le flag à chaque retour à l'accueil
        
        title = ctk.CTkLabel(self.container, text="🎨 Choisissez votre couleur de base", 
            font=ctk.CTkFont(size=32, weight="bold"), text_color="#F0F6FC")
        title.pack(pady=(30, 20))

        hex_frame = ctk.CTkFrame(self.container, fg_color="#21262D", corner_radius=15)
        hex_frame.pack(pady=20, padx=40, fill="x")
        
        ctk.CTkLabel(hex_frame, text="Code couleur personnalisé :", 
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#F0F6FC").pack(side="left", padx=(20, 10), pady=15)
        
        self.hex_entry = ctk.CTkEntry(hex_frame, placeholder_text="#AABBCC", font=ctk.CTkFont(size=14),
            corner_radius=10, height=35, width=150)
        self.hex_entry.pack(side="left", padx=10, pady=15)
        
        ctk.CTkButton(hex_frame, text="✓ Valider", command=self.select_hex_color,
            corner_radius=10, height=35, fg_color="#238636", hover_color="#2EA043").pack(side="left", padx=(10, 20), pady=15)

        colors_frame = ctk.CTkScrollableFrame(self.container, fg_color="transparent")
        colors_frame.pack(fill="both", expand=True, padx=40, pady=(10, 30))
        
        self._create_color_palette_widgets(colors_frame, lambda h: self.show_config_frame(self.hex_to_rgb(h)))

    def select_hex_color(self):
        try:
            hex_value = self.hex_entry.get().strip()
            if not hex_value.startswith('#'): hex_value = '#' + hex_value
            self.show_config_frame(self.hex_to_rgb(hex_value))
        except (ValueError, IndexError):
            self.hex_entry.delete(0, 'end'); self.hex_entry.insert(0, "❌ Code Invalide")

    def show_config_frame(self, start_color):
        self.clear_container()
        
        # Le choix de l'utilisateur est prioritaire
        self.start_color = start_color
        self.selected_color_hex = self.rgb_to_hex(self.start_color)

        main_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1, minsize=400)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        self.left_frame = ctk.CTkFrame(main_frame, fg_color="#21262D", corner_radius=20)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self.preview_title_label = ctk.CTkLabel(self.left_frame, text="👁️ Aperçu en temps réel", 
            font=ctk.CTkFont(size=20, weight="bold"), text_color="#F0F6FC")
        self.preview_title_label.pack(pady=20)
        self.preview_label = ctk.CTkLabel(self.left_frame, text="")
        self.preview_label.pack(pady=20, padx=20, expand=True)
        ctk.CTkButton(self.left_frame, text="Changer fond (clair/sombre)", command=self._toggle_preview_bg).pack(pady=5)
        ctk.CTkButton(self.left_frame, text="← Retour à la sélection", command=self.show_color_selection_frame,
            fg_color="#6C757D", hover_color="#5A6268", corner_radius=10, height=35).pack(pady=(10, 20))

        self.right_frame = ctk.CTkFrame(main_frame, fg_color="#21262D", corner_radius=20)
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        content_frame = ctk.CTkScrollableFrame(self.right_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(content_frame, text="⚙️ Configuration du Dégradé",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#F0F6FC").pack(pady=(15, 20), padx=20)

        ctk.CTkLabel(content_frame, text="📐 Dimensions de la forme centrale (pixels) :",
            font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', padx=20)
        size_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        size_frame.pack(fill='x', pady=(5, 15), padx=20)
        self.width_entry = ctk.CTkEntry(size_frame, placeholder_text="Largeur", corner_radius=10, height=40)
        self.width_entry.insert(0, self.loaded_settings.get("width", "4096") if self.is_first_load else "4096")
        self.width_entry.pack(side='left', expand=True, fill='x', padx=(0, 10))
        self.width_entry.bind('<KeyRelease>', self.on_dimension_change)
        self.height_entry = ctk.CTkEntry(size_frame, placeholder_text="Hauteur", corner_radius=10, height=40)
        self.height_entry.insert(0, self.loaded_settings.get("height", "4096") if self.is_first_load else "4096")
        self.height_entry.pack(side='left', expand=True, fill='x')
        self.height_entry.bind('<KeyRelease>', self.on_dimension_change)
        
        overlay_main_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        overlay_main_frame.pack(fill='x', padx=20, pady=(10,0))
        
        ctk.CTkLabel(overlay_main_frame, text="🖼️ Image Superposée",
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#F0F6FC").pack()
        
        b_frame1 = ctk.CTkFrame(overlay_main_frame, fg_color="transparent")
        b_frame1.pack(fill='x', pady=10)
        self.select_overlay_button = ctk.CTkButton(b_frame1, text="Choisir une image...", command=self._select_overlay_image)
        self.select_overlay_button.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.flaticon_button = ctk.CTkButton(b_frame1, text="Trouver sur Flaticon", command=self._open_flaticon, fg_color="#226089")
        self.flaticon_button.pack(side='left', fill='x', expand=True, padx=(5, 0))

        self.overlay_controls_frame = ctk.CTkFrame(overlay_main_frame, fg_color="transparent")
        self.overlay_label = ctk.CTkLabel(self.overlay_controls_frame, text="", text_color="gray", font=ctk.CTkFont(size=12))
        self.overlay_label.pack(anchor='w', pady=5)
        self.overlay_scale_var = ctk.DoubleVar(value=100.0)
        ctk.CTkLabel(self.overlay_controls_frame, text="Taille de l'image :", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(10, 0))
        b_frame2 = ctk.CTkFrame(self.overlay_controls_frame, fg_color="transparent")
        b_frame2.pack(fill='x')
        self.overlay_scale_label = ctk.CTkLabel(b_frame2, text="100%", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.selected_color_hex, width=50)
        self.overlay_scale_label.pack(side='left')
        self.ideal_size_button = ctk.CTkButton(b_frame2, text="Taille Idéale (85%)", command=self._set_ideal_size, height=25)
        self.ideal_size_button.pack(side='left', padx=10)
        self.overlay_scale_slider = ctk.CTkSlider(self.overlay_controls_frame, from_=1, to=100, variable=self.overlay_scale_var, command=self.on_config_change,
            progress_color=self.selected_color_hex, button_color=self.selected_color_hex, button_hover_color=self.selected_color_hex)
        self.overlay_scale_slider.pack(fill='x', pady=5)
        ctk.CTkLabel(self.overlay_controls_frame, text="Effets sur l'image :", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(10, 5))
        b_frame3 = ctk.CTkFrame(self.overlay_controls_frame, fg_color="transparent")
        b_frame3.pack(fill='x', pady=(10,0))
        self.recolor_button = ctk.CTkButton(b_frame3, text="🎨 Coloriser l'icône...", command=self._recolor_overlay)
        self.recolor_button.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.recolor_reset_button = ctk.CTkButton(b_frame3, text="Couleur Originale", command=self._reset_recolor_overlay)
        self.recolor_reset_button.pack(side='left', fill='x', expand=True, padx=(5, 0))
        self.invert_button = ctk.CTkButton(self.overlay_controls_frame, text="Inverser les Couleurs", command=self._toggle_invert_overlay)
        self.invert_button.pack(fill='x', pady=5)
        self.remove_overlay_button = ctk.CTkButton(self.overlay_controls_frame, text="❌ Retirer l'image", command=self._remove_overlay_image, fg_color="#D73A49")
        self.remove_overlay_button.pack(fill='x', pady=10)
        
        self.darkness_var = ctk.IntVar(value=self.loaded_settings.get("darkness", 30) if self.is_first_load else 30)
        ctk.CTkLabel(content_frame, text="✨ Luminosité des dégradés :", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(20, 5), padx=20)
        darkness_control_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        darkness_control_frame.pack(fill='x', pady=(0, 5), padx=20)
        self.darkness_label = ctk.CTkLabel(darkness_control_frame, text="30%", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.selected_color_hex)
        self.darkness_label.pack(anchor='w')
        self.darkness_slider = ctk.CTkSlider(darkness_control_frame, from_=0, to=100, variable=self.darkness_var, command=self.on_config_change,
            progress_color=self.selected_color_hex, button_color=self.selected_color_hex, button_hover_color=self.selected_color_hex)
        self.darkness_slider.pack(fill='x', pady=5)
        self.perfect_darkness_var = ctk.BooleanVar(value=self.loaded_settings.get("perfect_darkness", True) if self.is_first_load else True)
        self.perfect_darkness_checkbox = ctk.CTkCheckBox(darkness_control_frame, text="Assombrissement recommandé (30%)", variable=self.perfect_darkness_var, command=self.on_perfect_darkness_change, checkmark_color=self.selected_color_hex, hover_color=self.selected_color_hex)
        self.perfect_darkness_checkbox.pack(anchor='w', pady=(10, 0))

        multi_bg_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        multi_bg_frame.pack(fill='x', pady=(20, 5), padx=20)
        ctk.CTkLabel(multi_bg_frame, text="🎨 Contours / Bordures en Cascade", font=ctk.CTkFont(size=22, weight="bold"), text_color="#F0F6FC").pack()
        self.layer_padding_var = ctk.IntVar(value=self.loaded_settings.get("contour_padding", 100) if self.is_first_load else 100)
        ctk.CTkLabel(multi_bg_frame, text="Marge / Épaisseur des contours (pixels) :", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(10, 0))
        self.layer_padding_label = ctk.CTkLabel(multi_bg_frame, text="100px", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.selected_color_hex)
        self.layer_padding_label.pack(anchor='w')
        self.layer_padding_slider = ctk.CTkSlider(multi_bg_frame, from_=0, to=512, variable=self.layer_padding_var, command=self.on_config_change,
            progress_color=self.selected_color_hex, button_color=self.selected_color_hex, button_hover_color=self.selected_color_hex)
        self.layer_padding_slider.pack(fill='x', pady=5)
        self.add_layer_button = ctk.CTkButton(multi_bg_frame, text="+ Ajouter un contour", command=self._add_background_layer)
        self.add_layer_button.pack(fill='x', pady=(10, 5))
        self.layer_list_frame = ctk.CTkFrame(multi_bg_frame, fg_color="transparent")
        self.layer_list_frame.pack(fill='x', pady=5)
        
        if self.is_first_load:
            self.background_layers = [{'color': self.hex_to_rgb(hex_str)} for hex_str in self.loaded_settings.get("contours", [])]

        self.corner_radius_var = ctk.IntVar(value=self.loaded_settings.get("radius", 0) if self.is_first_load else 0)
        ctk.CTkLabel(content_frame, text="🔄 Arrondi des coins (forme intérieure) :", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(15, 5), padx=20)
        radius_control_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        radius_control_frame.pack(fill='x', pady=(0, 10), padx=20)
        self.radius_label = ctk.CTkLabel(radius_control_frame, text="0px", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.selected_color_hex)
        self.radius_label.pack(anchor='w')
        self.corner_slider = ctk.CTkSlider(radius_control_frame, from_=0, to=1024, variable=self.corner_radius_var, command=self.on_config_change,
            progress_color=self.selected_color_hex, button_color=self.selected_color_hex, button_hover_color=self.selected_color_hex)
        self.corner_slider.pack(fill='x', pady=5)
        radius_entry_frame = ctk.CTkFrame(radius_control_frame, fg_color="transparent")
        radius_entry_frame.pack(fill='x', pady=(5, 0))
        ctk.CTkLabel(radius_entry_frame, text="Valeur exacte :").pack(side='left')
        self.radius_entry = ctk.CTkEntry(radius_entry_frame, width=80, height=30, corner_radius=8)
        self.radius_entry.pack(side='left', padx=(10, 0))
        self.radius_entry.bind('<KeyRelease>', self.on_radius_entry_change)
        self.perfect_round_var = ctk.BooleanVar(value=self.loaded_settings.get("perfect_roundness", True) if self.is_first_load else True)
        self.perfect_round_checkbox = ctk.CTkCheckBox(radius_control_frame, text="Rondeur parfaite (25% pour carré arrondi web)",
            variable=self.perfect_round_var, command=self.on_perfect_round_change, checkmark_color=self.selected_color_hex, hover_color=self.selected_color_hex)
        self.perfect_round_checkbox.pack(anchor='w', pady=(10, 0))

        ctk.CTkLabel(content_frame, text="💾 Format du fichier :",
            font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(20, 5), padx=20)
        self.format_combo = ctk.CTkComboBox(content_frame, values=self.all_formats, corner_radius=10, height=35,
            button_color=self.selected_color_hex, button_hover_color=self.selected_color_hex)
        self.format_combo.set(self.loaded_settings.get("format", "PNG") if self.is_first_load else "PNG")
        self.format_combo.pack(fill='x', pady=(0, 20), padx=20)
        
        ctk.CTkLabel(content_frame, text="🌈 Direction du dégradé :",
            font=ctk.CTkFont(size=16, weight="bold")).pack(anchor='w', pady=(0, 5), padx=20)
        self.direction_combo = ctk.CTkComboBox(content_frame, values=["Haut-Droit vers Bas-Gauche", "Haut-Gauche vers Bas-Droit", 
                                   "Gauche vers Droite", "Haut vers Bas", "Radial depuis le Centre"],
            command=self.on_config_change, corner_radius=10, height=35,
            button_color=self.selected_color_hex, button_hover_color=self.selected_color_hex)
        self.direction_combo.set(self.loaded_settings.get("direction", "Haut-Droit vers Bas-Gauche") if self.is_first_load else "Haut-Droit vers Bas-Gauche")
        self.direction_combo.pack(fill='x', pady=(0, 30), padx=20)

        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill='x', pady=(10, 0), padx=20)
        self.generate_button = ctk.CTkButton(button_frame, text="🚀 Générer l'image", command=self.start_generation_process,
            corner_radius=15, height=45, font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=self.selected_color_hex, hover_color=self.rgb_to_hex(self.calculate_darker_color(self.hex_to_rgb(self.selected_color_hex), 0.8)))
        self.generate_button.pack(fill='x')
        
        self.progress_bar = ctk.CTkProgressBar(button_frame, progress_color=self.selected_color_hex)
        self.progress_bar.set(0)
        self.cpu_label = ctk.CTkLabel(button_frame, text="CPU: 0%", font=ctk.CTkFont(size=12))
        self.status_label = ctk.CTkLabel(button_frame, text="", font=ctk.CTkFont(size=14))
        self.status_label.pack(pady=5)
        
        self._update_overlay_controls()
        self._update_layer_display()
        self.on_config_change()
        
        self.is_first_load = False # Marquer la fin du premier chargement

    def _add_background_layer(self):
        ColorPalettePicker(self, callback=self._handle_contour_color_selection, title="Choisissez une couleur de contour")

    def _handle_contour_color_selection(self, hex_color):
        rgb_color = self.hex_to_rgb(hex_color)
        new_layer = {'color': rgb_color}
        self.background_layers.append(new_layer)
        self._update_layer_display()
        self.on_config_change()
        
    def _remove_background_layer(self, index):
        self.background_layers.pop(index)
        self._update_layer_display()
        self.on_config_change()

    def _update_layer_display(self):
        for widget in self.layer_list_frame.winfo_children():
            widget.destroy()

        for i, layer in enumerate(self.background_layers):
            layer_frame = ctk.CTkFrame(self.layer_list_frame, fg_color="#21262D")
            layer_frame.pack(fill='x', pady=2)
            
            color_box = ctk.CTkLabel(layer_frame, text="", fg_color=self.rgb_to_hex(layer['color']), width=20, height=20, corner_radius=5)
            color_box.pack(side='left', padx=10, pady=5)
            
            ctk.CTkLabel(layer_frame, text=f"Contour {i + 1}").pack(side='left', expand=True, anchor='w')
            
            remove_button = ctk.CTkButton(layer_frame, text="❌", width=30, height=30, fg_color="transparent", hover_color="#D73A49",
                                          command=lambda i=i: self._remove_background_layer(i))
            remove_button.pack(side='right', padx=5)
        
        self.update_idletasks()

    def _toggle_ui_elements(self, state='disabled'):
        widgets_to_toggle = [
            self.width_entry, self.height_entry, self.select_overlay_button, self.flaticon_button,
            self.ideal_size_button, self.overlay_scale_slider, 
            self.recolor_button, self.recolor_reset_button, self.invert_button, self.remove_overlay_button,
            self.darkness_slider, self.perfect_darkness_checkbox, self.corner_slider, self.radius_entry,
            self.perfect_round_checkbox, self.format_combo, self.direction_combo,
            self.add_layer_button, self.layer_padding_slider
        ]
        for widget in widgets_to_toggle:
            if widget is not None and hasattr(widget, 'configure'):
                widget.configure(state=state)
        for child in self.layer_list_frame.winfo_children():
            for btn in child.winfo_children():
                if isinstance(btn, ctk.CTkButton):
                    btn.configure(state=state)

    def _update_cpu_usage(self):
        if self.is_generating:
            try:
                cpu_percent = psutil.cpu_percent(interval=None)
                self.cpu_label.configure(text=f"CPU: {cpu_percent:.1f}%")
                self.after_id_cpu = self.after(1000, self._update_cpu_usage)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.is_generating = False

    def _open_flaticon(self):
        if messagebox.askyesno("Ouvrir le navigateur", "Vous allez être redirigé vers le site flaticon.com pour trouver une icône.\n\nVoulez-vous continuer ?"):
            webbrowser.open("https://www.flaticon.com")

    def _select_overlay_image(self):
        file_path = filedialog.askopenfilename(title="Sélectionnez une image", filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.webp *.bmp"), ("Tous les fichiers", "*.*")])
        if file_path:
            self.overlay_image_path = file_path
            self.overlay_pil_image_original = Image.open(file_path).convert("RGBA")
            self.overlay_label.configure(text=os.path.basename(file_path))
            self._reset_overlay_effects()
            self._update_overlay_controls()
            self._set_ideal_size()
            
    def _remove_overlay_image(self):
        self.overlay_pil_image_original = None
        self.overlay_image_path = None
        self._reset_overlay_effects()
        self._update_overlay_controls()
        self.on_config_change()
    
    def _reset_overlay_effects(self):
        self.overlay_recolor_hex = None
        self.overlay_invert = False
        self.invert_button.configure(fg_color=("#3E4D5C", "#21262d"))

    def _update_overlay_controls(self):
        has_image = self.overlay_pil_image_original is not None
        if has_image: self.overlay_controls_frame.pack(fill='x', pady=10)
        else: self.overlay_controls_frame.pack_forget()

    def _set_ideal_size(self):
        self.overlay_scale_var.set(85.0)
        self.on_config_change()

    def _recolor_overlay(self):
        ColorPalettePicker(self, callback=self._handle_recolor_selection, title="Choisissez une couleur pour l'icône")
    
    def _handle_recolor_selection(self, hex_color):
        self.overlay_recolor_hex = hex_color
        self.on_config_change()

    def _reset_recolor_overlay(self):
        self.overlay_recolor_hex = None
        self.on_config_change()

    def _toggle_invert_overlay(self):
        self.overlay_invert = not self.overlay_invert
        if self.overlay_invert: self.invert_button.configure(fg_color=self.selected_color_hex)
        else: self.invert_button.configure(fg_color=("#3E4D5C", "#21262d"))
        self.on_config_change()

    def _toggle_preview_bg(self):
        self.preview_bg_is_dark = not self.preview_bg_is_dark
        if self.preview_bg_is_dark:
            bg_color, text_color = "#21262D", "#F0F6FC"
        else:
            bg_color, text_color = "#E5E5E5", "#1A1A1A"
        self.left_frame.configure(fg_color=bg_color)
        self.preview_title_label.configure(text_color=text_color)

    def on_dimension_change(self, event=None):
        if hasattr(self, 'perfect_round_var') and self.perfect_round_var.get(): self.on_perfect_round_change()
        self.on_config_change()

    def on_radius_entry_change(self, event=None):
        try:
            value = int(self.radius_entry.get())
            self.corner_radius_var.set(max(0, min(1024, value)))
            self.on_config_change()
        except ValueError: pass

    def on_perfect_round_change(self):
        if self.perfect_round_var.get():
            try:
                width, height = int(self.width_entry.get()), int(self.height_entry.get())
                pr = min(min(width, height) // 4, 1024)
                self.corner_radius_var.set(pr)
                self.radius_entry.delete(0, 'end'); self.radius_entry.insert(0, str(pr))
            except ValueError: pass
        self.on_config_change()
    
    def on_perfect_darkness_change(self):
        if self.perfect_darkness_var.get(): self.darkness_var.set(30)
        self.on_config_change()

    def on_config_change(self, *args):
        current_radius = self.corner_radius_var.get()
        self.radius_label.configure(text=f"{current_radius}px")
        crev = self.radius_entry.get()
        if not crev or (crev.isdigit() and int(crev) != current_radius):
            self.radius_entry.delete(0, 'end'); self.radius_entry.insert(0, str(current_radius))
        
        try:
            width, height = int(self.width_entry.get()), int(self.height_entry.get())
            perfect_radius = min(min(width, height) // 4, 1024)
            self.perfect_round_var.set(current_radius == perfect_radius and width > 0 and height > 0)
        except ValueError:
            self.perfect_round_var.set(False)

        if current_radius > 0 or len(self.background_layers) > 0:
            self.format_combo.configure(values=self.formats_with_alpha)
            if self.format_combo.get() in self.formats_no_alpha: self.format_combo.set("PNG")
        else:
            self.format_combo.configure(values=self.all_formats)
        
        dv = self.darkness_var.get()
        self.perfect_darkness_var.set(dv == 30)
        self.end_color_factor = dv / 100.0
        self.darkness_label.configure(text=f"{dv}%")
        
        self.overlay_scale_label.configure(text=f"{int(self.overlay_scale_var.get())}%")
        self.layer_padding_label.configure(text=f"{self.layer_padding_var.get()}px")

        preview_pil = self.generate_preview_image(350, 350)
        preview_ctk = ctk.CTkImage(light_image=preview_pil, dark_image=preview_pil, size=(350, 350))
        self.preview_label.configure(image=preview_ctk)

    def generate_preview_image(self, max_width, max_height):
        try:
            base_w_orig = int(self.width_entry.get())
            base_h_orig = int(self.height_entry.get())
        except ValueError:
            return Image.new("RGBA", (max_width, max_height), (0,0,0,0))

        num_bg_layers = len(self.background_layers)
        layer_padding = self.layer_padding_var.get()
        radius = self.corner_radius_var.get()
        
        scale_factor = 250 / max(1, base_w_orig)
        base_w = int(base_w_orig * scale_factor)
        base_h = int(base_h_orig * scale_factor)
        scaled_padding = int(layer_padding * scale_factor)
        scaled_radius = int(radius * scale_factor)

        final_width = base_w + num_bg_layers * 2 * scaled_padding
        final_height = base_h + num_bg_layers * 2 * scaled_padding

        final_image = Image.new("RGBA", (final_width, final_height), (0,0,0,0))
        
        for i in reversed(range(num_bg_layers)):
            layer_color = self.background_layers[i]['color']
            layer_w = base_w + (i + 1) * 2 * scaled_padding
            layer_h = base_h + (i + 1) * 2 * scaled_padding
            layer_r = scaled_radius + (i + 1) * scaled_padding
            
            grad = generate_rounded_gradient_image(layer_w, layer_h, layer_color, self.end_color_factor, self.direction_combo.get(), layer_r)
            px = (final_width - layer_w) // 2
            py = (final_height - layer_h) // 2
            final_image.paste(grad, (px, py), grad)

        main_grad = generate_rounded_gradient_image(base_w, base_h, self.start_color, self.end_color_factor, self.direction_combo.get(), scaled_radius)
        px = (final_width - base_w) // 2
        py = (final_height - base_h) // 2
        final_image.paste(main_grad, (px, py), main_grad)

        if self.overlay_pil_image_original:
            overlay_copy = self.overlay_pil_image_original.copy()
            ratio = min((base_w * (self.overlay_scale_var.get() / 100.0)) / overlay_copy.width, (base_h * (self.overlay_scale_var.get() / 100.0)) / overlay_copy.height)
            new_size = (int(overlay_copy.width * ratio), int(overlay_copy.height * ratio))
            if new_size[0] > 0 and new_size[1] > 0:
                resized = overlay_copy.resize(new_size, Image.Resampling.LANCZOS)
                processed = apply_overlay_effects_process(resized, self.overlay_recolor_hex, self.overlay_invert)
                px = (final_width - processed.width) // 2
                py = (final_height - processed.height) // 2
                final_image.paste(processed, (px, py), processed)
        
        final_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return final_image
    
    def start_generation_process(self):
        try:
            width, height = int(self.width_entry.get()), int(self.height_entry.get())
            if width <= 0 or height <= 0: raise ValueError
            save_path = self.get_save_path()
            if not save_path:
                self.status_label.configure(text="❌ Génération annulée")
                return
            
            self._toggle_ui_elements(state='disabled')
            self.generate_button.configure(text="❌ Annuler la génération", command=self.cancel_generation,
                                           fg_color="#D73A49", hover_color="#B83241")
            self.status_label.configure(text="Lancement du processus...", text_color="gray")
            self.progress_bar.pack(fill='x', pady=(10, 5))
            self.cpu_label.pack()
            self.progress_bar.set(0)
            self.is_generating = True
            self._update_cpu_usage()
            
            self.queue = multiprocessing.Queue()
            process_args = (
                self.queue, self.start_color, self.end_color_factor, width, height, self.format_combo.get(),
                self.direction_combo.get(), self.corner_radius_var.get(), save_path,
                self.overlay_image_path, self.overlay_scale_var.get() / 100.0,
                self.overlay_recolor_hex, self.overlay_invert,
                self.background_layers, self.layer_padding_var.get()
            )
            self.process = multiprocessing.Process(target=create_gradient_image_manager, args=process_args)
            self.process.start()
            self.after(100, self.check_process_queue)
        except ValueError:
            self.status_label.configure(text="❌ Erreur : Dimensions invalides")

    def cancel_generation(self):
        if self.is_generating and self.process and self.process.is_alive():
            self.process.terminate()
            self.after(100, self._reset_ui_after_generation, "Génération annulée.", "gray")

    def check_process_queue(self):
        try:
            message_type, data = self.queue.get_nowait()
            if message_type == 'progress':
                self.progress_bar.set(data / 100.0)
                self.status_label.configure(text=f"Création de l'image en cours... {int(data)}%")
                self.after(100, self.check_process_queue)
            elif message_type == 'done':
                self.on_generation_complete(data)
            elif message_type == 'error':
                self.on_generation_failed(data)
        except queue.Empty:
            if self.is_generating:
                self.after(100, self.check_process_queue)
        except (ValueError, TypeError):
             if self.is_generating:
                self.after(100, self.check_process_queue)

    def get_save_path(self):
        file_format = self.format_combo.get()
        file_types = {
            "PNG": ("PNG", "*.png"), "JPG": ("JPEG", "*.jpg;*.jpeg"), "BMP": ("Bitmap", "*.bmp"),
            "WEBP": ("WebP", "*.webp"), "TIFF": ("TIFF", "*.tiff;*.tif"), "GIF": ("GIF", "*.gif"),
            "ICO": ("Icon", "*.ico"), "TGA": ("Targa", "*.tga")
        }
        description, extension = file_types.get(file_format, ("All files", "*.*"))
        
        num_layers = len(self.background_layers)
        padding = self.layer_padding_var.get()
        try:
            width = int(self.width_entry.get()) + num_layers * 2 * padding
            height = int(self.height_entry.get()) + num_layers * 2 * padding
        except ValueError:
            width, height = "invalid", "dims"

        default_name = f"gradient_{width}x{height}{extension.split(';')[0].replace('*', '')}"
        return filedialog.asksaveasfilename(initialdir=self.default_save_dir, initialfile=default_name,
            defaultextension=extension, filetypes=[(description, extension), ("All files", "*.*")])

    def _reset_ui_after_generation(self, status_text="", text_color="gray"):
        self.is_generating = False
        if self.after_id_cpu:
            self.after_cancel(self.after_id_cpu)
            self.after_id_cpu = None

        self.status_label.configure(text=status_text, text_color=text_color)
        self._toggle_ui_elements(state='normal')
        self.generate_button.configure(text="🚀 Générer l'image", command=self.start_generation_process,
                                       fg_color=self.selected_color_hex, 
                                       hover_color=self.rgb_to_hex(self.calculate_darker_color(self.hex_to_rgb(self.selected_color_hex), 0.8)))
        self.progress_bar.pack_forget()
        self.cpu_label.pack_forget()
        
    def on_generation_complete(self, save_path):
        self.progress_bar.set(1)
        self._reset_ui_after_generation(f"✅ Image sauvegardée : {os.path.basename(save_path)}", "lightgreen")
    
    def on_generation_failed(self, error_message):
        self._reset_ui_after_generation(f"❌ {error_message}", "red")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = GradientApp()
    app.mainloop()