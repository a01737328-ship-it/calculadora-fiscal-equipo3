import pandas as pd
import math
from datetime import datetime

# Función para truncar a n decimales
def truncar(numero, decimales):
    factor = 10**decimales
    return math.trunc(numero * factor) / factor

# 1. CARGA DE MATRICES
try:
    m1_udi = pd.read_excel('matriz 1.xlsx', skiprows=17)
    m2_inpc = pd.read_excel('matriz 2.xlsx', skiprows=1)
    m3_isr = pd.read_excel('matriz 3.xlsx', skiprows=11)
    
    m3_isr = m3_isr.dropna(subset=[m3_isr.columns[7]])

    m1_udi.columns = [str(c).strip() for c in m1_udi.columns]
    m2_inpc.columns = [str(c).strip() for c in m2_inpc.columns]
    m2_inpc.rename(columns={m2_inpc.columns[0]: 'ANIO'}, inplace=True)

    print("✅ Matrices cargadas y listas.")
except Exception as e:
    print(f"❌ Error al cargar archivos: {e}")

# --- PRIMER FASE: SOLICITUD DE DATOS ---
print("\n--- Sistema de Cálculo de ISR por Enajenación ---")
vp = float(input("Ingrese el precio de venta (vp): "))
vadq = float(input("Ingrese el valor de adquisición original: "))
pc = float(input("Porcentaje de construcción (ej. 0.80): "))
pt = float(input("Porcentaje de terreno (ej. 0.20): "))

fa_str = input("Fecha de adquisición (AAAA-MM-DD): ")
fe_str = input("Fecha de enajenación (AAAA-MM-DD): ")

gn = float(input("Monto de gastos notariales: "))
fgn_str = input("Fecha de pago de gastos notariales (AAAA-MM-DD): ")

cv = float(input("Monto de comisiones de venta: "))
fcv_str = input("Fecha de pago de comisiones (AAAA-MM-DD): ")

# Conversión de fechas y cálculo inmediato de años (at)
fa = datetime.strptime(fa_str, "%Y-%m-%d")
fe = datetime.strptime(fe_str, "%Y-%m-%d")
fgn = datetime.strptime(fgn_str, "%Y-%m-%d")
fcv = datetime.strptime(fcv_str, "%Y-%m-%d")

at = fe.year - fa.year
if at < 1: at = 1

# --- SEGUNDA FASE: EXENCIÓN CON REGLA DE 3 AÑOS ---
print("\n--- Verificación de Requisitos de Exención ---")
enajeno_reciente = input("¿El contribuyente ha exentado otra casa en los últimos 3 años? (S/N): ").upper()

# CORRECCIÓN: Si enajenó antes O si los años transcurridos son menos de 3, NO HAY EXENCIÓN
if enajeno_reciente == 'S' or at < 3:
    vealex = 0
    exed = vp
    if at < 3:
        print("⚠️ Nota: Al tener solo", at, "años transcurridos, no cumple el periodo mínimo para la exención.")
    else:
        print("⚠️ Nota: Exención negada por venta previa en el periodo de 3 años.")
else:
    m1_udi['Fecha'] = m1_udi['Fecha'].astype(str).str.strip()
    busqueda_udi = m1_udi[m1_udi['Fecha'] == fe_str]
    
    if busqueda_udi.empty:
        print(f"⚠️ Error: No se encontró UDI para {fe_str}")
        exit()
        
    udicor = float(busqueda_udi['SP68257'].values[0])
    vealex = truncar(udicor * 700000, 2)
    exed = vp - vealex
    print(f"✅ Exención de 700,000 UDIs aplicada: ${vealex:,.2f}")

# --- TERCER FASE / MICRO PROCESO ---
if exed <= 0:
    print(f"\n--- INFORME DE EXENCIÓN ---")
    print(f"Venta exenta de ISR. Valor exención: ${vealex:,.2f}")
else:
    # --- MICRO PROCESO 3: CÁLCULO DE GANANCIA ---
    propex = truncar(exed / vp, 4)
    
    # Costo de Construcción Disminuido
    vc = vadq * pc
    vt = vadq * pt
    vdc = vc * (1 - (0.03 * at))
    if vdc < (vc * 0.20): vdc = vc * 0.20
    
    # INPC Actualización
    mes_ant = fe.month - 1 if fe.month > 1 else 12
    año_ant = fe.year if fe.month > 1 else fe.year - 1
    
    inpcad = float(m2_inpc[m2_inpc['ANIO'].astype(float).astype(int) == fa.year][str(fa.month)].values[0])
    inpcde = float(m2_inpc[m2_inpc['ANIO'].astype(float).astype(int) == año_ant][str(mes_ant)].values[0])
    
    fact = truncar(inpcde / inpcad, 4)
    ccact = vdc * fact
    ctact = vt * fact
    
    # Gastos y Comisiones
    if fgn.year != fe.year:
        inpcgn = float(m2_inpc[m2_inpc['ANIO'].astype(float).astype(int) == fgn.year][str(fgn.month)].values[0])
        gnact = gn * truncar(inpcde / inpcgn, 4)
    else:
        gnact = gn

    if fcv.year != fe.year:
        inpccv = float(m2_inpc[m2_inpc['ANIO'].astype(float).astype(int) == fcv.year][str(fcv.month)].values[0])
        cvact = cv * truncar(inpcde / inpccv, 4)
    else:
        cvact = cv
        
    # Fase 5: Ganancia por enajenación (Proporcional)
    ganej = exed - ((ccact + ctact) * propex) - (gnact * propex) - (cvact * propex)
    
    # --- FASE 6: MACRO PROCESO 2 (ISR) ---
    if ganej > 0:
        gananacu = ganej / at
        if at > 20: divisor_at = 20
        else: divisor_at = at
        
        # Filtrado Matriz 3
        tabla_año = m3_isr[m3_isr.iloc[:, 7].astype(float).astype(int) == fe.year].copy()
        l_inf = pd.to_numeric(tabla_año.iloc[:, 8], errors='coerce')
        l_sup = pd.to_numeric(tabla_año.iloc[:, 9], errors='coerce').fillna(999999999.99)
        
        fila = tabla_año[(gananacu >= l_inf) & (gananacu <= l_sup)].iloc[0]
        
        # Cálculos de Impuesto
        isracu = ((gananacu - float(fila.iloc[8])) * float(fila.iloc[11])) + float(fila.iloc[10])
        tasafectiva = (isracu / gananacu)
        
        ganannoacu = ganej - gananacu
        isrnoacu = ganannoacu * tasafectiva
        isrtotal = isracu + isrnoacu

        print(f"\n--- INFORME DE RESULTADOS FISCALES ---")
        print(f"Ganancia por enajenación (ganej): ${ganej:,.2f}")
        print(f"Ganancia acumulable: ${gananacu:,.2f}")
        print(f"Ganancia no acumulable: ${ganannoacu:,.2f}")
        print(f"ISR sobre ganancia acumulable (ISRACU): ${isracu:,.2f}")
        print(f"ISR sobre ganancia no acumulable (ISRNOACU): ${isrnoacu:,.2f}")
        print(f"TOTAL DE ISR A PAGAR (ISRTOTAL): ${isrtotal:,.2f}")
        print(f"Monto excedente de la venta: ${exed:,.2f}")
        
    else:
        print(f"\n--- INFORME DE RESULTADO ---")
        print(f"Hubo una PÉRDIDA de ${abs(ganej):,.2f}. No genera pago de ISR.")	