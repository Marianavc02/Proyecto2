## Nombre 
  SDB ToolBox

# Proyecto Django - ProyectoSDB

  Este proyecto consiste en el desarrollo de una página web que permite a los empleados de la empresa Stanley Black & Decker (regional Medellín) acceder a su beneficio de compra de herramientas a precio de fabrica, mediante una solución integrada, amigable, eficiente y con una expereincia de usuario amena, además de integrar un panel de administrador para que este pueda manejar aspectos claves del beneficio ofrecido por la compañía. 

Este es un proyecto desarrollado con **Django**.  
A continuación se explican los pasos para clonar el repositorio y ejecutarlo en un entorno virtual.

---

## Requisitos previos
- Python 3.11+ instalado
- Git instalado

---

## Clonar el repositorio
```bash
git clone [https://github.com/TU_USUARIO/ProyectoSDB.git](https://github.com/Marianavc02/Proyecto2.git)
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
