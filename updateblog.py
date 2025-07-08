import os
import re

# Zapytaj użytkownika o ścieżkę do pliku .md
filepath = input("🔍 Podaj pełną ścieżkę do pliku .md: ").strip()

# Sprawdź, czy plik istnieje
if not os.path.isfile(filepath):
    print(f"❌ Plik nie istnieje: {filepath}")
    exit(1)

# Wczytaj zawartość pliku
with open(filepath, "r", encoding="utf-8") as file:
    content = file.read()

# Znajdź wszystkie linki do obrazów w formacie ![[plik.png]]
images = re.findall(r'!\[\[(.+?\.(?:png|jpg|jpeg|gif|webp))\]\]', content, re.IGNORECASE)

# Zamień każdy link na markdownowy kompatybilny z Hugo
for image in images:
    alt_text = os.path.splitext(image)[0]
    hugo_image = f"![{alt_text}](/images/{image.replace(' ', '%20')})"
    content = content.replace(f"![[{image}]]", hugo_image)

# Nadpisz zawartość pliku
with open(filepath, "w", encoding="utf-8") as file:
    file.write(content)

print("✅ Zakończono formatowanie linków do obrazków.")
