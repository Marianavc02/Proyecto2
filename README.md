# Proyecto Django - ProyectoSDB

Este es un proyecto desarrollado con **Django**.  
A continuación se explican los pasos para clonar el repositorio y ejecutarlo en un entorno virtual.

---

## Requisitos previos
- Python 3.11+ instalado
- Git instalado

---

## Clonar el repositorio
```bash
git clone https://github.com/TU_USUARIO/ProyectoSDB.git
cd ProyectoSDB
```
## Crear y activar el entorno virtual

 - Windows (PowerShell)
```bash
python -m venv env # Para crear
.\env\Scripts\activate # Para activar
```

 - Windows (cmd)
```bash
python -m venv env # Para crear
env\Scripts\activate.bat # Para activar
```

 - Linux / Mac
```bash
python3 -m venv env # Para crear
source env/bin/activate # Para activar
```
---

## Instalar dependencias

Con el entorno virtual activado, instala los paquetes necesarios:
```bash
pip install -r requirements.txt