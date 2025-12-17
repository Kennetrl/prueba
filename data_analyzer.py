# data_analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
import numpy as np


class DataAnalyzer:
    """Clase para limpiar datos, aplicar análisis del primer dígito y graficar (Ley de Benford)."""

    def __init__(self, input_file_path):
        self.input_file_path = input_file_path
        self.df = pd.DataFrame()

    def _convert_count_to_numeric(self, count_val):
        """Intenta convertir el conteo (que puede tener K, M, o puntos/comas) a un número entero."""
        # Si ya es un número, retornarlo directamente
        if isinstance(count_val, (int, float)):
            if pd.isna(count_val):
                return np.nan
            return int(count_val) if count_val > 0 else np.nan
        
        # Si es NaN o None
        if pd.isna(count_val) or count_val is None:
            return np.nan
        
        # Convertir a string para procesar
        if not isinstance(count_val, str):
            try:
                count_val = str(count_val)
            except:
                return np.nan

        s = count_val.upper().replace(',', '').strip()

        # Si contiene valores especiales, retornar NaN
        if any(x in s for x in ['PRIVADA', 'NO_EXISTE', 'NO_ENCONTRADO', 'TIMEOUT', 'ERROR']):
            return np.nan

        if 'K' in s:
            try:
                return int(float(s.replace('K', '')) * 1000)
            except:
                return np.nan
        if 'M' in s:
            try:
                return int(float(s.replace('M', '')) * 1000000)
            except:
                return np.nan

        # Eliminar cualquier punto residual que no haya sido manejado por K/M
        s = s.replace('.', '')

        try:
            return int(s) if s else np.nan
        except ValueError:
            return np.nan  # Retorna NaN para valores inválidos

    def clean_and_prepare_data(self):
        """Lee el archivo (CSV o XLSX), elimina filas no numéricas y prepara los datos."""
        try:
            # Detectar formato y leer
            if self.input_file_path.endswith('.xlsx'):
                self.df = pd.read_excel(self.input_file_path, engine='openpyxl')
                print(f"Leídos {len(self.df)} registros del archivo XLSX.")
            else:
                self.df = pd.read_csv(self.input_file_path)
                print(f"Leídos {len(self.df)} registros del archivo CSV.")
        except FileNotFoundError:
            print(f"❌ Error: Archivo '{self.input_file_path}' no encontrado.")
            return
        except Exception as e:
            print(f"❌ Error al leer el archivo: {e}")
            return

        # Verificar que existe la columna de seguidores
        if 'seguidores' not in self.df.columns:
            # Intentar con el nombre antiguo por compatibilidad
            if 'followers_count' in self.df.columns:
                self.df['seguidores'] = self.df['followers_count']
            else:
                print("❌ Error: No se encontró la columna 'seguidores' en el archivo.")
                return

        # Aplicar la limpieza
        self.df['followers_numeric'] = self.df['seguidores'].apply(self._convert_count_to_numeric)

        # Filtrar las filas con conteos válidos (> 0)
        self.df.dropna(subset=['followers_numeric'], inplace=True)
        self.df = self.df[self.df['followers_numeric'] > 0]

        self.df['followers_numeric'] = self.df['followers_numeric'].astype(int)

        print(f"✅ Limpieza completada. Quedan **{len(self.df)}** registros válidos para el análisis.")

    def analyze_and_plot_first_digit(self, graph_filename: str):
        """Saca el primer dígito, calcula frecuencias y grafica la Ley de Benford."""
        if self.df.empty:
            print("⚠️ No hay datos limpios para analizar.")
            return

        # Sacar el primer dígito de la izquierda
        self.df['first_digit'] = self.df['followers_numeric'].astype(str).str[0].astype(int)

        # Conteo de cada dígito (1 al 9)
        digit_counts = self.df['first_digit'].value_counts().sort_index()
        total_count = digit_counts.sum()
        frequencies = (digit_counts / total_count) * 100

        print("\n--- Resultados del Análisis del Primer Dígito ---")
        print(frequencies)

        # Gráfico
        self._create_benford_plot(frequencies, graph_filename)

    def _create_benford_plot(self, frequencies: pd.Series, filename: str):
        """Genera y guarda el gráfico de Benford."""

        # Distribución teórica de Benford (%)
        benford_data = {
            1: 30.1, 2: 17.6, 3: 12.5, 4: 9.7, 5: 7.9,
            6: 6.7, 7: 5.8, 8: 5.1, 9: 4.6
        }
        benford_df = pd.Series(benford_data)

        # Asegurar que el índice coincida (1-9)
        frequencies = frequencies.reindex(range(1, 10), fill_value=0)

        plt.figure(figsize=(10, 6))

        # Gráfico de barras de las frecuencias reales
        plt.bar(frequencies.index, frequencies.values, color='teal', alpha=0.7, label='Frecuencia Real')

        # Gráfico de línea de la Ley de Benford
        plt.plot(benford_df.index, benford_df.values, marker='o', linestyle='--', color='red',
                 label='Ley de Benford Teórica')

        plt.title('Distribución del Primer Dígito de Seguidores (Análisis de Benford)')
        plt.xlabel('Primer Dígito (1 al 9)')
        plt.ylabel('Frecuencia (%)')
        plt.xticks(range(1, 10))
        plt.grid(axis='y', linestyle='--')
        plt.legend()
        plt.tight_layout()

        plt.savefig(filename)
        print(f"📸 Gráfico de Benford guardado en: **{filename}**")