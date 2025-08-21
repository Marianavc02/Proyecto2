from django.shortcuts import render
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Empleado

# Subir archivo Excel e importar empleados
import pandas as pd
from django.shortcuts import render
from .models import Empleado

def importar_empleados(request):
    if request.method == "POST" and request.FILES["file"]:
        excel_file = request.FILES["file"]

        # Leer el archivo Excel con pandas
        df = pd.read_excel(excel_file)

        # 🔥 Borrar todos los registros previos
        Empleado.objects.all().delete()

        # Cargar los nuevos registros
        for _, row in df.iterrows():
            Empleado.objects.create(
                id=row["ID"],
                preferred_name=row["Preferred Name"],
                sbd_email=row["SBD Email"]
            )

        return redirect("lista_empleados")

    return render(request, "empleados/importar.html")


# Listar empleados (vista básica)
def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, "empleados/lista.html", {"empleados": empleados})

