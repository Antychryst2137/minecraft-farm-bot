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

class MinecraftFarmBot:
    def __init__(self, log_queue):
        self.running = False
        self.floor_count = 0
        self.warp_interval = 10
        self.eq_open = False
        self.in_chat = False
        self.log_queue = log_queue
        self.items_clicked = 0
        self.links_clicked = 0
        self.warps_done = 0
        
    def log(self, message):
        """Wyślij log do GUI"""
        self.log_queue.put(message)
        print(message)
        
    def start_bot(self):
        """Uruchom bota"""
        self.running = True
        self.log("✓ Bot WŁĄCZONY")
        threading.Thread(target=self.farm_loop, daemon=True).start()
        threading.Thread(target=self.monitor_inventory, daemon=True).start()
        threading.Thread(target=self.monitor_chat, daemon=True).start()
        
    def stop_bot(self):
        """Zatrzymaj bota"""
        self.running = False
        self.log("✗ Bot WYŁĄCZONY")
        
    def farm_loop(self):
        """Główna pętla - chodzenie A i D"""
        while self.running:
            if not self.eq_open and not self.in_chat:
                # Chodzenie prawo (D)
                keyboard.press('d')
                time.sleep(0.1)
                keyboard.release('d')
                time.sleep(0.4)
                
                # Liczenie pięter
                self.floor_count += 1
                self.log(f"[FARMA] Piętro: {self.floor_count}/{self.warp_interval}")
                
                # Warp co X pięter
                if self.floor_count >= self.warp_interval:
                    self.log(f"[WARP] Po {self.floor_count} piętrach - teleportacja!")
                    self.teleport_warp()
                    self.floor_count = 0
                    self.warps_done += 1
                    time.sleep(3)
                
                # Chodzenie lewo (A)
                keyboard.press('a')
                time.sleep(0.1)
                keyboard.release('a')
                time.sleep(0.4)
            else:
                time.sleep(0.1)
    
    def teleport_warp(self):
        """Teleportuj się na warp - klawisz /"""
        keyboard.press('/')
        time.sleep(0.5)
        keyboard.release('/')
        self.log("[WARP] Klawisz / wciśnięty!")
    
    def get_screen(self):
        """Przechwytaj ekran"""
        with mss.mss() as sct:
            screenshot = sct.grab(sct.monitors[1])
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def monitor_inventory(self):
        """Monitoruj otwarcie EQ i szukaj pogrubionego przedmiotu"""
        while self.running:
            try:
                screen = self.get_screen()
                enlarged_text_pos = self.find_enlarged_text(screen)
                
                if enlarged_text_pos:
                    self.eq_open = True
                    self.log("[EQ] ✓ Znaleziono pogrubiony przedmiot!")
                    time.sleep(0.3)
                    
                    x, y = enlarged_text_pos
                    pyautogui.click(x, y)
                    self.log("[EQ] ✓ Kliknięto!")
                    self.items_clicked += 1
                    time.sleep(0.8)
                    
                    self.eq_open = False
                
                time.sleep(0.15)
            except Exception as e:
                self.log(f"[ERROR] monitor_inventory: {e}")
                time.sleep(0.5)
    
    def find_enlarged_text(self, screen):
        """Szukaj pogrubionego tekstu"""
        try:
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            thresh = cv2.dilate(thresh, kernel, iterations=1)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if h > 14 and w > 25 and h < 50 and w < 200:
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
                
                if screen.shape[0] > 520:
                    chat_region = screen[520:, 0:320]
                else:
                    chat_region = screen[int(screen.shape[0]*0.7):, 0:320]
                
                link_info = self.find_clickable_link(chat_region, screen.shape)
                
                if link_info:
                    self.log("[CHAT] ✓ Znaleziono link!")
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
        self.root.title("🎮 Minecraft Farm Bot v1.0")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#1e1e1e')
        
        self.log_queue = queue.Queue()
        self.bot = MinecraftFarmBot(self.log_queue)
        
        self.setup_ui()
        self.update_logs()
        self.update_stats()
        
    def setup_ui(self):
        """Stwórz interfejs"""
        
        # Nagłówek
        header = tk.Frame(self.root, bg='#2d2d2d', height=60)
        header.pack(fill=tk.X, padx=0, pady=0)
        
        title = tk.Label(header, text="🎮 MINECRAFT FARM BOT", 
                        font=("Arial", 16, "bold"), bg='#2d2d2d', fg='#00ff00')
        title.pack(pady=10)
        
        # Panel kontrolny
        control_frame = tk.Frame(self.root, bg='#1e1e1e')
        control_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Przycisk START
        self.start_btn = tk.Button(control_frame, text="▶ START (F6)", 
                                   command=self.start_bot, 
                                   font=("Arial", 12, "bold"),
                                   bg='#00aa00', fg='white', width=15, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        # Przycisk STOP
        self.stop_btn = tk.Button(control_frame, text="⏹ STOP (F7)", 
                                  command=self.stop_bot,
                                  font=("Arial", 12, "bold"),
                                  bg='#aa0000', fg='white', width=15, height=2)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Status
        status_frame = tk.Frame(self.root, bg='#2d2d2d')
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold"), 
                bg='#2d2d2d', fg='#ffffff').pack(anchor=tk.W)
        
        self.status_label = tk.Label(status_frame, text="⭕ BOT WYŁĄCZONY", 
                                     font=("Arial", 11), bg='#2d2d2d', fg='#ff6666')
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # Statystyka
        stats_frame = tk.Frame(self.root, bg='#2d2d2d')
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(stats_frame, text="Statystyka:", font=("Arial", 10, "bold"),
                bg='#2d2d2d', fg='#ffffff').pack(anchor=tk.W)
        
        self.stats_text = tk.Label(stats_frame, text="", font=("Arial", 10),
                                   bg='#2d2d2d', fg='#00ff00', justify=tk.LEFT)
        self.stats_text.pack(anchor=tk.W, pady=5)
        
        # Logi
        log_frame = tk.Frame(self.root, bg='#1e1e1e')
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(log_frame, text="Logi:", font=("Arial", 10, "bold"),
                bg='#1e1e1e', fg='#ffffff').pack(anchor=tk.W)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        self.log_text = tk.Text(log_frame, height=15, width=70,
                               bg='#000000', fg='#00ff00', font=("Courier", 9),
                               yscrollcommand=scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Footer
        footer = tk.Frame(self.root, bg='#2d2d2d', height=40)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        
        footer_text = tk.Label(footer, text="F6 = START | F7 = STOP | Made with ❤️ for Minecraft",
                              font=("Arial", 8), bg='#2d2d2d', fg='#666666')
        footer_text.pack(pady=8)
        
        # Hotkeye
        self.root.bind('<F6>', lambda e: self.start_bot())
        self.root.bind('<F7>', lambda e: self.stop_bot())
    
    def start_bot(self):
        """Włącz bota"""
        self.bot.start_bot()
        self.status_label.config(text="🟢 BOT WŁĄCZONY", fg='#66ff66')
        self.start_btn.config(state=tk.DISABLED, bg='#004400')
        self.stop_btn.config(state=tk.NORMAL, bg='#aa0000')
    
    def stop_bot(self):
        """Wyłącz bota"""
        self.bot.stop_bot()
        self.status_label.config(text="⭕ BOT WYŁĄCZONY", fg='#ff6666')
        self.start_btn.config(state=tk.NORMAL, bg='#00aa00')
        self.stop_btn.config(state=tk.DISABLED, bg='#440000')
    
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
        stats = f"Piętro: {self.bot.floor_count}/{self.bot.warp_interval}\n"
        stats += f"Warpy: {self.bot.warps_done}\n"
        stats += f"Przedmioty: {self.bot.items_clicked}\n"
        stats += f"Linki: {self.bot.links_clicked}"
        
        self.stats_text.config(text=stats)
        self.root.after(500, self.update_stats)


def main():
    root = tk.Tk()
    gui = BotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
