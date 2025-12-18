# 🔍 Instagram Benford Analyzer

Este proyecto es una herramienta de automatización y análisis estadístico diseñada para extraer información de perfiles de Instagram y validar la autenticidad de sus métricas utilizando la **Ley de Benford**.

## 📋 Descripción del Proyecto
El programa analiza a los usuarios que una cuenta específica sigue (following) para determinar si las estadísticas de esa red de contactos siguen una distribución numérica natural o si presentan anomalías.

Se divide en tres fases modulares:
1.  **Fase 1 (Downloader):** Extracción de seguidor de un usuario de instagram mediante scroll automático.
2.  **Fase 2 (Scraper):** Recolección de metadatos (seguidores, seguidos, biografía) de cada perfil.

---

## 🛠️ Requisitos e Instalación

### Pre-requisitos
* **Python 3.8 o superior**
* **Google Chrome** instalado.
* **Credenciales de Instagram** (se recomienda usar una cuenta secundaria de pruebas).

### Instalación de dependencias
Ejecuta el siguiente comando en tu terminal para instalar las librerías necesarias:

###Estrategia
La mejor estrategia sería utilizar los datos de la Fase 2 para identificar palabras clave en su biografía (como "futbol") y cruzar esa información con su nivel de actividad social; si sus métricas de seguidores en la Fase 3 son consistentes y orgánicas según la Ley de Benford, podrías concluir que es una persona disciplinata y auténtica con quien podrías conectar ofreciéndole contenido o productos que resuenen con su rutina de bienestar, enfocándote en la calidad y la comunidad en lugar de solo en la apariencia.

```bash
pip install selenium webdriver-manager pandas openpyxl
