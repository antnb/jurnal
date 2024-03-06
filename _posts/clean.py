import re

# Buka file teks
with open('urls.txt', 'r') as file:
    lines = file.readlines()

# Pola untuk mencocokkan URL dengan download id
pattern = r'https:\/\/ojs\.unud\.ac\.id\/index\.php\/komunikasi\/article\/view\/\d+\/\d+'

# Filter baris yang tidak mengandung download id
filtered_lines = [line for line in lines if not re.search(pattern, line)]

# Tulis kembali ke file teks
with open('komunikasi.txt', 'w') as file:
    file.writelines(filtered_lines)

