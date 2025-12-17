# profile_scraper.py
import os
import time
import random
import csv
from selenium import webdriver
from selenium.webdriver import Chrome
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class ProfileScraper:
    """Clase para el login y el scraping de conteos de seguidores de una lista de usuarios."""

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None

    # --- Métodos de Utilidad ---
    def _init_driver(self, headless=True):
        """Inicializa y configura el driver de Chrome."""
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1600,900")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        if headless:
            options.add_argument("--headless=new")

        service = Service(ChromeDriverManager().install())
        self.driver = Chrome(service=service, options=options)
        return self.driver

    def _wait_for(self, timeout=15):
        """Función de conveniencia para WebDriverWait."""
        return WebDriverWait(self.driver, timeout)

    def _login_instagram(self) -> bool:
        """Realiza el login en Instagram (similar a la lógica del Downloader)."""
        if not self.driver:
            self._init_driver(headless=True)  # Usamos headless aquí para ser más rápido

        wait = self._wait_for(20)
        self.driver.get("https://www.instagram.com/")

        try:
            user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        except Exception:
            return False

        user_input.send_keys(self.username)
        pass_input.send_keys(self.password)

        try:
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[./div[text()='Iniciar sesión']]")))
            submit_btn.click()
        except Exception:
            return False

        try:
            wait.until(lambda d: "instagram.com" in d.current_url and "login" not in d.current_url)
            time.sleep(3)
            print("✅ Login exitoso (Scraper).")
            return True

        except Exception:
            print("❌ Fallo al detectar la sesión iniciada (Scraper).")
            return False

    def read_usernames_from_csv(self, filename: str) -> list[str]:
        """Lee la lista de usernames desde el archivo CSV generado en la Fase 1."""
        usernames = []
        try:
            with open(filename, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # Saltar la cabecera
                for row in reader:
                    if row:
                        usernames.append(row[0])
            print(f"✅ Leídos {len(usernames)} usuarios de '{filename}'.")
            return usernames
        except FileNotFoundError:
            print(f"❌ Error: Archivo '{filename}' no encontrado. Asegúrate de haber ejecutado la Fase 1.")
            return []
        except Exception as e:
            print(f"❌ Error al leer el CSV: {e}")
            return []

    def _extract_number_from_text(self, text: str) -> str:
        """Extrae números de un texto, manejando K, M, etc."""
        if not text:
            return ""
        # Limpiar y extraer números
        text = text.replace(',', '').replace('.', '').strip()
        numbers = ''.join(filter(str.isdigit, text))
        return numbers if numbers else ""

    def _get_profile_info(self, username: str) -> dict:
        """Extrae información completa del perfil: seguidores, seguidos, biografía."""
        wait = self._wait_for(10)
        profile_url = f"https://www.instagram.com/{username}/"
        self.driver.get(profile_url)

        result = {
            'username': username,
            'seguidores': '',
            'seguidos': '',
            'biografia': ''
        }

        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "header")))
            time.sleep(random.uniform(2, 3))

            # Detectar cuenta privada primero
            private_indicators = [
                "//*[contains(text(), 'Esta cuenta es privada')]",
                "//*[contains(text(), 'This account is private')]",
                "//*[contains(@class, 'rkEop')]"
            ]

            for indicator in private_indicators:
                try:
                    if self.driver.find_elements(By.XPATH, indicator):
                        result['seguidores'] = "PRIVADA"
                        result['seguidos'] = "PRIVADA"
                        result['biografia'] = "PRIVADA"
                        return result
                except:
                    pass

            # Detectar cuenta inexistente
            if "Lo sentimos, no pudimos encontrar" in self.driver.page_source or "Sorry, this page isn't available" in self.driver.page_source:
                result['seguidores'] = "NO_EXISTE"
                result['seguidos'] = "NO_EXISTE"
                result['biografia'] = "NO_EXISTE"
                return result

            # Extraer SEGUIDORES (followers)
            followers_selectors = [
                "//a[contains(@href, '/followers')]//span",
                "//a[contains(@href, '/followers')]",
                "//header//section//li[2]//span",
                "//header//ul//li[2]//span",
            ]
            
            for selector in followers_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and any(char.isdigit() for char in text):
                            numbers = self._extract_number_from_text(text)
                            if numbers:
                                result['seguidores'] = numbers
                                break
                    if result['seguidores']:
                        break
                except:
                    continue

            # Extraer SEGUIDOS (following)
            following_selectors = [
                "//a[contains(@href, '/following')]//span",
                "//a[contains(@href, '/following')]",
                "//header//section//li[3]//span",
                "//header//ul//li[3]//span",
            ]
            
            for selector in following_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and any(char.isdigit() for char in text):
                            numbers = self._extract_number_from_text(text)
                            if numbers:
                                result['seguidos'] = numbers
                                break
                    if result['seguidos']:
                        break
                except:
                    continue

            # Extraer BIOGRAFÍA (description)
            # La biografía en Instagram está generalmente en un div específico dentro del header
            bio_selectors = [
                "//header//section//div[contains(@class, '-vDIg')]//span",
                "//header//div[contains(@class, '-vDIg')]//span",
                "//header//section//div[contains(@class, '_aacl')]//span",
                "//header//div[contains(@class, '_aacl')]//span",
                "//header//section//div//h1/following-sibling::div//span",
                "//header//section//div//span[not(ancestor::a)]",
            ]
            
            for selector in bio_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        # La biografía generalmente tiene más de 5 caracteres y menos de 500
                        # No contiene números al inicio y no es un enlace
                        if text and 5 < len(text) < 500:
                            # Verificar que no sea estadísticas o enlaces
                            if (not any(char.isdigit() for char in text[:10]) and 
                                not text.startswith('http') and 
                                'seguidores' not in text.lower() and 
                                'seguidos' not in text.lower() and
                                'following' not in text.lower() and
                                'followers' not in text.lower() and
                                'publicaciones' not in text.lower() and
                                'posts' not in text.lower()):
                                result['biografia'] = text
                                break
                    if result['biografia']:
                        break
                except:
                    continue

            # Si no se encontró biografía con los selectores anteriores, intentar método alternativo
            if not result['biografia']:
                try:
                    # Buscar en el header cualquier texto que parezca biografía
                    header = self.driver.find_element(By.TAG_NAME, "header")
                    # Buscar divs que contengan la biografía (generalmente después del nombre de usuario)
                    divs = header.find_elements(By.XPATH, ".//div//span")
                    for div in divs:
                        text = div.text.strip()
                        if text and 10 < len(text) < 500:
                            # Filtrar textos que no son biografía
                            if (not any(char.isdigit() for char in text[:10]) and 
                                'seguidores' not in text.lower() and 
                                'seguidos' not in text.lower() and
                                'following' not in text.lower() and
                                'followers' not in text.lower() and
                                not text.startswith('http')):
                                result['biografia'] = text
                                break
                except:
                    pass

            # Si aún no hay valores, marcar como no encontrado
            if not result['seguidores']:
                result['seguidores'] = "NO_ENCONTRADO"
            if not result['seguidos']:
                result['seguidos'] = "NO_ENCONTRADO"
            if not result['biografia']:
                result['biografia'] = ""

            return result

        except TimeoutException:
            result['seguidores'] = "TIMEOUT"
            result['seguidos'] = "TIMEOUT"
            result['biografia'] = "TIMEOUT"
            return result
        except Exception as e:
            print(f"Error al procesar {username}: {e}")
            result['seguidores'] = "ERROR_DESCONOCIDO"
            result['seguidos'] = "ERROR_DESCONOCIDO"
            result['biografia'] = "ERROR_DESCONOCIDO"
            return result

    def _save_results_to_file(self, data: list[dict], filename: str):
        """Guarda la lista de diccionarios en CSV o XLSX según la extensión del archivo."""
        if not data:
            return
        
        # Determinar formato según extensión
        if filename.endswith('.xlsx'):
            self._save_to_xlsx(data, filename)
        else:
            self._save_to_csv(data, filename)

    def _save_to_csv(self, data: list[dict], filename: str):
        """Guarda los datos en formato CSV."""
        fieldnames = ['username', 'seguidores', 'seguidos', 'biografia']
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            print(f"\n🎉 Resultados guardados exitosamente en: **{filename}**")
        except Exception as e:
            print(f"\n❌ Error al guardar el archivo CSV: {e}")

    def _save_to_xlsx(self, data: list[dict], filename: str):
        """Guarda los datos en formato XLSX."""
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            # Asegurar el orden de las columnas
            df = df[['username', 'seguidores', 'seguidos', 'biografia']]
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\n🎉 Resultados guardados exitosamente en: **{filename}**")
        except Exception as e:
            print(f"\n❌ Error al guardar el archivo XLSX: {e}")
            # Fallback a CSV si falla XLSX
            csv_filename = filename.replace('.xlsx', '.csv')
            self._save_to_csv(data, csv_filename)

    # --- Método de Ejecución Principal ---
    def scrape_follower_counts(self, usernames_list: list[str], output_file: str):
        """Método principal para ejecutar el scraping completo de perfiles."""
        if not self._login_instagram():
            return

        resultados = []
        print(f"Comenzando a escanear {len(usernames_list)} perfiles...")

        for i, username in enumerate(usernames_list):
            print(f"\n--- Procesando {i + 1}/{len(usernames_list)}: @{username} ---")
            time.sleep(random.uniform(10, 15))
            profile_info = self._get_profile_info(username)

            resultados.append(profile_info)
            print(f"✅ @{username} -> Seguidores: {profile_info['seguidores']}, Seguidos: {profile_info['seguidos']}, Bio: {profile_info['biografia'][:50] if profile_info['biografia'] else 'N/A'}...")

        self._save_results_to_file(resultados, output_file)

    def close_driver(self):
        """Cierra el driver de Selenium."""
        if self.driver:
            self.driver.quit()
            print("Cerrando navegador del Scraper.")