# 🎮 Minecraft Farm Bot v1.0

Automatyczny bot do Minecrafta, który zbiera plony z farmy, teleportuje się na warpy i klika przedmioty + linki.

## 📋 Funkcje

✅ **Automatyczne chodzenie** - A i D po farmie  
✅ **Teleportacja** - Co 10 pięter klika bind warpa (/)  
✅ **Zbieranie przedmiotów** - Szuka pogrubionego przedmiotu w EQ i klika  
✅ **Klikanie linków** - Szuka linków na chacie i je potwierdza  
✅ **GUI** - Graficzny interfejs z logami i statystyką  

## 📦 Wymagania

- Python 3.9+
- Windows / Linux / Mac

## 🚀 Instalacja

### 1. Zainstaluj Python
Pobierz z: https://www.python.org/

### 2. Zainstaluj biblioteki

Otwórz terminal/CMD w folderze bota i wklej:
```bash
pip install -r requirements.txt
```

## 🎮 Jak używać

### Wersja z GUI (rekomendowana)

```bash
python minecraft_farm_bot_gui.py
```

Otworzy się okno z:
- Przyciskami START/STOP
- Statusem bota
- Logami na żywo
- Statystyką (piętro, warpy, przedmioty, linki)

### Wersja konsolowa (bez GUI)

```bash
python minecraft_farm_bot.py
```

## ⌨️ Hotkeye

| Klawisz | Akcja |
|---------|-------|
| **F6** | Włącz bota |
| **F7** | Wyłącz bota |

## 📊 Logi w konsoli

Bot wypisuje wszystkie akcje:
```
[FARMA] Piętro: 1/10
[FARMA] Piętro: 2/10
...
[WARP] Po 10 piętrach - teleportacja!
[EQ] ✓ Znaleziono pogrubiony przedmiot!
[EQ] ✓ Kliknięto!
[CHAT] ✓ Znaleziono link!
[CHAT] ✓ Potwierdzono!
```

## ⚙️ Konfiguracja

Otwórz `minecraft_farm_bot_gui.py` i zmień:

```python
self.warp_interval = 10  # Zmień na inną wartość aby warp co X pięter
```

## 🐛 Troubleshooting

**GUI nie startuje?**
```bash
pip install --upgrade tkinter
```
(Na Linuxie: `sudo apt-get install python3-tk`)

**Bot nie wykrywa przedmiotu?**
- Upewnij się, że EQ się otwiera
- Zmień parametry w funkcji `find_enlarged_text()`

**Bot nie klika linku?**
- Linki mogą mieć inny kolor
- Zmień HSV range w `find_clickable_link()`

## 📝 Notatki

- Bot działa tylko gdy minecraft jest w fokusie
- Nie otwiera sam EQ - czeka na losowe otwarcie
- Po każdym warpia czeka 3 sekundy przed powrotem na farmę
- GUI aktualizuje się co 0.5 sekund

## ❓ Pytania?

Zmień parametry samodzielnie lub skontaktuj się z autorem!

---

**Made with ❤️ for Minecraft farmers**
