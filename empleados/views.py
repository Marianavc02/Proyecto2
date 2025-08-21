from django.shortcuts import render
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Empleado

# Subir archivo Excel e importar empleados
def importar_empleados(request):
    if request.method == "POST" and request.FILES.get("file"):
        excel_file = request.FILES["file"]
        df = pd.read_excel(excel_file)  # Lee el Excel con pandas

        for _, row in df.iterrows():
            Empleado.objects.update_or_create(
                id=row["ID"],
                defaults={
                    "preferred_name": row["Preferred Name"],
                    "sbd_email": row["SBD Email"]
                }
            )
        return redirect("lista_empleados")

    return render(request, "empleados/importar.html")



# Listar empleados (vista básica)
def lista_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, "empleados/lista.html", {"empleados": empleados})

