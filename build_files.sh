#!/bin/bash

# Pastikan pip terinstal
python3 -m pip install --upgrade pip

# Instal semua dependensi
python3 -m pip install -r requirements.txt

# PENTING: Kumpulkan Static Files
# --noinput agar tidak ada prompt
# --clear untuk menghapus file lama
echo "Collecting static files..."
python3 manage.py collectstatic --noinput --clear

# Jalankan migrasi database (jika ada perubahan model)
echo "Running migrations..."
python3 manage.py migrate --noinput