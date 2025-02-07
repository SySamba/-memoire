# Utiliser une image de base Python
FROM python:3.9-slim

# Installer les bibliothèques système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY app.py .
COPY fake_news.pkl .
COPY vectorize.pkl .
COPY SenePlus.csv .
COPY seneco.csv .
COPY senewebs.csv .
COPY walfadjri.csv .
COPY templates/ ./templates/
COPY static/ ./static/
# Installer les dépendances Python
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Exposer le port sur lequel l'application Flask va écouter
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
