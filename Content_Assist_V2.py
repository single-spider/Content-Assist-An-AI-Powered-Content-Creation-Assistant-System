import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog, font as tkfont, colorchooser, filedialog
import google.generativeai as genai
import google.api_core.exceptions
import json
import os
import threading
from PIL import Image
import shutil
import datetime
import time
import requests

# --- Configuration ---
APP_NAME = "AI Content Assistant - By Abstracto"
DATA_FILE = "ai_assistant_data_v2_1.json"
DEFAULT_FOLDER_NAME = "Story Line"
DEFAULT_MODEL = "gemini-1.5-flash-latest"
DEFAULT_API_PROVIDER = "google"
ICONS_FOLDER = "icons"
BACKUP_FOLDER = "backups"
MAX_BACKUPS = 10
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Define expected icon filenames (add more if you use them)
ICON_FILENAMES = {
    "folder": "folder.png",
    "page": "page.png",
    "add": "add.png",
    "delete": "delete.png",
    "settings": "settings.png",
    "bold": "bold.png",
    "italic": "italic.png",
    "underline": "underline.png",
    "refresh": "refresh.png",
    "save": "save.png",
    "load": "load.png",
    "clear": "clear.png",
}

# --- Helper Function for Icons (using CTkImage) ---
def load_icon_ctk(filename_key, size=(16, 16)):
    """Loads an icon and returns a CTkImage."""
    filename = ICON_FILENAMES.get(filename_key, f"{filename_key}.png")
    path = os.path.join(ICONS_FOLDER, filename)
    try:
        img = Image.open(path)
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except FileNotFoundError:
        print(f"Warning: Icon file not found: {path}")
        try:
            placeholder_img = Image.new('RGBA', size, (0,0,0,0))
            return ctk.CTkImage(light_image=placeholder_img, dark_image=placeholder_img, size=size)
        except Exception as e:
            print(f"Error creating placeholder icon: {e}")
            return None
    except Exception as e:
        print(f"Error loading icon {filename}: {e}")
        return None


# --- Application State Management ---
class AppState:
    def __init__(self, filename=DATA_FILE):
        self.filename = os.path.abspath(filename)
        self.data = {
            "api_keys": {},
            "selected_api_key_name": None,
            "selected_model_name": DEFAULT_MODEL,
            "appearance_mode": "System",
            "folders": {},
            "references": {},
            "api_provider": DEFAULT_API_PROVIDER,
            "show_free_models_only": True
        }
        if not self.load_data():
            if not self.data["folders"]:
                self.add_folder(DEFAULT_FOLDER_NAME, initialize_default=True)
            if not self.data["api_keys"]:
                self.data["api_keys"]["Default Key"] = ""
                self.data["selected_api_key_name"] = "Default Key"

    def get_api_provider(self):
        return self.data.get("api_provider", DEFAULT_API_PROVIDER)
    
    def set_api_provider(self, provider):
        if provider in ["google", "openrouter"]:
            self.data["api_provider"] = provider
            self.save_data()
            return True
        return False
    
    def get_show_free_models_only(self):
        return self.data.get("show_free_models_only", True)
    
    def set_show_free_models_only(self, value):
        self.data["show_free_models_only"] = bool(value)
        self.save_data()

    # --- Backup ---
    def create_backup(self, max_backups=MAX_BACKUPS):
        """Creates a timestamped backup of the current data file."""
        if not os.path.exists(self.filename):
            print("Backup skipped: Main data file does not exist yet.")
            return

        if not os.path.exists(BACKUP_FOLDER):
            try:
                os.makedirs(BACKUP_FOLDER)
                print(f"Created backup directory: {BACKUP_FOLDER}")
            except OSError as e:
                print(f"Error creating backup directory {BACKUP_FOLDER}: {e}")
                return

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = os.path.basename(self.filename)
            backup_filename = f"{base_filename}.{timestamp}.bak"
            backup_path = os.path.join(BACKUP_FOLDER, backup_filename)

            shutil.copy2(self.filename, backup_path)
            print(f"Backup created: {backup_path}")

            backups = sorted(
                [os.path.join(BACKUP_FOLDER, f) for f in os.listdir(BACKUP_FOLDER) if f.startswith(base_filename) and f.endswith(".bak")],
                key=os.path.getmtime
            )

            if len(backups) > max_backups:
                num_to_delete = len(backups) - max_backups
                for i in range(num_to_delete):
                    try:
                        os.remove(backups[i])
                        print(f"Deleted old backup: {backups[i]}")
                    except OSError as e:
                        print(f"Error deleting old backup {backups[i]}: {e}")

        except Exception as e:
            print(f"Error during backup creation or cleanup: {e}")


    def get_appearance_mode(self):
        return self.data.get("appearance_mode", "System")

    def set_appearance_mode(self, mode):
        if mode in ["System", "Light", "Dark"]:
            self.data["appearance_mode"] = mode
            self.save_data()
            return True
        return False

    def load_data(self):
        """Loads data from self.filename."""
        print(f"Loading data from: {self.filename}")
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                print(f"Successfully loaded data: {loaded_data.keys()}")
                
                if "folders" in loaded_data:
                    self.data["folders"] = loaded_data["folders"]
                    print(f"Loaded folders: {list(self.data['folders'].keys())}")
                
                if "api_keys" in loaded_data:
                    self.data["api_keys"] = loaded_data["api_keys"]
                
                if "selected_api_key_name" in loaded_data:
                    self.data["selected_api_key_name"] = loaded_data["selected_api_key_name"]
                
                if "selected_model_name" in loaded_data:
                    self.data["selected_model_name"] = loaded_data["selected_model_name"]
                
                if "appearance_mode" in loaded_data:
                    self.data["appearance_mode"] = loaded_data["appearance_mode"]
                
                if "references" in loaded_data:
                    self.data["references"] = loaded_data["references"]
                
                if "api_provider" in loaded_data:
                    self.data["api_provider"] = loaded_data["api_provider"]
                
                if "show_free_models_only" in loaded_data:
                    self.data["show_free_models_only"] = loaded_data["show_free_models_only"]
                
                return True
            except Exception as e:
                print(f"Error loading data: {e}")
                return False
        else:
            print(f"Data file not found: {self.filename}")
            return False

    def save_data(self):
        """Saves data to self.filename."""
        try:
            if self.data["selected_api_key_name"] not in self.data["api_keys"] and self.data["selected_api_key_name"] is not None:
                 self.data["selected_api_key_name"] = next(iter(self.data["api_keys"]), None) if self.data["api_keys"] else None

            directory = os.path.dirname(self.filename)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving data to {self.filename}: {e}")
            messagebox.showerror("Save Error", f"Could not save data to {self.filename}:\n{e}", parent=None)
        except Exception as e:
             print(f"Unexpected error saving data to {self.filename}: {e}")
             messagebox.showerror("Save Error", f"An unexpected error occurred while saving to {self.filename}:\n{e}", parent=None)


    # --- API Key Management (unchanged) ---
    def get_api_key_names(self):
        return list(self.data["api_keys"].keys())

    def get_api_key_value(self, key_name):
        return self.data["api_keys"].get(key_name, "")

    def add_or_update_api_key(self, key_name, key_value):
        key_name = key_name.strip()
        if key_name:
            self.data["api_keys"][key_name] = key_value.strip()
            if len(self.data["api_keys"]) == 1 or self.data["selected_api_key_name"] is None:
                self.set_selected_api_key_name(key_name)
            self.save_data()
            return True
        return False

    def delete_api_key(self, key_name):
         if key_name in self.data["api_keys"]:
             if len(self.data["api_keys"]) == 1:
                  pass

             del self.data["api_keys"][key_name]
             if self.data["selected_api_key_name"] == key_name:
                 self.data["selected_api_key_name"] = next(iter(self.data["api_keys"]), None) if self.data["api_keys"] else None
             self.save_data()
             return True
         return False

    def set_selected_api_key_name(self, key_name):
         if key_name in self.data["api_keys"] or key_name is None:
             self.data["selected_api_key_name"] = key_name
             self.save_data()
             return True
         return False

    def get_selected_api_key_name(self):
         if self.data["selected_api_key_name"] not in self.data["api_keys"] and self.data["selected_api_key_name"] is not None:
              first_key = next(iter(self.data["api_keys"]), None) if self.data["api_keys"] else None
              self.data["selected_api_key_name"] = first_key
         return self.data["selected_api_key_name"]

    def get_selected_api_key_value(self):
        key_name = self.get_selected_api_key_name()
        return self.get_api_key_value(key_name) if key_name else ""

    # --- Model Management (unchanged) ---
    def set_selected_model(self, model_name):
        self.data["selected_model_name"] = model_name
        self.save_data()

    def get_selected_model(self):
        return self.data.get("selected_model_name", DEFAULT_MODEL)

    # --- Folder/Page/Function Management (unchanged structure, save calls already present) ---
    def get_folders(self):
        return list(self.data["folders"].keys())

    def add_folder(self, folder_name, initialize_default=False):
        folder_name = folder_name.strip()
        if folder_name and folder_name not in self.data["folders"]:
            self.data["folders"][folder_name] = {"pages": {}, "functions": {}}
            if initialize_default:
                self.data["folders"][folder_name]["functions"] = {
                    "Summarize": "Summarize the following text concisely:",
                    "Describe Scene": "Expand the following scene description with more sensory details (sight, sound, smell, touch) and atmosphere:",
                    "Generate Dialogue": "Write realistic dialogue between [Character A] and [Character B] based on the following context. Ensure their voices are distinct:\nContext:",
                    "Improve Flow": "Rewrite the following text to improve the flow, transitions, and readability:",
                    "Show, Don't Tell": "Rewrite the following sentence(s) to 'show' the emotion/action rather than 'telling' it:",
                    "Character Reaction": "Describe how [Character Name] would realistically react emotionally and physically to the preceding events:",
                    "Suggest Twist": "Based on the preceding text, suggest one surprising but plausible plot twist or complication:",
                    "Fix Grammar": "Correct any grammar and spelling errors in the following text:",
                }
            self.save_data()
            return True
        return False

    def delete_folder(self, folder_name):
         if folder_name in self.data["folders"]:
             if len(self.data["folders"]) == 1:
                 return False

             del self.data["folders"][folder_name]
             self.save_data()
             return True
         return False

    def get_pages(self, folder_name):
        return list(self.data["folders"].get(folder_name, {}).get("pages", {}).keys())

    def add_page(self, folder_name, page_name):
        page_name = page_name.strip()
        if folder_name in self.data["folders"] and page_name and page_name not in self.data["folders"][folder_name]["pages"]:
            self.data["folders"][folder_name]["pages"][page_name] = {"content": [], "notes": ""}
            self.save_data()
            return True
        return False

    def delete_page(self, folder_name, page_name):
        if folder_name in self.data["folders"] and page_name in self.data["folders"][folder_name]["pages"]:
            del self.data["folders"][folder_name]["pages"][page_name]
            self.save_data()
            return True
        return False

    def get_page_content(self, folder_name, page_name):
        """Gets the content for a specific page, handling both old and new formats."""
        try:
            page_data = self.data["folders"].get(folder_name, {}).get("pages", {}).get(page_name, {})
            
            if isinstance(page_data, list):
                return page_data
            elif isinstance(page_data, dict):
                return page_data.get("content", [])
            else:
                return []
        except Exception as e:
            print(f"Error getting page content: {e}")
            return []
    def update_page_content(self, folder_name, page_name, rich_content_dump):
        if folder_name in self.data["folders"] and page_name in self.data["folders"][folder_name]["pages"]:
            if isinstance(self.data["folders"][folder_name]["pages"][page_name], dict):
                 self.data["folders"][folder_name]["pages"][page_name]["content"] = rich_content_dump
            else:
                 self.data["folders"][folder_name]["pages"][page_name] = {"content": rich_content_dump, "notes": ""}
            self.save_data()
            return True
        return False

    def get_page_notes(self, folder_name, page_name):
        page_data = self.data["folders"].get(folder_name, {}).get("pages", {}).get(page_name, {})
        return page_data.get("notes", "")

    def update_page_notes(self, folder_name, page_name, notes):
        if folder_name in self.data["folders"] and page_name in self.data["folders"][folder_name]["pages"]:
             if isinstance(self.data["folders"][folder_name]["pages"][page_name], dict):
                 self.data["folders"][folder_name]["pages"][page_name]["notes"] = notes
                 self.save_data()
                 return True
        return False

    def get_functions(self, folder_name):
        return self.data["folders"].get(folder_name, {}).get("functions", {})

    def add_or_update_function(self, folder_name, func_name, system_prompt):
        func_name = func_name.strip()
        if folder_name in self.data["folders"] and func_name:
            if "functions" not in self.data["folders"][folder_name]:
                self.data["folders"][folder_name]["functions"] = {}
            self.data["folders"][folder_name]["functions"][func_name] = system_prompt.strip()
            self.save_data()
            return True
        return False

    def delete_function(self, folder_name, func_name):
        if folder_name in self.data["folders"] and "functions" in self.data["folders"][folder_name] and func_name in self.data["folders"][folder_name]["functions"]:
            del self.data["folders"][folder_name]["functions"][func_name]
            self.save_data()
            return True
        return False

    def add_reference(self, folder_name, page_name):
        """Adds a page to the references list."""
        ref_key = f"{folder_name}/{page_name}"
        if ref_key not in self.data.get("references", {}):
            if not self.data.get("references"):
                self.data["references"] = {}
            self.data["references"][ref_key] = {"folder": folder_name, "page": page_name}
            self.save_data()
            return True
        return False

    def remove_reference(self, folder_name, page_name):
        """Removes a page from the references list."""
        ref_key = f"{folder_name}/{page_name}"
        if ref_key in self.data.get("references", {}):
            del self.data["references"][ref_key]
            self.save_data()
            return True
        return False

    def get_references(self):
        """Returns the list of reference pages."""
        return self.data.get("references", {})


# --- Main Application UI ---
class App(ctk.CTk):
    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.current_folder = None
        self.current_page = None
        self.ai_is_running = False
        self.available_models = []
        self.folder_expanded_state = {}
        self.search_results = set()
        self._last_saved_content_dump = None

        self.update_title()

        self.geometry("1200x800")

        ctk.set_appearance_mode(self.app_state.get_appearance_mode())
        ctk.set_default_color_theme("blue")

        self.icon_folder = load_icon_ctk("folder", size=(18, 18))
        self.icon_page = load_icon_ctk("page", size=(18, 18))
        self.icon_add = load_icon_ctk("add", size=(18, 18))
        self.icon_delete = load_icon_ctk("delete", size=(18, 18))
        self.icon_settings = load_icon_ctk("settings", size=(18, 18))
        self.icon_bold = load_icon_ctk("bold", size=(18, 18))
        self.icon_italic = load_icon_ctk("italic", size=(18, 18))
        self.icon_underline = load_icon_ctk("underline", size=(18, 18))
        self.icon_refresh = load_icon_ctk("refresh", size=(18, 18))
        self.icon_save = load_icon_ctk("save", size=(18, 18))
        self.icon_load = load_icon_ctk("load", size=(18, 18))
        self.icon_clear = load_icon_ctk("clear", size=(14, 14))

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        self.sidebar_label = ctk.CTkLabel(self.sidebar_frame, text="Navigator", font=ctk.CTkFont(size=18, weight="bold"))
        self.sidebar_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.search_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.search_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search pages...")
        self.search_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.search_entry.bind("<Return>", self.perform_search)
        self.search_entry.bind("<KeyRelease>", self.perform_search)

        self.clear_search_button = ctk.CTkButton(
            self.search_frame, text="", image=self.icon_clear, width=28, height=28,
            command=self.clear_search, fg_color="transparent", hover=False, border_width=0
        )
        self.clear_search_button.grid(row=0, column=1, padx=(0,0))

        self.folder_page_frame = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="")
        self.folder_page_frame.grid(row=2, column=0, padx=10, pady=0, sticky="nsew")
        self.folder_page_frame.grid_columnconfigure(0, weight=1)

        self.references_frame = ctk.CTkFrame(self.sidebar_frame)
        self.references_frame.grid(row=3, column=0, padx=10, pady=(5,0), sticky="ew")
        self.references_frame.grid_columnconfigure(0, weight=1)

        self.references_label = ctk.CTkLabel(self.references_frame, text="References:", font=ctk.CTkFont(weight="bold"))
        self.references_label.grid(row=0, column=0, padx=5, pady=(5,0), sticky="w")

        self.references_list = ctk.CTkScrollableFrame(self.references_frame, height=100)
        self.references_list.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        self.sidebar_buttons_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_buttons_frame.grid(row=4, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.sidebar_buttons_frame.grid_columnconfigure((0, 1), weight=1)

        self.add_folder_button = ctk.CTkButton(self.sidebar_buttons_frame, text=" Folder", image=self.icon_add, compound="left", command=self.add_folder_dialog)
        self.add_folder_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.add_page_button = ctk.CTkButton(self.sidebar_buttons_frame, text=" Page", image=self.icon_add, compound="left", command=self.add_page_dialog, state="disabled")
        self.add_page_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        delete_color = "#D32F2F"
        delete_hover = "#C62828"

        self.delete_folder_button = ctk.CTkButton(
            self.sidebar_buttons_frame, text=" Folder", image=self.icon_delete, compound="left",
            command=self.delete_folder, fg_color=delete_color, hover_color=delete_hover, state="disabled"
        )
        self.delete_folder_button.grid(row=1, column=0, padx=(0, 5), pady=(5,0), sticky="ew")

        self.delete_page_button = ctk.CTkButton(
            self.sidebar_buttons_frame, text=" Page", image=self.icon_delete, compound="left",
            command=self.delete_page, fg_color=delete_color, hover_color=delete_hover, state="disabled"
        )
        self.delete_page_button.grid(row=1, column=1, padx=(5, 0), pady=(5,0), sticky="ew")

        self.file_mgmt_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.file_mgmt_frame.grid(row=5, column=0, padx=10, pady=(10, 10), sticky="ew")
        self.file_mgmt_frame.grid_columnconfigure(0, weight=1)

        self.save_as_button = ctk.CTkButton(self.file_mgmt_frame, text=" Save Project As...", image=self.icon_save, compound="left", command=self.save_project_as)
        self.save_as_button.grid(row=0, column=0, padx=5, pady=3, sticky="ew")

        self.load_button = ctk.CTkButton(self.file_mgmt_frame, text=" Load Project...", image=self.icon_load, compound="left", command=self.load_project)
        self.load_button.grid(row=1, column=0, padx=5, pady=3, sticky="ew")

        self.settings_button = ctk.CTkButton(self.file_mgmt_frame, text=" Settings", image=self.icon_settings, compound="left", command=self.open_settings)
        self.settings_button.grid(row=2, column=0, padx=5, pady=(10, 5), sticky="ew")

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=5, pady=5)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.function_bar_frame = ctk.CTkFrame(self.main_frame)
        self.function_bar_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="new")

        self.format_toolbar = ctk.CTkFrame(self.main_frame, height=35)
        self.format_toolbar.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="new")
        self._create_format_toolbar()

        text_bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkTextbox"]["fg_color"])
        text_fg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkTextbox"]["text_color"])
        text_border_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkTextbox"]["border_color"])
        text_insert_color = text_fg_color
        text_select_fg_color = text_fg_color
        text_select_bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        self.workspace = tk.Text(
            self.main_frame,
            wrap=tk.WORD,
            undo=True,
            padx=10,
            pady=10,
            font=ctk.CTkFont(family="sans-serif", size=14).actual(),
            background=text_bg_color,
            foreground=text_fg_color,
            borderwidth=ctk.ThemeManager.theme["CTkTextbox"]["border_width"],
            relief=tk.FLAT,
            highlightthickness=ctk.ThemeManager.theme["CTkTextbox"]["border_width"],
            highlightbackground=text_border_color,
            highlightcolor=text_border_color,
            insertbackground=text_insert_color,
            selectforeground=text_select_fg_color,
            selectbackground=text_select_bg_color
        )
        self.workspace.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.workspace.bind("<KeyRelease>", self.on_text_change)
        self.workspace.bind("<ButtonRelease-1>", lambda e: self.after(50, self.update_word_count))
        self.workspace.configure(state="disabled")

        bold_font_props = ctk.CTkFont(family="sans-serif", size=14, weight="bold").actual()
        italic_font_props = ctk.CTkFont(family="sans-serif", size=14, slant="italic").actual()
        bold_italic_font_props = ctk.CTkFont(family="sans-serif", size=14, weight="bold", slant="italic").actual()
        self.workspace.tag_configure("bold", font=bold_font_props)
        self.workspace.tag_configure("italic", font=italic_font_props)
        self.workspace.tag_configure("underline", underline=True)
        self.workspace.tag_configure("bold_italic", font=bold_italic_font_props)
        sep_font_props = ctk.CTkFont(slant="italic", size=12).actual()
        sep_color = self._apply_appearance_mode(("#005588", "#88CCFF"))
        self.workspace.tag_configure("ai_separator", font=sep_font_props, foreground=sep_color)
        self.workspace.bind("<<Modified>>", self.interpret_markdown)
        
        bold_font = ctk.CTkFont(family="sans-serif", size=14, weight="bold").actual()
        italic_font = ctk.CTkFont(family="sans-serif", size=14, slant="italic").actual()
        bold_italic_font = ctk.CTkFont(family="sans-serif", size=14, weight="bold", slant="italic").actual()
        
        self.workspace.tag_configure("bold", font=bold_font)
        self.workspace.tag_configure("italic", font=italic_font)
        self.workspace.tag_configure("bold_italic", font=bold_italic_font)
        self.workspace.tag_configure("underline", underline=True)

        self.status_bar_frame = ctk.CTkFrame(self.main_frame, height=25, fg_color="transparent")
        self.status_bar_frame.grid(row=3, column=0, padx=10, pady=(0,5), sticky="ew")
        self.status_bar_frame.grid_columnconfigure(0, weight=1)

        self.status_bar = ctk.CTkLabel(self.status_bar_frame, text="Ready.", anchor="w", font=ctk.CTkFont(size=12))
        self.status_bar.grid(row=0, column=0, sticky="ew")

        self.word_count_label = ctk.CTkLabel(self.status_bar_frame, text="", anchor="e", font=ctk.CTkFont(size=12))
        self.word_count_label.grid(row=0, column=1, padx=(10, 0), sticky="e")

        self.update_sidebar()
        folders = self.app_state.get_folders()
        if folders:
            first_folder = sorted(folders)[0]
            self.select_folder(first_folder)
        else:
             self.update_function_bar()

    def update_title(self):
        """Updates the window title based on the current project file."""
        proj_name = os.path.basename(self.app_state.filename)
        self.title(f"{APP_NAME} - {proj_name}")

    def interpret_markdown(self, event=None):
        """Interprets basic Markdown syntax and applies text tags."""
        if not self.current_page or self.workspace.cget("state") == "disabled":
            return

        cursor_pos = self.workspace.index(tk.INSERT)
        
        for tag in ["bold", "italic", "bold_italic"]:
            self.workspace.tag_remove(tag, "1.0", tk.END)
        
        content = self.workspace.get("1.0", tk.END)
        
        patterns = [
            (r'\*\*\*(.*?)\*\*\*', "bold_italic"),
            (r'\*\*(.*?)\*\*', "bold"),
            (r'__(.*?)__', "bold"),
            (r'\*(.*?)\*', "italic"),
            (r'_(.*?)_', "italic"),
        ]
        
        for pattern, tag in patterns:
            start_idx = "1.0"
            while True:
                match_start = self.workspace.search(pattern, start_idx, tk.END, regexp=True)
                if not match_start:
                    break
                    
                match_end = self.workspace.search(
                    pattern.split(r"(.*?)")[1],
                    f"{match_start}+1c", 
                    tk.END,
                    regexp=True
                )
                
                if match_end:
                    content_start = f"{match_start}+{len(pattern.split('(')[0])}c"
                    content_end = match_end
                    self.workspace.tag_add(tag, content_start, content_end)
                    start_idx = f"{match_end}+1c"
                else:
                    break
        
        self.workspace.mark_set(tk.INSERT, cursor_pos)

    def configure_markdown_tags(self):
        bold_font = ctk.CTkFont(family="sans-serif", size=14, weight="bold")
        italic_font = ctk.CTkFont(family="sans-serif", size=14, slant="italic")
        bold_italic_font = ctk.CTkFont(family="sans-serif", size=14, weight="bold", slant="italic")
        
        self.workspace.tag_configure("bold", font=bold_font)
        self.workspace.tag_configure("italic", font=italic_font)
        self.workspace.tag_configure("bold_italic", font=bold_italic_font)
    def _create_format_toolbar(self):
        for widget in self.format_toolbar.winfo_children():
            widget.destroy()

        self.bold_button = ctk.CTkButton(
            self.format_toolbar, 
            text="B", 
            width=30,
            command=self.toggle_bold,
            font=ctk.CTkFont(weight="bold")
        )
        self.bold_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.italic_button = ctk.CTkButton(
            self.format_toolbar, 
            text="I", 
            width=30,
            command=self.toggle_italic,
            font=ctk.CTkFont(slant="italic")
        )
        self.italic_button.pack(side=tk.LEFT, padx=2, pady=2)

        self.underline_button = ctk.CTkButton(
            self.format_toolbar, 
            text="U", 
            width=30,
            command=self.toggle_underline,
            font=ctk.CTkFont(underline=True)
        )
        self.underline_button.pack(side=tk.LEFT, padx=2, pady=2)

    def toggle_format_toolbar(self, enabled=True):
        state = "normal" if enabled else "disabled"
        for widget in self.format_toolbar.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state=state)

    def _toggle_tag(self, tag_name):
        if not self.current_page: return
        try:
            if self.workspace.tag_ranges(tk.SEL):
                 selection_start = self.workspace.index(tk.SEL_FIRST)
                 selection_end = self.workspace.index(tk.SEL_LAST)
                 tags_at_start = self.workspace.tag_names(selection_start)
                 if tag_name in tags_at_start:
                     self.workspace.tag_remove(tag_name, selection_start, selection_end)
                 else:
                     self.workspace.tag_add(tag_name, selection_start, selection_end)
                 self.on_text_change()
            else:
                 pass
        except tk.TclError:
            pass

    def toggle_bold(self): self._toggle_tag("bold")
    def toggle_italic(self): self._toggle_tag("italic")
    def toggle_underline(self): self._toggle_tag("underline")

    def update_word_count(self, event=None):
        """Updates the word count label in the status bar."""
        if self.workspace.cget("state") == "disabled":
            self.word_count_label.configure(text="")
            return

        try:
            page_text = self.workspace.get("1.0", tk.END)
            page_word_count = len(page_text.split())

            selection_word_count = 0
            if self.workspace.tag_ranges(tk.SEL):
                selection_text = self.workspace.get(tk.SEL_FIRST, tk.SEL_LAST)
                selection_word_count = len(selection_text.split())

            if selection_word_count > 0:
                count_text = f"Sel: {selection_word_count} / Page: {page_word_count} words"
            else:
                count_text = f"Page: {page_word_count} words"

            self.word_count_label.configure(text=count_text)
        except tk.TclError:
            self.word_count_label.configure(text="")
        except Exception as e:
            print(f"Error updating word count: {e}")
            self.word_count_label.configure(text="WC Error")

    def _get_plain_text_content(self, folder_name, page_name):
        """Extracts plain text from a page's rich content dump."""
        try:
            rich_content_dump = self.app_state.get_page_content(folder_name, page_name)
            if rich_content_dump:
                plain_text = ""
                for item_type, value, index in rich_content_dump:
                    if item_type == "text":
                        plain_text += value
                if plain_text.endswith('\n'):
                    plain_text = plain_text[:-1]
                return plain_text
            return ""
        except Exception as e:
            print(f"Error getting plain text for {folder_name}/{page_name}: {e}")
            return ""

    def perform_search(self, event=None):
        """Performs search and updates sidebar highlights."""
        search_term = self.search_entry.get().strip()
        self.search_results.clear()

        if len(search_term) > 0:
            term_lower = search_term.lower()
            folders = self.app_state.get_folders()
            for folder in folders:
                pages = self.app_state.get_pages(folder)
                for page in pages:
                    page_text = self._get_plain_text_content(folder, page)
                    if term_lower in page_text.lower():
                        self.search_results.add((folder, page))

        self.update_sidebar()

    def clear_search(self):
        """Clears the search entry and results."""
        self.search_entry.delete(0, tk.END)
        self.search_results.clear()
        self.update_sidebar()

    def toggle_folder_expansion(self, folder_name):
        """Toggles the expanded/collapsed state of a folder."""
        current_state = self.folder_expanded_state.get(folder_name, True)
        self.folder_expanded_state[folder_name] = not current_state
        self.update_sidebar()

    def update_sidebar(self):
        for widget in self.folder_page_frame.winfo_children():
            widget.destroy()

        folders = self.app_state.get_folders()
        row_index = 0

        theme = ctk.ThemeManager.theme
        selected_fg_color = self._apply_appearance_mode(theme["CTkButton"]["fg_color"])
        normal_folder_fg_color = self._apply_appearance_mode(("gray75", "gray28"))
        normal_page_fg_color = self._apply_appearance_mode(("gray85", "gray35"))
        hover_color = self._apply_appearance_mode(theme["CTkButton"]["hover_color"])
        search_highlight_color = self._apply_appearance_mode(("#aaddff", "#005588"))

        for folder_name in sorted(folders):
            is_selected_folder = (folder_name == self.current_folder)
            is_expanded = self.folder_expanded_state.get(folder_name, True)

            fg_color = selected_fg_color if is_selected_folder else normal_folder_fg_color
            font_weight = "bold" if is_selected_folder else "normal"
            expand_indicator = "[-] " if is_expanded else "[+] "
            folder_display_text = f"{expand_indicator}{folder_name}"

            folder_button = ctk.CTkButton(
                self.folder_page_frame,
                text=folder_display_text,
                image=self.icon_folder,
                compound="left",
                command=lambda fn=folder_name: self.toggle_folder_expansion(fn) if not is_selected_folder else self.select_folder(fn),
                anchor="w",
                font=ctk.CTkFont(weight=font_weight),
                fg_color=fg_color,
                hover_color=hover_color
            )
            folder_button.bind("<Button-1>", lambda e, fn=folder_name: self.select_folder(fn))
            folder_button.grid(row=row_index, column=0, pady=(6, 2), padx=5, sticky="ew")
            row_index += 1

            if is_expanded:
                pages = self.app_state.get_pages(folder_name)
                for page_name in sorted(pages):
                     is_selected_page = (is_selected_folder and page_name == self.current_page)
                     is_search_match = (folder_name, page_name) in self.search_results

                     page_fg_color = normal_page_fg_color
                     if is_selected_page:
                         page_fg_color = selected_fg_color
                     elif is_search_match:
                         page_fg_color = search_highlight_color

                     page_button = ctk.CTkButton(
                         self.folder_page_frame,
                         text=f" {page_name}",
                         image=self.icon_page,
                         compound="left",
                         command=lambda fn=folder_name, pn=page_name: self.select_page(fn, pn),
                         anchor="w",
                         fg_color=page_fg_color,
                         text_color_disabled=self._apply_appearance_mode(theme["CTkButton"]["text_color_disabled"]),
                         height=26,
                         font=ctk.CTkFont(size=12),
                         hover_color=hover_color
                     )
                     page_button.grid(row=row_index, column=0, pady=1, padx=(25, 5), sticky="ew")

                     ref_button = ctk.CTkButton(
                         self.folder_page_frame,
                         text="📌",
                         width=20,
                         command=lambda fn=folder_name, pn=page_name: self.add_reference(fn, pn),
                     )
                     ref_button.grid(row=row_index, column=1, pady=1, padx=2)

                     row_index += 1

        can_add_page = self.current_folder is not None
        can_delete_folder = self.current_folder is not None and len(self.app_state.get_folders()) > 1
        can_delete_page = self.current_page is not None
        self.add_page_button.configure(state="normal" if can_add_page else "disabled")
        self.delete_folder_button.configure(state="normal" if can_delete_folder else "disabled")
        self.delete_page_button.configure(state="normal" if can_delete_page else "disabled")

        self.update_references_list()

    def update_references_list(self):
        """Updates the references list display."""
        for widget in self.references_list.winfo_children():
            widget.destroy()

        references = self.app_state.get_references()
        if not references:
            label = ctk.CTkLabel(self.references_list, text="No references added", text_color="gray")
            label.pack(pady=5)
            return

        for ref_key, ref_data in references.items():
            ref_frame = ctk.CTkFrame(self.references_list, fg_color="transparent")
            ref_frame.pack(fill="x", padx=2, pady=1)
            
            label = ctk.CTkLabel(ref_frame, text=f"📄 {ref_data['page']}", anchor="w")
            label.pack(side="left", padx=(5,0))
            
            remove_btn = ctk.CTkButton(
                ref_frame, text="×", width=20, height=20,
                command=lambda f=ref_data['folder'], p=ref_data['page']: self.remove_reference(f, p)
            )
            remove_btn.pack(side="right", padx=(5,0))

    def add_reference(self, folder_name, page_name):
        """Adds current page to references."""
        if self.app_state.add_reference(folder_name, page_name):
            self.update_references_list()

    def remove_reference(self, folder_name, page_name):
        """Removes a page from references."""
        if self.app_state.remove_reference(folder_name, page_name):
            self.update_references_list()

    def select_folder(self, folder_name):
        print(f"Selecting folder: {folder_name}")
        if self.current_page:
             if not self.save_current_page_content():
                 print("Save failed, aborting folder selection.")
                 return

        self.folder_expanded_state[folder_name] = True

        self.current_folder = folder_name
        self.current_page = None
        self.workspace.configure(state="normal")
        self.workspace.delete("1.0", tk.END)
        self.workspace.configure(state="disabled")
        self.toggle_format_toolbar(False)
        self.word_count_label.configure(text="")

        pages = self.app_state.get_pages(folder_name)
        self.update_sidebar()
        self.update_function_bar()

        if pages:
            first_page = sorted(pages)[0]
            self.select_page(folder_name, first_page)
        else:
            self.status_bar.configure(text=f"Folder: {folder_name} (No pages). Click '+ Page' to create one.")


    def select_page(self, folder_name, page_name):
        print(f"Selecting page: {folder_name} / {page_name}")

        if self.current_folder and self.current_page and \
           (self.current_folder != folder_name or self.current_page != page_name):
            if not self.save_current_page_content():
                print("Save failed, aborting page selection.")
                return

        self.current_folder = folder_name
        self.current_page = page_name

        rich_content_dump = self.app_state.get_page_content(folder_name, page_name)
        self._last_saved_content_dump = rich_content_dump

        self.workspace.configure(state="normal")
        self.workspace.delete("1.0", tk.END)

        try:
            if rich_content_dump:
                text_content = "".join(item[1] for item in rich_content_dump if item[0] == "text")
                if text_content.endswith('\n'):
                     text_content = text_content[:-1]
                self.workspace.insert("1.0", text_content)

                tag_ranges = {}
                tag_starts = {}

                sorted_dump = sorted(rich_content_dump, key=lambda x: self._tk_index_to_tuple(x[2]))

                for item_type, value, index_str in sorted_dump:
                    if item_type.startswith("tagon-"):
                        tag_name = item_type.split("-", 1)[1]
                        tag_starts[tag_name] = index_str
                    elif item_type.startswith("tagoff-"):
                        tag_name = item_type.split("-", 1)[1]
                        if tag_name in tag_starts:
                            start_index = tag_starts.pop(tag_name)
                            try:
                                start_tk = self.workspace.index(start_index)
                                end_tk = self.workspace.index(index_str)
                                if start_tk and end_tk:
                                    self.workspace.tag_add(tag_name, start_tk, end_tk)
                            except tk.TclError as e:
                                print(f"Warning: Invalid index during tag application for '{tag_name}': {start_index}-{index_str} ({e})")

            self.workspace.edit_reset()
            self.workspace.edit_modified(False)

        except Exception as e:
            print(f"Error loading rich text content for {folder_name}/{page_name}: {e}")
            messagebox.showerror("Load Error", f"Could not load content for '{page_name}'.\nError: {e}", parent=self)
            try:
                plain_text = self._get_plain_text_content(folder_name, page_name)
                self.workspace.insert("1.0", f"--- Error loading rich content. Raw text fallback: ---\n{plain_text}\n--- End Fallback ---")
            except Exception as fb_e:
                print(f"Error in fallback load: {fb_e}")
                self.workspace.insert("1.0", f"--- Error loading content. Could not extract raw text. ---\nError: {e}")

        self.update_sidebar()
        self.update_function_bar()
        self.toggle_format_toolbar(True)
        self.status_bar.configure(text=f"Editing: {folder_name} / {page_name}")
        self.update_word_count()


    def save_current_page_content(self):
        """Saves the rich text content of the current page to AppState."""
        if self.current_folder and self.current_page and self.workspace.cget("state") == "normal":
            try:
                raw_dump = self.workspace.dump("1.0", tk.END, text=True, tag=True, window=False)

                rich_content_dump = []
                current_text = ""
                last_index = "1.0"

                for key, value, index in raw_dump:
                    index_str = self.workspace.index(index)
                    if key == "text":
                        current_text += value
                        last_index = self.workspace.index(f"{index_str}+{len(value)}c")
                    elif key == "tagon":
                        if current_text:
                             rich_content_dump.append(("text", current_text, self.workspace.index(f"{last_index}-{len(current_text)}c")))
                             current_text = ""
                        rich_content_dump.append((f"tagon-{value}", "", index_str))
                        last_index = index_str
                    elif key == "tagoff":
                        if current_text:
                             rich_content_dump.append(("text", current_text, self.workspace.index(f"{last_index}-{len(current_text)}c")))
                             current_text = ""
                        rich_content_dump.append((f"tagoff-{value}", "", index_str))
                        last_index = index_str

                if current_text:
                    rich_content_dump.append(("text", current_text, self.workspace.index(f"{last_index}-{len(current_text)}c")))

                if not rich_content_dump and not self.workspace.get("1.0", "end-1c"):
                    rich_content_dump = [("text", "", "1.0")]

                if rich_content_dump == self._last_saved_content_dump:
                    return True

                success = self.app_state.update_page_content(
                    self.current_folder,
                    self.current_page,
                    rich_content_dump
                )
                if success:
                    self._last_saved_content_dump = rich_content_dump
                    self.workspace.edit_modified(False)
                    self.status_bar.configure(text=f"Saved: {self.current_folder} / {self.current_page}")
                    self.after(2000, self.clear_save_status)
                    return True
                else:
                    print(f"Error: Failed to save content for {self.current_folder}/{self.current_page} in AppState.")
                    self.status_bar.configure(text=f"Error saving: {self.current_folder} / {self.current_page}")
                    return False

            except tk.TclError as e:
                 print(f"Error dumping content from Text widget: {e}")
                 if "invalid command name" in str(e):
                     print("Workspace widget might be destroyed or invalid.")
                     return False
                 self.status_bar.configure(text=f"Error dumping content for save.")
                 return False
            except Exception as e:
                print(f"Error getting content dump or saving: {e}")
                self.status_bar.configure(text=f"Error saving: {self.current_folder} / {self.current_page}")
                return False
        elif not self.current_folder or not self.current_page:
            return True
        elif self.workspace.cget("state") == "disabled":
            return True
        return False


    def _tk_index_to_tuple(self, index):
        try:
            if isinstance(index, str):
                index = self.workspace.index(index)
                line, char = map(int, index.split('.'))
                return (line, char)
            elif isinstance(index, (tuple, list)) and len(index) == 2:
                 return tuple(index)
            return (0, 0)
        except Exception as e:
            print(f"Error converting index {index}: {e}")
            return (0, 0)

    def clear_save_status(self):
        current_status = self.status_bar.cget("text")
        if current_status.startswith("Saved:"):
            if self.current_folder and self.current_page:
                 self.status_bar.configure(text=f"Editing: {self.current_folder} / {self.current_page}")
            else:
                 self.status_bar.configure(text="Ready.")

    def on_text_change(self, event=None):
        """Handles text changes for saving and word count."""
        if self.workspace.edit_modified():
            self.save_current_page_content()
        self.update_word_count()

    def add_folder_dialog(self):
        dialog = ctk.CTkInputDialog(text="Enter new folder name:", title="Add Folder")
        folder_name = dialog.get_input()
        if folder_name:
            folder_name = folder_name.strip()
            if self.app_state.add_folder(folder_name):
                self.folder_expanded_state[folder_name] = True
                self.update_sidebar()
                self.select_folder(folder_name)
            else:
                messagebox.showwarning("Add Folder", f"Folder '{folder_name}' already exists or is invalid.", parent=self)

    def add_page_dialog(self):
        if not self.current_folder:
            messagebox.showwarning("Add Page", "Please select a folder first.", parent=self)
            return
        dialog = ctk.CTkInputDialog(text=f"Enter new page name for folder '{self.current_folder}':", title="Add Page")
        page_name = dialog.get_input()
        if page_name:
            page_name = page_name.strip()
            if self.app_state.add_page(self.current_folder, page_name):
                self.update_sidebar()
                self.select_page(self.current_folder, page_name)
            else:
                messagebox.showwarning("Add Page", f"Page '{page_name}' already exists or is invalid.", parent=self)

    def delete_folder(self):
        if not self.current_folder: return
        if len(self.app_state.get_folders()) <= 1:
             messagebox.showwarning("Cannot Delete", "You cannot delete the last folder.", parent=self)
             return

        if messagebox.askyesno("Delete Folder", f"🚨 Are you sure you want to permanently delete the folder '{self.current_folder}' and ALL its pages and functions?\nThis action cannot be undone.", icon='warning', parent=self):
             folder_to_delete = self.current_folder
             self.current_folder = None
             self.current_page = None
             self.workspace.configure(state="normal")
             self.workspace.delete("1.0", tk.END)
             self.workspace.configure(state="disabled")
             self.toggle_format_toolbar(False)
             self.word_count_label.configure(text="")

             if folder_to_delete in self.folder_expanded_state:
                 del self.folder_expanded_state[folder_to_delete]

             if self.app_state.delete_folder(folder_to_delete):
                 self.update_sidebar()
                 self.update_function_bar()
                 self.status_bar.configure(text="Folder deleted. Select or create a folder.")
                 remaining_folders = self.app_state.get_folders()
                 if remaining_folders:
                     self.select_folder(sorted(remaining_folders)[0])
             else:
                  messagebox.showerror("Delete Folder", f"Failed to delete folder '{folder_to_delete}'. It might be the last one.", parent=self)


    def delete_page(self):
        if not self.current_folder or not self.current_page: return
        if messagebox.askyesno("Delete Page", f"Are you sure you want to delete the page '{self.current_page}' from folder '{self.current_folder}'?\nThis action cannot be undone.", icon='warning', parent=self):
            folder = self.current_folder
            page_to_delete = self.current_page

            self.current_page = None
            self.workspace.configure(state="normal")
            self.workspace.delete("1.0", tk.END)
            self.workspace.configure(state="disabled")
            self.toggle_format_toolbar(False)
            self.word_count_label.configure(text="")

            if self.app_state.delete_page(folder, page_to_delete):
                 self.update_sidebar()
                 self.status_bar.configure(text=f"Page deleted. Select or create a page in '{folder}'.")
                 pages = self.app_state.get_pages(folder)
                 if pages:
                     self.select_page(folder, sorted(pages)[0])
                 else:
                      self.update_function_bar()
            else:
                 messagebox.showerror("Delete Page", f"Failed to delete page '{page_to_delete}'.", parent=self)

    def update_function_bar(self):
        for widget in self.function_bar_frame.winfo_children():
            widget.destroy()

        if not self.current_folder:
            label = ctk.CTkLabel(self.function_bar_frame, text="Select a folder to see AI functions", text_color=("gray50", "gray50"))
            label.pack(side=tk.LEFT, padx=5, pady=5)
            return

        manage_button_frame = ctk.CTkFrame(self.function_bar_frame, fg_color="transparent")
        manage_button_frame.pack(side=tk.RIGHT, padx=(10,0), pady=5)
        add_func_button = ctk.CTkButton(manage_button_frame, text="+ New", command=self.manage_functions_dialog, width=80)
        add_func_button.pack(side=tk.LEFT, padx=(0,5))
        edit_func_button = ctk.CTkButton(manage_button_frame, text="Manage", command=self.manage_functions_dialog, width=90)
        edit_func_button.pack(side=tk.LEFT)

        functions = self.app_state.get_functions(self.current_folder)
        page_selected = self.current_page is not None
        ai_button_state = "normal" if page_selected and not self.ai_is_running else "disabled"

        func_scroll_frame = ctk.CTkScrollableFrame(self.function_bar_frame, orientation="horizontal", height=40, fg_color="transparent", scrollbar_button_color=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"]), scrollbar_button_hover_color=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["hover_color"]))
        func_scroll_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=0)

        if not functions:
             no_func_label = ctk.CTkLabel(func_scroll_frame, text="No functions defined. Use 'Manage' to add.", text_color=("gray50", "gray50"))
             no_func_label.pack(side=tk.LEFT, padx=10)
        else:
            for func_name in sorted(functions.keys()):
                func_button = ctk.CTkButton(
                    func_scroll_frame,
                    text=func_name,
                    command=lambda fn=func_name: self.run_ai_function(fn),
                    state=ai_button_state
                )
                func_button.pack(side=tk.LEFT, padx=4, pady=5)

    def open_settings(self):
        settings_dialog = ctk.CTkToplevel(self)
        settings_dialog.title("Settings")
        settings_dialog.geometry("650x450")
        settings_dialog.transient(self)
        settings_dialog.grab_set()
        settings_dialog.attributes("-topmost", True)

        tab_view = ctk.CTkTabview(settings_dialog, width=630, height=380)
        tab_view.pack(padx=20, pady=(10, 0), fill="both", expand=True)
        tab_view.add("API Keys")
        tab_view.add("AI Model")

        self.create_api_keys_tab(tab_view.tab("API Keys"))
        self.create_ai_model_tab(tab_view.tab("AI Model"))

        close_button = ctk.CTkButton(settings_dialog, text="Close", command=settings_dialog.destroy, width=100)
        close_button.pack(pady=10)
        settings_dialog.wait_window()
        self.configure_genai()

    def create_api_keys_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)
        select_frame = ctk.CTkFrame(tab)
        select_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        select_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(select_frame, text="Active API Key:").grid(row=0, column=0, padx=(5, 10), pady=5, sticky="w")
        key_names = self.app_state.get_api_key_names()
        selected_key = self.app_state.get_selected_api_key_name()
        self.api_key_selector_var = ctk.StringVar(value=selected_key if selected_key in key_names else (key_names[0] if key_names else "No keys defined"))
        self.api_key_selector = ctk.CTkOptionMenu(
            select_frame, variable=self.api_key_selector_var,
            values=key_names if key_names else ["No keys defined"],
            command=self.on_select_api_key, state="normal" if key_names else "disabled"
        )
        self.api_key_selector.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        manage_frame = ctk.CTkScrollableFrame(tab, label_text="Manage API Keys")
        manage_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        manage_frame.grid_columnconfigure(1, weight=1)
        self.api_key_widgets = {}
        def _update_key_list():
            for name in list(self.api_key_widgets.keys()):
                 if name in self.api_key_widgets:
                    for widget in self.api_key_widgets[name]['widgets']:
                        if widget.winfo_exists(): widget.destroy()
                    del self.api_key_widgets[name]
            key_names = self.app_state.get_api_key_names()
            display_key_names = key_names if key_names else ["No keys defined"]
            self.api_key_selector.configure(values=display_key_names)
            selected_key = self.app_state.get_selected_api_key_name()
            if selected_key is not None:
                 self.api_key_selector_var.set(selected_key)
                 self.api_key_selector.configure(state="normal")
            else:
                 self.api_key_selector_var.set("No keys defined")
                 self.api_key_selector.configure(state="disabled")
            for i, name in enumerate(sorted(key_names)):
                key_value = self.app_state.get_api_key_value(name)
                row_frame = ctk.CTkFrame(manage_frame, fg_color="transparent")
                row_frame.grid(row=i, column=0, columnspan=3, pady=3, sticky="ew")
                row_frame.grid_columnconfigure(1, weight=1)
                name_label = ctk.CTkLabel(row_frame, text=name, width=150, anchor="w")
                name_label.grid(row=0, column=0, padx=5, pady=2)
                key_entry = ctk.CTkEntry(row_frame, show="*", width=200)
                key_entry.insert(0, key_value)
                key_entry.configure(state="readonly")
                key_entry.bind("<Button-1>", lambda e, k=name: _reveal_key(k))
                key_entry.bind("<FocusOut>", lambda e, k=name: _hide_key(k))
                key_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
                delete_button = ctk.CTkButton(
                    row_frame, text="", image=self.icon_delete, width=30,
                    command=lambda k=name: _delete_key(k),
                     fg_color="#D32F2F", hover_color="#C62828"
                )
                delete_button.grid(row=0, column=2, padx=(5,0), pady=2)
                self.api_key_widgets[name] = {'label': name_label, 'entry': key_entry, 'delete_btn': delete_button, 'widgets': [row_frame, name_label, key_entry, delete_button]}
        def _reveal_key(key_name):
             if key_name in self.api_key_widgets:
                 entry = self.api_key_widgets[key_name]['entry']
                 entry.configure(show="")
                 entry.configure(state="normal")
                 entry.focus()
                 entry.select_range(0, "end")
        def _hide_key(key_name):
             if key_name in self.api_key_widgets:
                 entry = self.api_key_widgets[key_name]['entry']
                 if entry.winfo_exists():
                     entry.configure(show="*")
                     entry.configure(state="readonly")
        def _delete_key(key_name):
            if len(self.app_state.get_api_key_names()) <= 1:
                 messagebox.showwarning("Cannot Delete", "You must keep at least one API key entry.", parent=tab.winfo_toplevel())
                 return
            if messagebox.askyesno("Delete API Key", f"Are you sure you want to delete the API key named '{key_name}'?", parent=tab.winfo_toplevel()):
                 if self.app_state.delete_api_key(key_name):
                     print(f"Deleted API key: {key_name}")
                     _update_key_list()
                 else:
                     messagebox.showerror("Error", f"Could not delete API key '{key_name}'.", parent=tab.winfo_toplevel())
        def _add_key():
            dialog = ctk.CTkInputDialog(text="Enter a unique name for the new API Key:", title="Add API Key")
            key_name = dialog.get_input()
            if key_name is None or not key_name.strip(): return
            key_name = key_name.strip()
            if key_name in self.app_state.get_api_key_names():
                messagebox.showwarning("Name Exists", f"An API Key named '{key_name}' already exists.", parent=tab.winfo_toplevel())
                return
            dialog_val = ctk.CTkInputDialog(text=f"Enter the API Key value for '{key_name}':", title="Add API Key Value")
            key_value = dialog_val.get_input()
            if key_value is not None:
                 if self.app_state.add_or_update_api_key(key_name, key_value):
                     print(f"Added API key: {key_name}")
                     _update_key_list()
                 else:
                     messagebox.showerror("Error", f"Could not add API key '{key_name}'.", parent=tab.winfo_toplevel())
        add_button_frame = ctk.CTkFrame(tab, fg_color="transparent")
        add_button_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="e")
        add_button = ctk.CTkButton(add_button_frame, text="Add New API Key", image=self.icon_add, compound="left", command=_add_key)
        add_button.pack()
        _update_key_list()

    def on_select_api_key(self, selected_key_name):
        print(f"Selected API key: {selected_key_name}")
        if selected_key_name != "No keys defined":
             self.app_state.set_selected_api_key_name(selected_key_name)
        else:
             self.app_state.set_selected_api_key_name(None)

    def create_ai_model_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=0)

        provider_frame = ctk.CTkFrame(tab)
        provider_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20,5), sticky="ew")
        
        ctk.CTkLabel(provider_frame, text="AI Provider:").pack(side=tk.LEFT, padx=(0,10))
        
        provider_var = ctk.StringVar(value=self.app_state.get_api_provider())
        google_radio = ctk.CTkRadioButton(
            provider_frame, text="Google AI", 
            variable=provider_var, value="google",
            command=lambda: self._on_provider_change(provider_var.get())
        )
        google_radio.pack(side=tk.LEFT, padx=10)
        
        openrouter_radio = ctk.CTkRadioButton(
            provider_frame, text="OpenRouter", 
            variable=provider_var, value="openrouter",
            command=lambda: self._on_provider_change(provider_var.get())
        )
        openrouter_radio.pack(side=tk.LEFT, padx=10)

        self.free_models_frame = ctk.CTkFrame(tab)
        self.free_models_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        
        self.free_models_var = ctk.BooleanVar(value=self.app_state.get_show_free_models_only())
        self.free_models_cb = ctk.CTkCheckBox(
            self.free_models_frame, 
            text="Show only free models",
            variable=self.free_models_var,
            command=self._on_free_models_toggle
        )
        self.free_models_cb.pack(side=tk.LEFT)
        
        self._update_free_models_visibility(provider_var.get())

        # Add search frame
        search_frame = ctk.CTkFrame(tab)
        search_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self.model_search_var = ctk.StringVar()
        self.model_search_var.trace_add("write", self._filter_models)
        
        search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Search models...",
            textvariable=self.model_search_var
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        clear_search_btn = ctk.CTkButton(
            search_frame,
            text="✕",
            width=30,
            command=self._clear_model_search
        )
        clear_search_btn.grid(row=0, column=1)

        # Model list frame
        model_list_frame = ctk.CTkFrame(tab)
        model_list_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=5, sticky="nsew")
        model_list_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

        # Scrollable model list
        self.model_list = ctk.CTkScrollableFrame(model_list_frame)
        self.model_list.grid(row=0, column=0, sticky="nsew")
        self.model_list.grid_columnconfigure(0, weight=1)

        # Selected model display
        selected_frame = ctk.CTkFrame(tab)
        selected_frame.grid(row=4, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        
        ctk.CTkLabel(selected_frame, text="Selected Model:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.selected_model_label = ctk.CTkLabel(
            selected_frame, 
            text=self.app_state.get_selected_model(),
            font=ctk.CTkFont(weight="bold")
        )
        self.selected_model_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Status and refresh
        status_frame = ctk.CTkFrame(tab)
        status_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)

        self.model_status_label = ctk.CTkLabel(
            status_frame, 
            text="Click 'Refresh List' to load available models.", 
            text_color="gray"
        )
        self.model_status_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        refresh_button = ctk.CTkButton(
            status_frame, 
            text="Refresh List", 
            image=self.icon_refresh, 
            compound="left", 
            command=lambda: self.fetch_models(tab)
        )
        refresh_button.grid(row=0, column=1, padx=5, pady=5)

        self.after(100, lambda: self.fetch_models(tab))

    def _filter_models(self, *args):
        """Filters the model list based on search text."""
        search_text = self.model_search_var.get().lower()
        
        # Clear existing model buttons
        for widget in self.model_list.winfo_children():
            widget.destroy()

        # Filter and display models
        filtered_models = [
            model for model in self.available_models 
            if search_text in model.lower()
        ]

        for i, model in enumerate(filtered_models):
            is_selected = model == self.app_state.get_selected_model()
            btn = ctk.CTkButton(
                self.model_list,
                text=model,
                command=lambda m=model: self._select_model_from_list(m),
                fg_color=("blue" if is_selected else "transparent"),
                anchor="w"
            )
            btn.grid(row=i, column=0, padx=5, pady=2, sticky="ew")

    def _clear_model_search(self):
        """Clears the model search field."""
        self.model_search_var.set("")

    def _select_model_from_list(self, model_name):
        """Handles model selection from the list."""
        self.app_state.set_selected_model(model_name)
        self.selected_model_label.configure(text=model_name)
        self._filter_models()  # Refresh the list to update selection highlighting

    def _handle_models_fetch_success(self, models_list):
        """Updated to work with the new model list UI"""
        self.available_models = models_list
        current_selection = self.app_state.get_selected_model()
        
        if not self.available_models:
            self.model_status_label.configure(
                text="No compatible models found or API error.", 
                text_color="red"
            )
        else:
            if current_selection not in self.available_models:
                current_selection = self.available_models[0]
                self.app_state.set_selected_model(current_selection)
            
            self.selected_model_label.configure(text=current_selection)
            self._filter_models()  # Populate the model list
            self.model_status_label.configure(
                text=f"Found {len(self.available_models)} models.", 
                text_color="green"
            )

    def _on_provider_change(self, provider):
        if self.app_state.set_api_provider(provider):
            self._update_free_models_visibility(provider)
            self.fetch_models(self.model_status_label.winfo_toplevel())

    def _update_free_models_visibility(self, provider):
        if provider == "openrouter":
            self.free_models_frame.grid()
        else:
            self.free_models_frame.grid_remove()

    def _on_free_models_toggle(self):
        self.app_state.set_show_free_models_only(self.free_models_var.get())
        self.fetch_models(self.model_status_label.winfo_toplevel())

    def fetch_models(self, parent_tab):
        """Fetches available AI models from the selected provider."""
        api_key = self.app_state.get_selected_api_key_value()
        if not api_key:
            self.model_status_label.configure(text="Error: API Key missing or invalid.", text_color="red")
            self._filter_models()  # Clear the model list
            return

        self.model_status_label.configure(text="Fetching models...", text_color="orange")
        self.available_models = []  # Clear current models
        self._filter_models()  # Update UI to show empty state

        try:
            if parent_tab.winfo_exists():
                parent_tab.winfo_toplevel().update_idletasks()
        except tk.TclError: 
            pass

        fetch_thread = threading.Thread(target=self._fetch_models_thread, args=(api_key,))
        fetch_thread.start()
    def _fetch_models_thread(self, api_key):
        try:
            provider = self.app_state.get_api_provider()
            
            if provider == "google":
                # Google provider code remains unchanged
                genai.configure(api_key=api_key)
                listed_models = genai.list_models()
                models_list = sorted([m.name for m in listed_models if 'generateContent' in m.supported_generation_methods])
            else:
                print("Fetching models from OpenRouter...")
                response = requests.get(
                    f"{OPENROUTER_BASE_URL}/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                response.raise_for_status()
                
                print(f"OpenRouter response status: {response.status_code}")
                
                models_data = response.json().get('data', [])  # Get the 'data' array from response
                models_list = []
                show_free_only = self.app_state.get_show_free_models_only()
                
                for model in models_data:
                    model_id = model.get('id')
                    if model_id:
                        if show_free_only:
                            pricing = model.get('pricing', {})
                            # Check if all pricing values are '0'
                            if all(value == '0' for value in pricing.values()):
                                models_list.append(model_id)
                        else:
                            models_list.append(model_id)
                
                models_list.sort()
                print(f"Parsed {len(models_list)} models")

            self.after(0, self._handle_models_fetch_success, models_list)

        except Exception as e:
            print(f"Error in _fetch_models_thread: {type(e).__name__} - {str(e)}")
            self.after(0, self._handle_models_fetch_error, e)

    def _handle_models_fetch_success(self, models_list):
        """Handles successful model fetch by updating the UI with the new models list."""
        self.available_models = models_list
        current_selection = self.app_state.get_selected_model()
        
        if not self.available_models:
            self.model_status_label.configure(
                text="No compatible models found or API error.", 
                text_color="red"
            )
        else:
            if current_selection not in self.available_models:
                current_selection = self.available_models[0]
                self.app_state.set_selected_model(current_selection)
            
            self.selected_model_label.configure(text=current_selection)
            self._filter_models()  # Update the model list UI
            self.model_status_label.configure(
                text=f"Found {len(self.available_models)} models.", 
                text_color="green"
            )

    def _handle_models_fetch_error(self, error):
        """Handles errors that occur during model fetching."""
        error_type = type(error).__name__
        msg = f"Error fetching models: {error_type} - {error}"
        print(msg)
        self.available_models = []
        
        try:
            if self.model_status_label.winfo_exists():
                self.model_status_label.configure(text=msg, text_color="red")
                self._filter_models()  # Clear and update the model list
        except tk.TclError: 
            pass

    def on_select_model(self, selected_model_name):
        print(f"Selected model: {selected_model_name}")
        if selected_model_name not in ["No models found", "API Key Required", "Permission Denied", "Error Fetching Models"]:
             self.app_state.set_selected_model(selected_model_name)
        else:
             current_saved_model = self.app_state.get_selected_model()
             if current_saved_model in self.available_models:
                  self.model_selector_var.set(current_saved_model)
             else:
                  if self.available_models:
                       fallback_model = self.available_models[0]
                       self.app_state.set_selected_model(fallback_model)
                       self.model_selector_var.set(fallback_model)
                  else:
                       pass

    def manage_functions_dialog(self):
        if not self.current_folder:
             messagebox.showwarning("Manage Functions", "Please select a folder first.", parent=self)
             return
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Manage Functions for '{self.current_folder}'")
        dialog.geometry("700x550")
        dialog.transient(self)
        dialog.grab_set()
        dialog.attributes("-topmost", True)
        current_functions = self.app_state.get_functions(self.current_folder).copy()
        dialog.grid_columnconfigure(0, weight=1, minsize=200)
        dialog.grid_columnconfigure(1, weight=3)
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=0)
        list_frame = ctk.CTkFrame(dialog, width=200)
        list_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        list_frame.grid_rowconfigure(1, weight=1)
        list_label = ctk.CTkLabel(list_frame, text="Functions:", font=ctk.CTkFont(weight="bold"))
        list_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        self.func_list_frame = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.func_list_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.func_list_frame.grid_columnconfigure(0, weight=1)
        self.selected_func_button = None
        edit_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        edit_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")
        edit_frame.grid_rowconfigure(2, weight=1)
        edit_frame.grid_columnconfigure(1, weight=1)
        name_label = ctk.CTkLabel(edit_frame, text="Function Name:")
        name_label.grid(row=0, column=0, padx=5, pady=(10,5), sticky="w")
        self.func_name_entry = ctk.CTkEntry(edit_frame)
        self.func_name_entry.grid(row=0, column=1, padx=5, pady=(10,5), sticky="ew")
        prompt_label = ctk.CTkLabel(edit_frame, text="System Prompt (Instructions for the AI):")
        prompt_label.grid(row=1, column=0, columnspan=2, padx=5, pady=(5,0), sticky="w")
        self.func_prompt_text = ctk.CTkTextbox(edit_frame, wrap="word")
        self.func_prompt_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        button_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="sew")
        button_frame.grid_columnconfigure((0,1,2), weight=1)
        new_button = ctk.CTkButton(button_frame, text="Clear / New", command=lambda: self._clear_func_edit_fields(current_functions), width=100)
        new_button.grid(row=0, column=0, padx=5, pady=5)
        save_button = ctk.CTkButton(button_frame, text="Save / Update", command=lambda: self._save_edited_function(current_functions), width=120)
        save_button.grid(row=0, column=1, padx=5, pady=5)
        delete_button = ctk.CTkButton(button_frame, text="Delete Selected", image=self.icon_delete, compound="left", fg_color="#D32F2F", hover_color="#C62828", command=lambda: self._delete_edited_function(current_functions), width=140)
        delete_button.grid(row=0, column=2, padx=5, pady=5)
        self._populate_func_listbox(current_functions)
        close_button = ctk.CTkButton(dialog, text="Close", command=dialog.destroy, width=100)
        close_button.grid(row=1, column=0, columnspan=2, pady=(0,10))
        dialog.wait_window()
        self.update_function_bar()

    def _populate_func_listbox(self, functions_dict):
        for widget in self.func_list_frame.winfo_children():
            widget.destroy()
        self.selected_func_button = None
        default_fg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        selected_fg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"])
        hover_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["hover_color"])
        func_names = sorted(functions_dict.keys())
        if not func_names:
            no_func_label = ctk.CTkLabel(self.func_list_frame, text="No functions yet.", text_color="gray")
            no_func_label.pack(pady=10)
        for name in func_names:
             btn = ctk.CTkButton(
                 self.func_list_frame, text=name, command=None, anchor="w",
                 fg_color=default_fg, hover_color=hover_color, width=180
             )
             btn.configure(command=lambda n=name, b=btn: self._on_func_select(n, functions_dict, b))
             btn.pack(fill=tk.X, padx=5, pady=2)
        self._clear_func_edit_fields(functions_dict, clear_list_selection=False)

    def _on_func_select(self, selected_name, functions_dict, button_widget):
         default_fg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
         selected_fg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"])
         if self.selected_func_button and self.selected_func_button != button_widget:
             try:
                 if self.selected_func_button.winfo_exists():
                     self.selected_func_button.configure(fg_color=default_fg)
             except tk.TclError: pass
         if button_widget.winfo_exists():
             button_widget.configure(fg_color=selected_fg)
             self.func_name_entry.delete(0, tk.END)
             self.func_name_entry.insert(0, selected_name)
             self.func_prompt_text.delete("1.0", tk.END)
             self.func_prompt_text.insert("1.0", functions_dict.get(selected_name, ""))

    def _clear_func_edit_fields(self, functions_dict, clear_list_selection=True):
        if clear_list_selection and self.selected_func_button:
            default_fg = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            try:
                if self.selected_func_button.winfo_exists():
                    self.selected_func_button.configure(fg_color=default_fg)
            except tk.TclError: pass
            self.selected_func_button = None
        try:
            if self.func_name_entry.winfo_exists(): self.func_name_entry.delete(0, tk.END)
            if self.func_prompt_text.winfo_exists(): self.func_prompt_text.delete("1.0", tk.END)
        except tk.TclError: pass

    def _save_edited_function(self, functions_dict):
        name = self.func_name_entry.get().strip()
        prompt = self.func_prompt_text.get("1.0", tk.END).strip()
        parent_dialog = self.func_name_entry.winfo_toplevel()
        if not name: messagebox.showwarning("Save Function", "Function name cannot be empty.", parent=parent_dialog); return
        if not prompt: messagebox.showwarning("Save Function", "System prompt cannot be empty.", parent=parent_dialog); return
        original_name = None
        if self.selected_func_button:
             original_name = self.selected_func_button.cget("text")
        if name != original_name and name in functions_dict:
            messagebox.showwarning("Name Conflict", f"A function named '{name}' already exists.", parent=parent_dialog); return
        if original_name and original_name != name:
             if not self.app_state.delete_function(self.current_folder, original_name):
                   messagebox.showerror("Save Error", f"Could not remove old function '{original_name}'.", parent=parent_dialog); return
        if self.app_state.add_or_update_function(self.current_folder, name, prompt):
             functions_dict[name] = prompt
             if original_name and original_name != name: del functions_dict[original_name]
             self._populate_func_listbox(functions_dict)
             for widget in self.func_list_frame.winfo_children():
                 if isinstance(widget, ctk.CTkButton) and widget.cget("text") == name:
                      self._on_func_select(name, functions_dict, widget); break
        else:
            messagebox.showerror("Save Error", f"Failed to save function '{name}'.", parent=parent_dialog)

    def _delete_edited_function(self, functions_dict):
        parent_dialog = self.func_name_entry.winfo_toplevel()
        if not self.selected_func_button: messagebox.showwarning("Delete Function", "Select a function to delete.", parent=parent_dialog); return
        selected_name = self.selected_func_button.cget("text")
        if messagebox.askyesno("Delete Function", f"Delete function '{selected_name}'?", icon='warning', parent=parent_dialog):
            if self.app_state.delete_function(self.current_folder, selected_name):
                del functions_dict[selected_name]
                self._populate_func_listbox(functions_dict)

    def configure_genai(self):
        api_key = self.app_state.get_selected_api_key_value()
        if not api_key:
            print("GenAI configuration skipped: No API key selected or value is empty.")
            return False
        try:
            genai.configure(api_key=api_key)
            return True
        except Exception as e:
             print(f"Error configuring GenAI: {e}")
             return False

    def run_ai_function(self, func_name):
        if not self.current_folder or not self.current_page:
            messagebox.showwarning("Run Function", "Please select a page first.", parent=self)
            return
        if self.ai_is_running:
             messagebox.showwarning("Busy", "AI is currently processing. Please wait.", parent=self)
             return
        if not self.configure_genai():
            messagebox.showerror("API Key Error", "Google AI API Key is not configured or invalid. Check Settings.", parent=self)
            return

        functions = self.app_state.get_functions(self.current_folder)
        system_prompt = functions.get(func_name)
        if not system_prompt:
             messagebox.showerror("Function Error", f"Could not find prompt for function '{func_name}'.", parent=self)
             return

        run_on_selection = False
        user_content = ""
        try:
            if self.workspace.tag_ranges(tk.SEL):
                user_content = self.workspace.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
                if user_content:
                    run_on_selection = True
                    print(f"Running AI on selection ({len(user_content)} chars)")
                else:
                    user_content = self.workspace.get("1.0", tk.END).strip()
            else:
                user_content = self.workspace.get("1.0", tk.END).strip()

        except tk.TclError as e:
             messagebox.showerror("Content Error", f"Could not get text from workspace: {e}", parent=self)
             return

        if not user_content:
            messagebox.showinfo("Run Function", "Workspace/Selection is empty. Nothing to process.", parent=self)
            return

        model_name = self.app_state.get_selected_model()
        if not model_name or model_name in ["No models found", "API Key Required", "Permission Denied", "Error Fetching Models"]:
             messagebox.showerror("Model Error", f"Invalid AI model ('{model_name}'). Select a valid model in Settings.", parent=self)
             return

        self.ai_is_running = True
        self.update_function_bar()
        status_suffix = " (selection)" if run_on_selection else ""
        self.status_bar.configure(text=f"⏳ Running '{func_name}'{status_suffix}...")
        self.workspace.configure(state="disabled")
        self.toggle_format_toolbar(False)
        self.update_idletasks()

        thread = threading.Thread(target=self._ai_call_thread, args=(model_name, system_prompt, user_content, func_name, run_on_selection))
        thread.start()

    def _ai_call_thread(self, model_name, system_prompt, user_content, func_name, run_on_selection):
        try:
            references = self.app_state.get_references()
            reference_content = ""
            if references:
                reference_content = "--- Reference Content (For Context) ---\n"
                for ref_key, ref_data in references.items():
                    ref_text = self._get_plain_text_content(ref_data['folder'], ref_data['page'])
                    reference_content += f"\n[{ref_data['page']}]:\n{ref_text}\n"
                reference_content += "\n--- End References ---\n\n"

            combined_content = f"{reference_content}{user_content}"
            provider = self.app_state.get_api_provider()
            api_key = self.app_state.get_selected_api_key_value()

            if provider == "google":
                is_gemma = "gemma" in model_name.lower()
                if is_gemma:
                    model = genai.GenerativeModel(model_name=model_name)
                    prompt_content = f"{"No formatting"+system_prompt}\n\n{combined_content}"
                    response = model.generate_content(prompt_content)
                else:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction="No formatting"+system_prompt
                    )
                    response = model.generate_content(combined_content)

            else:
                response = requests.post(
                    url=f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "localhost",
                        "X-Title": APP_NAME
                    },
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "system",
                                "content": "No formatting" + system_prompt
                            },
                            {
                                "role": "user",
                                "content": combined_content
                            }
                        ]
                    }
                )
                response.raise_for_status()
                response = response.json()

            self.after(0, self._handle_ai_response, response, func_name, run_on_selection, provider)

        except Exception as e:
            self.after(0, self._handle_ai_error, e, func_name)
        finally:
            self.after(0, self._ai_call_finished)

    def _handle_ai_response(self, response, func_name, run_on_selection, provider):
        try:
            ai_text = ""
            
            if provider == "google":
                if hasattr(response.candidates[0], 'content') and hasattr(response.candidates[0].content, 'parts'):
                    ai_text = "".join([part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')])
            else:
                choices = response.get('choices', [])
                if choices:
                    ai_text = choices[0].get('message', {}).get('content', '').strip()
                else:
                    raise ValueError("No response choices from OpenRouter")

            if not ai_text.strip():
                raise ValueError("Empty response from AI")

            self.workspace.configure(state="normal")

            if run_on_selection:
                try:
                    sel_start = self.workspace.index(tk.SEL_FIRST)
                    sel_end = self.workspace.index(tk.SEL_LAST)
                    self.workspace.delete(sel_start, sel_end)
                    self.workspace.insert(sel_start, ai_text)
                    self.status_bar.configure(text=f"✅ '{func_name}' replaced selection.")
                except tk.TclError:
                    run_on_selection = False
                    print("Warning: Selection lost before AI replace, appending instead.")
                    self.status_bar.configure(text=f"'{func_name}' completed (selection lost).")

            if not run_on_selection:
                separator_tag = "ai_separator"
                current_content = self.workspace.get("1.0", "end-1c").strip()
                prefix = "\n\n" if current_content else ""
                separator = f"{prefix}--- AI Result ({func_name}) ---"
                self.workspace.insert(tk.END, separator, (separator_tag,))
                self.workspace.insert(tk.END, f"\n{ai_text}")
                self.status_bar.configure(text=f"✅ '{func_name}' appended result.")

            self.workspace.see(tk.END)
            self.workspace.edit_modified(True)
            self.save_current_page_content()

        except Exception as e:
            print(f"Error processing AI response: {e}")
            response_details = ""
            try:
                 response_details = f"\nResponse: {response}"
                 if hasattr(response, 'prompt_feedback'): response_details += f"\nPrompt Feedback: {response.prompt_feedback}"
                 if hasattr(response, 'candidates'): response_details += f"\nCandidates: {response.candidates}"
            except Exception: pass
            messagebox.showerror("AI Response Error", f"Error processing AI response: {e}" + response_details, parent=self)
            self.status_bar.configure(text=f"'{func_name}' failed (processing error).")

    def _handle_ai_error(self, error, func_name):
        error_type = type(error).__name__
        msg = f"Error running '{func_name}':\n\n[{error_type}]\n{error}"
        title = "AI Execution Error"
        error_str = str(error)
        if "Permission denied" in error_str: msg = f"AI Error: Permission Denied.\nCheck API key validity/permissions.\nDetails: {error_str}"; title = "API Permission Error"
        elif "Invalid Argument" in error_str or "model" in error_str.lower() or "prompt" in error_str.lower(): msg = f"AI Error: Invalid Argument.\nCheck model/prompt/content.\nDetails: {error_str}"; title = "AI Argument Error"
        elif "ResourceExhausted" in error_str or "quota" in error_str.lower(): msg = f"AI Error: Quota Exceeded.\nDetails: {error_str}"; title = "API Quota Error"
        elif "network" in error_str.lower() or "connection" in error_str.lower() or "ssl" in error_str.lower(): msg = f"AI Error: Network/Connection Issue.\nCheck internet/firewall.\nDetails: {error_str}"; title = "Network Error"
        messagebox.showerror(title, msg, parent=self)
        self.status_bar.configure(text=f"❌ '{func_name}' failed ({error_type}).")

    def _ai_call_finished(self):
        self.ai_is_running = False
        try:
            if self.workspace.winfo_exists():
                self.workspace.configure(state="normal")
        except tk.TclError: pass
        self.toggle_format_toolbar(self.current_page is not None)
        self.update_function_bar()

    def _apply_appearance_mode(self, ctk_color_tuple):
         if not isinstance(ctk_color_tuple, (tuple, list)) or len(ctk_color_tuple) != 2:
              return ctk_color_tuple
         return ctk_color_tuple[0] if ctk.get_appearance_mode() == "Light" else ctk_color_tuple[1]

    def save_project_as(self):
        """Saves the entire project data to a new file."""
        if self.current_page:
            if not self.save_current_page_content():
                messagebox.showerror("Save Error", "Could not save current page changes. 'Save As' aborted.", parent=self)
                return
        self.app_state.save_data()

        initial_dir = os.path.dirname(self.app_state.filename)
        initial_file = os.path.basename(self.app_state.filename)
        chosen_path = filedialog.asksaveasfilename(
            title="Save Project As",
            initialdir=initial_dir if os.path.isdir(initial_dir) else os.path.expanduser("~"),
            initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("AI Assistant Project", "*.json"), ("All Files", "*.*")]
        )

        if chosen_path:
            try:
                shutil.copy2(self.app_state.filename, chosen_path)
                self.app_state.filename = chosen_path
                self.update_title()
                messagebox.showinfo("Save Project As", f"Project successfully saved to:\n{chosen_path}", parent=self)
            except Exception as e:
                messagebox.showerror("Save Project As Error", f"Could not copy project file:\n{e}", parent=self)

    def load_project(self):
        """Loads a project from a chosen file."""
        if self.current_page and self.workspace.edit_modified():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Do you want to save changes to the current project\n'{os.path.basename(self.app_state.filename)}'?",
                parent=self
            )
            if response is True:
                if not self.save_current_page_content():
                    messagebox.showerror("Save Error", "Could not save current changes.", parent=self)
                    return
                self.app_state.save_data()
            elif response is None:
                return

        chosen_path = filedialog.askopenfilename(
            title="Load Project",
            initialdir=os.path.dirname(os.path.abspath(self.app_state.filename)),
            filetypes=[("AI Assistant Project", "*.json"), ("All Files", "*.*")]
        )

        if chosen_path:
            print(f"Loading project from: {chosen_path}")
            
            new_app_state = AppState(chosen_path)
            if new_app_state.load_data():
                self.app_state = new_app_state
                
                self.current_folder = None
                self.current_page = None
                self.folder_expanded_state.clear()
                self.search_results.clear()
                
                self.workspace.configure(state="normal")
                self.workspace.delete("1.0", tk.END)
                self.workspace.configure(state="disabled")
                
                self.update_sidebar()
                self.update_function_bar()
                self.update_title()
                
                folders = self.app_state.get_folders()
                if folders:
                    first_folder = sorted(folders)[0]
                    self.select_folder(first_folder)
                
                messagebox.showinfo("Load Project", 
                                f"Project loaded from:\n{chosen_path}", parent=self)
            else:
                messagebox.showerror("Load Error", 
                                f"Failed to load project from:\n{chosen_path}", parent=self)

    def _refresh_ui_after_load(self):
        """Resets and repopulates the UI after loading a new project file."""
        print("Refreshing UI after project load...")
        
        self.current_folder = None
        self.current_page = None
        self.folder_expanded_state.clear()
        self.search_results.clear()
        self._last_saved_content_dump = None
        
        self.workspace.configure(state="normal")
        self.workspace.delete("1.0", tk.END)
        self.workspace.configure(state="disabled")
        self.toggle_format_toolbar(False)
        
        self.search_entry.delete(0, tk.END)
        
        self.update_sidebar()
        self.update_function_bar()
        
        folders = self.app_state.get_folders()
        if folders:
            first_folder = sorted(folders)[0]
            self.select_folder(first_folder)
            
        print("UI refresh complete")

    def on_closing(self):
        """Handles application close, prompting for unsaved changes."""
        print("Closing application...")

        unsaved_changes = False
        if self.current_page and self.workspace.edit_modified():
            unsaved_changes = True

        if unsaved_changes:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Do you want to save changes to\n'{os.path.basename(self.app_state.filename)}'\nbefore quitting?",
                parent=self
            )
            if response is True:
                if not self.save_current_page_content():
                    messagebox.showwarning("Save Error", "Could not save current changes, but closing anyway.", parent=self)
                else:
                    self.app_state.save_data()
            elif response is None:
                print("Closing cancelled by user.")
                return

        print("Saving final app state...")
        self.app_state.save_data()

        print("Destroying main window.")
        self.destroy()


if __name__ == "__main__":
    if not os.path.exists(ICONS_FOLDER):
        try:
            os.makedirs(ICONS_FOLDER)
            print(f"Created '{ICONS_FOLDER}' directory. Place icons inside.")
        except OSError as e:
            print(f"Warning: Could not create icons folder '{ICONS_FOLDER}': {e}")

    if not os.path.exists(BACKUP_FOLDER):
        try:
            os.makedirs(BACKUP_FOLDER)
            print(f"Created '{BACKUP_FOLDER}' directory.")
        except OSError as e:
            print(f"Warning: Could not create backup folder '{BACKUP_FOLDER}': {e}")

    print("Initializing application state...")
    app_state = AppState()

    print("Creating backup...")
    app_state.create_backup()

    print("Creating application window...")
    app = App(app_state)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    print("Starting main loop.")
    app.mainloop()