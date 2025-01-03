from flask import Flask, render_template
import pyodbc
import joblib
import pandas as pd

app = Flask(__name__)


model_path = "model_fake_news.pkl"
vectorizer_path = "vectorizer.pkl"
model = joblib.load(model_path)
vectorizer = joblib.load(vectorizer_path)


def get_db_connection():
    return pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=DESKTOP-0RNC19U;'
                          'DATABASE=seneweb;'
                          'Trusted_Connection=yes;')


def fetch_articles_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, category, title, link, meta FROM Articles")
        rows = cursor.fetchall()
        articles = []
        seen_titles = set()
        
        for row in rows:
            title = row[2]
            if title not in seen_titles:  
                seen_titles.add(title)
                articles.append({
                    "id": row[0],
                    "category": row[1],
                    "title": title,
                    "link": row[3],
                    "meta": row[4]
                })
        return articles
    finally:
        cursor.close()
        conn.close()


def fetch_articles_from_csv():
    df = pd.read_csv('SenePlus.csv')
    df = df.fillna("")  
    articles = []
    seen_titles = set()
    
    for _, row in df.iterrows():
        title = row['Titre']
        if title and title not in seen_titles:  
            seen_titles.add(title)
            articles.append({
                "id": None,
                "category": "SenePlus",
                "title": title,
                "link": row['like_lien'],
                "meta": "Source: SenePlus"
            })
        
    return articles



def predict_truthfulness(title):
    title_vectorized = vectorizer.transform([title])
    prediction = model.predict(title_vectorized)
    return "Vrai" if prediction[0] == 1 else "Faux"

@app.route("/")
def index():
    db_articles = fetch_articles_from_db()  
    csv_articles = fetch_articles_from_csv()  

    all_articles = db_articles + csv_articles  

    for article in all_articles:
        article["prediction"] = predict_truthfulness(article["title"])
    
    return render_template("index.html", articles=all_articles)

if __name__ == "__main__":
    app.run(debug=True)

