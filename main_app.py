# main_app.py
import os
import sys
from followers_downloader import FollowersDownloader
from profile_scraper import ProfileScraper
from data_analyzer import DataAnalyzer

# --- CONFIGURACIÓN GLOBAL ---
# ¡IMPORTANTE! Reemplaza con tus credenciales
USER = os.getenv("IG_TEST_USER", "melares23@gmail.com")
PASSWORD = os.getenv("IG_TEST_PASS", "Lunita1780L")

# Variables de la cuenta objetivo
CUENTA_OBJETIVO = "nayeli.nxx"  # <--- Perfil a analizar
LIMITE_SEGUIDOS = 300  # Límite para el primer scraping (para no tardar demasiado)


class MainApp:
    """Clase principal que coordina las tres fases del programa."""

    def __init__(self, username, password, target_account, limit):
        self.username = username
        self.password = password
        self.target_account = target_account
        self.limit = limit

        # Archivos de salida dinámicos
        self.following_list_csv = f"{target_account}_following_list.csv"
        self.output_data_file = f"{target_account}_profile_data.xlsx"  # Cambiado a XLSX
        self.graph_filename = f"{target_account}_benford_analysis.png"

        print(f"🌟 **Iniciando Análisis de Benford para seguidos de:** {target_account}")

    # --- Métodos de Fase Individual ---

    def _run_phase_1_download(self):
        """FASE 1: Descarga de Nombres de Usuario."""
        print("\n--- 💻 Fase 1: Descarga de Nombres de Usuario (Seguidos) ---")
        downloader = FollowersDownloader(self.username, self.password)
        try:
            downloader.download_and_save_followers(self.target_account, self.limit, self.following_list_csv)
        except Exception as e:
            print(f"⚠️ Error en la Fase 1: {e}")
        finally:
            downloader.close_driver()

    def _run_phase_2_scrape_counts(self):
        """FASE 2: Recopilación de Información Completa de Perfiles."""
        if not os.path.exists(self.following_list_csv):
            print(f"\n⚠️ Necesitas ejecutar la Fase 1 primero. Archivo '{self.following_list_csv}' no encontrado.")
            return

        print("\n--- 🖱️ Fase 2: Recopilación de Información de Perfiles (Seguidores, Seguidos, Biografía) ---")
        scraper = ProfileScraper(self.username, self.password)
        usernames_to_count = scraper.read_usernames_from_csv(self.following_list_csv)

        if usernames_to_count:
            try:
                scraper.scrape_follower_counts(usernames_to_count, self.output_data_file)
            except Exception as e:
                print(f"⚠️ Error en la Fase 2: {e}")
            finally:
                scraper.close_driver()
        else:
            print("❌ No hay usuarios para procesar. Terminando Fase 2.")

    def _run_phase_3_analyze(self):
        """FASE 3: Limpieza y Análisis de Benford."""
        if not os.path.exists(self.output_data_file):
            print(f"\n⚠️ Necesitas ejecutar la Fase 2 primero. Archivo '{self.output_data_file}' no encontrado.")
            return

        print("\n--- 📈 Fase 3: Limpieza, Análisis de Benford y Gráfico ---")
        analyzer = DataAnalyzer(self.output_data_file)
        analyzer.clean_and_prepare_data()
        analyzer.analyze_and_plot_first_digit(self.graph_filename)

    def run_phase(self, phase_to_run):
        """Ejecuta una fase específica."""

        if phase_to_run == 1:
            self._run_phase_1_download()
        elif phase_to_run == 2:
            self._run_phase_2_scrape_counts()
        elif phase_to_run == 3:
            self._run_phase_3_analyze()
        elif phase_to_run == 0:
            # Ejecutar completo
            self._run_phase_1_download()
            self._run_phase_2_scrape_counts()
            self._run_phase_3_analyze()
        else:
            print("\n❌ Opción no válida. Por favor, selecciona 0, 1, 2 o 3.")


# ----------------------------------------------------------------------
# LÓGICA DE INICIO Y MENÚ INTERACTIVO
# ----------------------------------------------------------------------

def display_menu():
    """Muestra el menú y pide la opción al usuario."""
    print("\n" + "=" * 40)
    print("      🔍 ANALIZADOR DE SEGUIDOS (BENFORD)")
    print("=" * 40)
    print("Selecciona la fase a ejecutar:")
    print("  [1] 💻 FASE 1: Recolectar Nombres de Usuario (Seguidos)")
    print("  [2] 🖱️ FASE 2: Recolectar Info Completa (Seguidores, Seguidos, Biografía) (Requiere Fase 1)")
    print("  [3] 📈 FASE 3: Análisis de Benford y Gráfico (Requiere Fase 2)")
    print("  [0] ✨ EJECUTAR PROCESO COMPLETO (1 -> 2 -> 3)")
    print("  [4] 🛑 Salir")
    print("=" * 40)

    while True:
        try:
            choice = input("Ingresa tu opción (0-4): ").strip()
            if choice == '4':
                sys.exit(0)
            return int(choice)
        except ValueError:
            print("Entrada inválida. Por favor, ingresa un número.")


if __name__ == '__main__':

    phase = -1  # Valor inicial que indica que se necesita preguntar

    # 1. Verificar si hay argumentos en línea de comandos (Ejecución silenciosa)
    if len(sys.argv) > 1:
        try:
            phase = int(sys.argv[1])
        except ValueError:
            print("❌ El argumento debe ser un número entero (0, 1, 2 o 3).")
            sys.exit(1)

    app = MainApp(USER, PASSWORD, CUENTA_OBJETIVO, LIMITE_SEGUIDOS)

    # 2. Si no hay argumento, mostrar el menú interactivo
    if phase == -1:
        phase = display_menu()

    app.run_phase(phase)