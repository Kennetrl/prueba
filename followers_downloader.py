# followers_downloader.py
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
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException


class FollowersDownloader:
    """Clase para la descarga inicial de nombres de usuario seguidos de una cuenta objetivo."""

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None

    # --- Métodos de Utilidad (Iniciador y Espera) ---

    def _init_driver(self, headless=False):
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

    # --- Lógica de Login (Corregida con manejo de pop-ups) ---
    def _login_instagram(self) -> bool:
        """Realiza el login en Instagram y maneja pop-ups post-login."""
        if not self.driver:
            self._init_driver(headless=False)

        wait = self._wait_for(20)
        self.driver.get("https://www.instagram.com/")

        try:
            user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            pass_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        except Exception:
            print("❌ Timeout: No se encontraron los campos de login.")
            return False

        # Enviar credenciales
        user_input.clear()
        user_input.send_keys(self.username)
        pass_input.clear()
        pass_input.send_keys(self.password)

        try:
            # Intentar clic en el botón de login
            submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[./div[text()='Iniciar sesión']]")))
            submit_btn.click()
        except Exception:
            print("❌ No se pudo hacer clic en el botón de login.")
            return False

        # Manejo de pop-ups y espera al feed
        try:
            # 1. Esperar a que la URL cambie (éxito del login)
            wait.until(lambda d: "instagram.com" in d.current_url and "login" not in d.current_url)
            time.sleep(3)
            print("✅ Login exitoso, intentando cerrar notificaciones/guardado.")

            # 2. Intentar cerrar el pop-up "Guardar información de inicio de sesión"
            try:
                now_not_btn_save = wait.until(EC.element_to_be_clickable((By.XPATH,
                                                                          "//div[text()='Guardar información de inicio de sesión']/following-sibling::div//button[text()='Ahora no']")))
                now_not_btn_save.click()
                print("   -> Pop-up 'Guardar información' cerrado.")
                time.sleep(2)
            except TimeoutException:
                pass

                # 3. Intentar cerrar el pop-up "Activar notificaciones"
            try:
                notification_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Ahora no']")))
                notification_btn.click()
                print("   -> Pop-up 'Notificaciones' cerrado.")
                time.sleep(2)
            except TimeoutException:
                pass

            return True

        except Exception as e:
            print(f"❌ Fallo al detectar la sesión iniciada o al cerrar pop-ups: {e}")
            return False

    # --- Lógica de Búsqueda (Corregida con navegación directa) ---
    def _buscar_usuario(self, username_objetivo):
        """Navega directamente al perfil del usuario objetivo después del login."""
        wait = WebDriverWait(self.driver, 15)
        profile_url = f"https://www.instagram.com/{username_objetivo}/"

        print(f"🔍 Navegando directamente a: {profile_url}")
        self.driver.get(profile_url)

        try:
            # Esperar a que el header del perfil (donde están las stats) esté presente
            wait.until(EC.presence_of_element_located((By.XPATH, "//header")))

            # Comprobar si la página realmente cargó un perfil (Evita errores de "Page Not Found")
            if "page not found" in self.driver.page_source.lower() or "no se pudo encontrar" in self.driver.page_source.lower():
                print(f"❌ Error: La URL {username_objetivo} no parece ser un perfil válido.")
                return False

            print(f"✅ Perfil de @{username_objetivo} cargado con éxito.")
            time.sleep(3)
            return True

        except TimeoutException:
            print("❌ Timeout al cargar el perfil. No se encontró el header del perfil.")
            return False
        except Exception as e:
            print(f"❌ Error durante la navegación directa al perfil: {e}")
            return False

    # --- Guardado de Datos ---
    def _guardar_a_csv(self, data: list[str], filename: str):
        """Guarda una lista de usernames en un archivo CSV."""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['username'])
                writer.writerows([[username] for username in data])
            print(f"\n🎉 Lista de usuarios guardada exitosamente en: **{filename}**")
        except Exception as e:
            print(f"\n❌ Error al guardar el archivo CSV: {e}")

    # --- Lógica de Scroll y Extracción (Original) ---
    def _obtener_seguidos(self, limite=500) -> list[str]:
        """Abre el modal de seguidos y scrollea para obtener la lista."""
        wait = self._wait_for(15)
        seguidos_set = set()

        # Paso 1: Abrir el modal
        try:
            seguidos_link_xpath = "//a[contains(@href, '/following/')]"
            seguidos_link = wait.until(
                EC.element_to_be_clickable((By.XPATH, seguidos_link_xpath))
            )
            self.driver.execute_script("arguments[0].click();", seguidos_link)
            print("✅ Se abrió el modal de seguidos.")
            time.sleep(3)

            # Paso 2: Detectar el contenedor con scroll
            modal = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']")))
            # Intenta encontrar el contenedor desplazable. Este XPath puede cambiar si Instagram actualiza la interfaz.
            scroll_container = modal.find_element(By.XPATH,
                                                  ".//div[contains(@style,'height')]//div[contains(@style,'overflow')][1]")

            if not scroll_container:
                print("❌ No se encontró el contenedor desplazable del modal.")
                return []

            print("🌀 Contenedor desplazable detectado, comenzando scroll persistente...")

            # Variables de control de persistencia
            max_scroll_attempts_without_new_users = 7
            no_progress_count = 0
            last_count = 0

            while len(seguidos_set) < limite:
                # 1. Extraer usuarios visibles
                links = scroll_container.find_elements(By.XPATH,
                                                       ".//a[contains(@href,'/') and not(contains(@tabindex, '-1'))]")

                for a in links:
                    try:
                        href = a.get_attribute("href")
                        if href and "instagram.com" in href:
                            # Filtramos para obtener solo el username
                            username = href.split("/")[-2]
                            if username and username not in seguidos_set:
                                seguidos_set.add(username)
                    except Exception:
                        continue

                if len(seguidos_set) >= limite:
                    break

                print(f"📊 Capturados: {len(seguidos_set)} (Scrolls sin progreso: {no_progress_count})", end="\r")

                # 2. Control de progreso
                if len(seguidos_set) == last_count:
                    no_progress_count += 1
                else:
                    no_progress_count = 0

                last_count = len(seguidos_set)

                # 3. Realizar Scroll y esperar
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_container)
                time.sleep(random.uniform(3.0, 4.5))

                # 4. Condición de salida
                if no_progress_count >= max_scroll_attempts_without_new_users:
                    print(f"\n⚠️ Límite de reintentos ({max_scroll_attempts_without_new_users}) alcanzado.")
                    break

            seguidos_list = list(seguidos_set)
            print(f"\n✅ Total de seguidos recolectados: {len(seguidos_list)}")
            return seguidos_list

        except Exception as e:
            print(f"❌ Error al obtener seguidos: {e}")
            return []

    # --- Método de Ejecución Principal ---
    def download_and_save_followers(self, perfil_objetivo: str, limite: int, csv_filename: str):
        """Descarga la lista inicial de seguidos y la guarda en un CSV."""

        if not self._login_instagram():
            print("❌ Login fallido. No se puede continuar.")
            return

        if not self._buscar_usuario(perfil_objetivo):
            print("❌ No se pudo encontrar el usuario objetivo o cargar el perfil.")
            return

        print(f"Comenzando el scraping de seguidos de {perfil_objetivo}...")
        seguidos_usernames = self._obtener_seguidos(limite=limite)

        if seguidos_usernames:
            self._guardar_a_csv(seguidos_usernames, csv_filename)
        else:
            print("⚠️ No se pudieron obtener seguidos.")

    def close_driver(self):
        """Cierra el driver de Selenium."""
        if self.driver:
            self.driver.quit()
            print("Cerrando navegador del Downloader.")