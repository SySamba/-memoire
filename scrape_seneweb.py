import logging
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyodbc

# Configuration de la journalisation
logging.basicConfig(filename='scraping.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_seneweb_featured():
    # Chemin vers le WebDriver
    driver_path = "C:\\Users\\HP\\Downloads\\edgedriver_win64\\msedgedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Edge(service=service)

    try:
        url = "https://www.seneweb.com/"
        driver.get(url)
        
        # Attendre que la page soit complètement chargée
        wait = WebDriverWait(driver, 15)
        featured_posts = wait.until(EC.presence_of_all_elements_located(
            (By.CLASS_NAME, "module_featured_post_content")
        ))

        # Extraire les données des articles
        scraped_data = []
        for post in featured_posts:
            try:
                category = post.find_element(By.CLASS_NAME, "module_featured_post_category").text.strip()
                title_element = post.find_element(By.TAG_NAME, "h1").find_element(By.TAG_NAME, "a")
                title = title_element.text.strip()
                link = title_element.get_attribute("href").strip()
                meta = post.find_element(By.CLASS_NAME, "post_meta.module_featured_post_meta").text.strip()

                scraped_data.append({"category": category, "title": title, "link": link, "meta": meta})
            except Exception as e:
                logging.error(f"Erreur lors de l'extraction d'un article : {e}")

        save_to_sql_server(scraped_data)
        logging.info(f"{len(scraped_data)} articles insérés avec succès.")
    except Exception as e:
        logging.error(f"Erreur principale : {e}")
    finally:
        driver.quit()

def save_to_sql_server(scraped_data):
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=DESKTOP-0RNC19U;'
                          'DATABASE=seneweb;'
                          'Trusted_Connection=yes;')
    cursor = conn.cursor()
    for data in scraped_data:
        try:
            cursor.execute('INSERT INTO Articles (category, title, link, meta) VALUES (?, ?, ?, ?)',
                           data['category'], data['title'], data['link'], data['meta'])
            conn.commit()
        except Exception as e:
            logging.error(f"Erreur lors de l'insertion : {e}")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    while True:
        logging.info("Lancement du scraping...")
        scrape_seneweb_featured()
        time.sleep(600)  
