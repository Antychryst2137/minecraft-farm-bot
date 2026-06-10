import pyautogui
import time
import keyboard
import mss
import cv2
import numpy as np
import threading
from PIL import Image
import tkinter as tk
from tkinter import ttk
import queue
import json
import os

class MinecraftFarmBot:
    def __init__(self, log_queue, config):
        self.running = False
        self.floor_count = 0
        self.config = config
        self.mining = False
        self.in_chat = False
        self.log_queue = log_queue
        self.items_clicked = 0
        self.links_clicked = 0
        self.warps_done = 0
        self.sells_done = 0
        self.antiafk_clicked = 0
        
    def log(self, message):
        """Wyślij log do GUI"""
        self.log_queue.put(message)
        print(message)
        
    def start_bot(self):
        """Uruchom bota"""
        self.running = True
        self.log("✓ Bot WŁĄCZONY - pracuje w tle!")
        self.log(f"  Klawisz kopania: {self.config['mining_key']}")
        self.log(f"  Piętro do warpa: {self.config['warp_interval']}")
        self.log(f"  Przycisk warpa: {self.config['warp_key']}")
        self.log(f"  Wyłączenie: {self.config['toggle_key']}")
        threading.Thread(target=self.farm_loop, daemon=True).start()
        threading.Thread(target=self.monitor_chest, daemon=True).start()
        if self.config.get('enable_chat_monitor', False):
            threading.Thread(target=self.monitor_chat, daemon=True).start()
        
    def stop_bot(self):
        """Zatrzymaj bota"""
        self.running = False
        if self.mining:
            keyboard.release(self.config['mining_key'])
            self.mining = False
        self.log("✗ Bot WYŁĄCZONY")
        
    def farm_loop(self):
        """Główna pętla - ciągłe kopanie i poruszanie"""
        sell_counter = 0
        while self.running:
            if not self.in_chat:
                # Kopanie - trzymanie przycisku
                if not self.mining:
                    keyboard.press(self.config['mining_key'])
                    self.mining = True
                
                # Poruszanie się
                keyboard.press(self.config['right_key'])
                time.sleep(self.config['walk_duration'])
                keyboard.release(self.config['right_key'])
                time.sleep(0.1)
                
                # Liczenie pięter
                self.floor_count += 1
                sell_counter += 1
                
                # Sell co X pięter
                if self.config['sell_interval'] > 0 and sell_counter >= self.config['sell_interval']:
                    if self.mining:
                        keyboard.release(self.config['mining_key'])
                        self.mining = False
                    self.sell_items()
                    sell_counter = 0
                    if self.running:
                        keyboard.press(self.config['mining_key'])
                        self.mining = True
                
                self.log(f"[FARMA] Piętro: {self.floor_count}/{self.config['warp_interval']}")
                
                # Warp co X pięter
                if self.floor_count >= self.config['warp_interval']:
                    if self.mining:
                        keyboard.release(self.config['mining_key'])
                        self.mining = False
                    self.log(f"[WARP] Po {self.floor_count} piętrach - teleportacja!")
                    self.teleport_warp()
                    self.floor_count = 0
                    self.warps_done += 1
                    time.sleep(3)
                    if self.running:
                        keyboard.press(self.config['mining_key'])
                        self.mining = True
                
                # Poruszanie się lewo
                keyboard.press(self.config['left_key'])
                time.sleep(self.config['walk_duration'])
                keyboard.release(self.config['left_key'])
                time.sleep(0.1)
            else:
                if self.mining:
                    keyboard.release(self.config['mining_key'])
                    self.mining = False
                time.sleep(0.1)
    
    def teleport_warp(self):
        """Teleportuj się na warp"""
        keyboard.press(self.config['warp_key'])
        time.sleep(0.5)
        keyboard.release(self.config['warp_key'])
        self.log(f"[WARP] Klawisz '{self.config['warp_key']}' wciśnięty!")
    
    def sell_items(self):
        """Sprzedaj przedmioty"""
        self.log(f"[SELL] Wciskam klawisz '{self.config['sell_key']}'!")
        keyboard.press(self.config['sell_key'])
        time.sleep(0.3)
        keyboard.release(self.config['sell_key'])
        self.sells_done += 1
        self.log(f"[SELL] ✓ Sprzedano! (razem: {self.sells_done})")
    
    def get_screen(self):
        """Przechwytaj ekran"""
        try:
            with mss.mss() as sct:
                screenshot = sct.grab(sct.monitors[1])
                return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except:
            return None
    
    def monitor_chest(self):
        """Monitoruj otwarcie skrzyni i szukaj antiAFK w górnej części"""
        while self.running:
            try:
                screen = self.get_screen()
                if screen is None:
                    time.sleep(0.5)
                    continue
                
                # Szukaj górnej części EQ (gdzie jest skrzynia)
                # Zwykle GUI Minecrafta jest w środku ekranu
                screen_height = screen.shape[0]
                screen_width = screen.shape[1]
                
                # Górna część - gdzie będzie chest (około 1/3 ekranu od góry)
                chest_region = screen[int(screen_height*0.15):int(screen_height*0.55), :]
                
                # Szukaj pogrubionego tekstu (antiAFK)
                antiafk_pos = self.find_bold_item(chest_region)
                
                if antiafk_pos:
                    self.log("[ANTIAFK] ✓ Znaleziono antiAFK!")
                    
                    # Przerywamy kopanie na moment
                    if self.mining:
                        keyboard.release(self.config['mining_key'])
                        self.mining = False
                    
                    time.sleep(0.2)
                    
                    x, y = antiafk_pos
                    # Kompensacja offset'u z powodu ucinięcia regionu
                    y_adjusted = y + int(screen_height*0.15)
                    
                    pyautogui.click(x, y_adjusted)
                    self.log("[ANTIAFK] ✓ Kliknięto!")
                    self.antiafk_clicked += 1
                    time.sleep(0.8)
                    
                    # Wznów kopanie
                    if self.running:
                        keyboard.press(self.config['mining_key'])
                        self.mining = True
                
                time.sleep(0.2)
            except Exception as e:
                self.log(f"[ERROR] monitor_chest: {e}")
                time.sleep(0.5)
    
    def find_bold_item(self, region):
        """Szukaj pogrubionego tekstu w regionie"""
        try:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            
            # Proguowanie dla jasnych pikseli (pogrubiony tekst)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            
            # Dylatacja dla połączenia pikseli
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            thresh = cv2.dilate(thresh, kernel, iterations=1)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            # Szukaj największego konturu (to będzie pogrubiony tekst)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                
                # Filtruj po rozmiarze - pogrubiony tekst powinien być widoczny
                if h > 8 and w > 20 and h < 40 and w < 150:
                    center_x = x + w // 2
                    center_y = y + h // 2
                    return (center_x, center_y)
            
            return None
        except Exception as e:
            return None
    
    def monitor_chat(self):
        """Monitoruj czat i szukaj linku"""
        while self.running:
            try:
                screen = self.get_screen()
                if screen is None:
                    time.sleep(0.5)
                    continue
                
                if screen.shape[0] > 520:
                    chat_region = screen[520:, 0:320]
                else:
                    chat_region = screen[int(screen.shape[0]*0.7):, 0:320]
                
                link_info = self.find_clickable_link(chat_region, screen.shape)
                
                if link_info:
                    self.log("[CHAT] ✓ Znaleziono link!")
                    
                    if self.mining:
                        keyboard.release(self.config['mining_key'])
                        self.mining = False
                    
                    time.sleep(0.5)
                    
                    self.in_chat = True
                    keyboard.press('t')
                    time.sleep(0.4)
                    
                    link_x, link_y = link_info
                    pyautogui.click(link_x, link_y)
                    self.log("[CHAT] ✓ Kliknięto link!")
                    self.links_clicked += 1
                    time.sleep(0.8)
                    
                    keyboard.press('enter')
                    self.log("[CHAT] ✓ Potwierdzono!")
                    time.sleep(1)
                    
                    self.in_chat = False
                    
                    if self.running:
                        keyboard.press(self.config['mining_key'])
                        self.mining = True
                    
                    time.sleep(2)
                
                time.sleep(0.3)
            except Exception as e:
                self.log(f"[ERROR] monitor_chat: {e}")
                time.sleep(0.5)
    
    def find_clickable_link(self, chat_region, screen_shape):
        """Szukaj linku w chacie"""
        try:
            hsv = cv2.cvtColor(chat_region, cv2.COLOR_BGR2HSV)
            
            lower = np.array([80, 80, 100])
            upper = np.array([100, 255, 255])
            
            mask = cv2.inRange(hsv, lower, upper)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            mask = cv2.dilate(mask, kernel, iterations=1)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                
                offset_y = screen_shape[0] - chat_region.shape[0]
                
                center_x = x + w // 2
                center_y = offset_y + y + h // 2
                
                return (center_x, center_y)
            
            return None
        except Exception as e:
            return None


class BotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Minecraft Farm Bot v3.0 - AntiAFK & Mining")
        self.root.geometry("800x950")
        self.root.resizable(False, False)
        
        self.log_queue = queue.Queue()
        self.bot = None
        self.config = self.load_config()
        
        self.setup_ui()
        self.update_logs()
        self.update_stats()
        
        # Hotkeye
        self.root.bind('<F6>', lambda e: self.start_bot())
        self.root.bind('<F7>', lambda e: self.stop_bot())
        
    def load_config(self):
        """Załaduj konfigurację z pliku"""
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
        
        # Domyślna konfiguracja
        return {
            'mining_key': 'z',
            'left_key': 'a',
            'right_key': 'd',
            'walk_duration': 0.5,
            'warp_key': '/',
            'warp_interval': 10,
            'sell_key': "'",
            'sell_interval': 0,
            'toggle_key': ']',
            'enable_chat_monitor': False
        }
    
    def save_config(self):
        """Zapisz konfigurację do pliku"""
        try:
            self.config = {
                'mining_key': self.mining_key_entry.get().lower() or 'z',
                'left_key': self.left_key_entry.get().lower() or 'a',
                'right_key': self.right_key_entry.get().lower() or 'd',
                'walk_duration': float(self.walk_duration_entry.get() or 0.5),
                'warp_key': self.warp_key_entry.get() or '/',
                'warp_interval': int(self.warp_interval_entry.get() or 10),
                'sell_key': self.sell_key_entry.get() or "'",
                'sell_interval': int(self.sell_interval_entry.get() or 0),
                'toggle_key': self.toggle_key_entry.get() or ']',
                'enable_chat_monitor': self.chat_monitor_var.get()
            }
            
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            
            self.log("✓ Konfiguracja zapisana!")
        except ValueError:
            self.log("❌ Błąd! Sprawdź czy wszystkie wartości są poprawne")
    
    def setup_ui(self):
        """Stwórz interfejs"""
        
        # Notebook (zakładki)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === ZAKŁADKA 1: KONFIGURACJA ===
        config_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(config_frame, text="⚙️ Konfiguracja")
        
        # Przyciski
        ttk.Label(config_frame, text="PRZYCISKI", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Przycisk kopania
        ttk.Label(config_frame, text="Przycisk KOPANIA (Z):").pack(anchor=tk.W)
        self.mining_key_entry = ttk.Entry(config_frame, width=15)
        self.mining_key_entry.insert(0, self.config['mining_key'])
        self.mining_key_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Przycisk lewy
        ttk.Label(config_frame, text="Przycisk LEWO (A):").pack(anchor=tk.W)
        self.left_key_entry = ttk.Entry(config_frame, width=15)
        self.left_key_entry.insert(0, self.config['left_key'])
        self.left_key_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Przycisk prawy
        ttk.Label(config_frame, text="Przycisk PRAWO (D):").pack(anchor=tk.W)
        self.right_key_entry = ttk.Entry(config_frame, width=15)
        self.right_key_entry.insert(0, self.config['right_key'])
        self.right_key_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Przycisk warpa
        ttk.Label(config_frame, text="Przycisk WARP (/):").pack(anchor=tk.W)
        self.warp_key_entry = ttk.Entry(config_frame, width=15)
        self.warp_key_entry.insert(0, self.config['warp_key'])
        self.warp_key_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Przycisk sella
        ttk.Label(config_frame, text="Przycisk SELL ('):").pack(anchor=tk.W)
        self.sell_key_entry = ttk.Entry(config_frame, width=15)
        self.sell_key_entry.insert(0, self.config['sell_key'])
        self.sell_key_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Przycisk toggle
        ttk.Label(config_frame, text="Przycisk WYŁĄCZENIA (]):").pack(anchor=tk.W)
        self.toggle_key_entry = ttk.Entry(config_frame, width=15)
        self.toggle_key_entry.insert(0, self.config['toggle_key'])
        self.toggle_key_entry.pack(anchor=tk.W, pady=(0, 20))
        
        # Czasy i wartości
        ttk.Separator(config_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Label(config_frame, text="CZASY I WARTOŚCI", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10, 10))
        
        # Czas poruszania
        ttk.Label(config_frame, text="Czas poruszania w jedną stronę (sekundy):").pack(anchor=tk.W)
        self.walk_duration_entry = ttk.Entry(config_frame, width=15)
        self.walk_duration_entry.insert(0, str(self.config['walk_duration']))
        self.walk_duration_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Interwał warpa
        ttk.Label(config_frame, text="Co ile pięter WARP:").pack(anchor=tk.W)
        self.warp_interval_entry = ttk.Entry(config_frame, width=15)
        self.warp_interval_entry.insert(0, str(self.config['warp_interval']))
        self.warp_interval_entry.pack(anchor=tk.W, pady=(0, 10))
        
        # Interwał sella
        ttk.Label(config_frame, text="Co ile pięter SELL (0 = wyłączony):").pack(anchor=tk.W)
        self.sell_interval_entry = ttk.Entry(config_frame, width=15)
        self.sell_interval_entry.insert(0, str(self.config['sell_interval']))
        self.sell_interval_entry.pack(anchor=tk.W, pady=(0, 20))
        
        # Opcje
        ttk.Separator(config_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        ttk.Label(config_frame, text="OPCJE", font=("Arial", 11, "bold")).pack(anchor=tk.W, pady=(10, 10))
        
        self.chat_monitor_var = tk.BooleanVar(value=self.config.get('enable_chat_monitor', False))
        chat_check = ttk.Checkbutton(config_frame, text="Monitoruj czat (szukaj linków)", 
                                     variable=self.chat_monitor_var)
        chat_check.pack(anchor=tk.W, pady=(0, 20))
        
        # Przycisk zapisz
        save_btn = ttk.Button(config_frame, text="💾 Zapisz konfigurację", 
                             command=self.save_config)
        save_btn.pack(fill=tk.X, pady=10)
        
        # === ZAKŁADKA 2: KONTROLA ===
        control_frame = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(control_frame, text="🎮 Kontrola")
        
        # Info
        info_label = ttk.Label(control_frame, text="⚠️ Bot pracuje w tle - możesz grać bez przeszkód!", 
                              font=("Arial", 10, "bold"), foreground="green")
        info_label.pack(pady=10)
        
        info_label2 = ttk.Label(control_frame, text="Przycisk ] = Wyłącz/Włącz bota bez resetowania GUI", 
                               font=("Arial", 9))
        info_label2.pack(pady=5)
        
        # Status
        status_frame = ttk.LabelFrame(control_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="⭕ BOT WYŁĄCZONY", 
                                     font=("Arial", 12, "bold"))
        self.status_label.pack(pady=10)
        
        # Przyciski kontrolne
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(btn_frame, text="▶ START (F6)", 
                                   command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ STOP (F7)", 
                                  command=self.stop_bot, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Statystyka
        stats_frame = ttk.LabelFrame(control_frame, text="Statystyka", padding=10)
        stats_frame.pack(fill=tk.X)
        
        self.stats_text = ttk.Label(stats_frame, text="", font=("Courier", 9), justify=tk.LEFT)
        self.stats_text.pack(anchor=tk.W)
        
        # === ZAKŁADKA 3: LOGI ===
        logs_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(logs_frame, text="📋 Logi")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(logs_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        self.log_text = tk.Text(logs_frame, height=30, width=95,
                               bg='#000000', fg='#00ff00', font=("Courier", 8),
                               yscrollcommand=scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
    
    def log(self, message):
        """Dodaj log"""
        self.log_queue.put(message)
    
    def start_bot(self):
        """Włącz bota"""
        self.save_config()
        self.bot = MinecraftFarmBot(self.log_queue, self.config)
        self.bot.start_bot()
        self.status_label.config(text="🟢 BOT WŁĄCZONY - pracuje w tle!")
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # Nasłuch na toggle key
        threading.Thread(target=self.listen_toggle_key, daemon=True).start()
    
    def listen_toggle_key(self):
        """Słuchaj na klawisz toggle"""
        while self.bot and self.bot.running:
            try:
                if keyboard.is_pressed(self.config['toggle_key']):
                    time.sleep(0.5)  # Debounce
                    if self.bot:
                        self.bot.stop_bot()
                        self.status_label.config(text="⭕ BOT WYŁĄCZONY (via hotkey)")
                        self.start_btn.config(state='normal')
                        self.stop_btn.config(state='disabled')
                    break
            except:
                pass
            time.sleep(0.1)
    
    def stop_bot(self):
        """Wyłącz bota"""
        if self.bot:
            self.bot.stop_bot()
        self.status_label.config(text="⭕ BOT WYŁĄCZONY")
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
    
    def update_logs(self):
        """Aktualizuj logi z kolejki"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
        except:
            pass
        
        self.root.after(100, self.update_logs)
    
    def update_stats(self):
        """Aktualizuj statystykę"""
        if self.bot and self.bot.running:
            stats = f"Piętro: {self.bot.floor_count}/{self.config['warp_interval']}\n"
            stats += f"Warpy: {self.bot.warps_done}\n"
            stats += f"Sprzedaże: {self.bot.sells_done}\n"
            stats += f"AntiAFK: {self.bot.antiafk_clicked}\n"
            stats += f"Linki: {self.bot.links_clicked}"
        else:
            stats = "Bot wyłączony"
        
        self.stats_text.config(text=stats)
        self.root.after(500, self.update_stats)


def main():
    root = tk.Tk()
    gui = BotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
