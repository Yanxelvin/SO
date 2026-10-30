import threading
import queue
import time
import random

NUM_DOCUMENTOS = 24
NUM_TRABAJADORES = 4
FACTOR_TIEMPO = 0.1          

trabajos = queue.Queue()     
resultados = {}              
registro = []                
lock = threading.Lock()      

# Cargar 24 documentos en la cola (id, tamaño simulado entre 1 y 5)
documentos = [(doc_id, random.randint(1, 5)) for doc_id in range(1, NUM_DOCUMENTOS + 1)]
for doc in documentos:
    trabajos.put(doc)

def trabajador(nombre):
    while True:
        try:
            doc_id, tamano = trabajos.get_nowait()
        except queue.Empty:
            break

        time.sleep(tamano * FACTOR_TIEMPO)

        with lock:
            resultados[nombre]["documentos"] += 1
            resultados[nombre]["tamano_total"] += tamano
            registro.append((doc_id, tamano, nombre))
            print(f"  [{nombre}] procesó DOC-{doc_id:02d} (tamaño {tamano})")

        trabajos.task_done()


def procesar_secuencial(lista_documentos):
    inicio = time.perf_counter()
    for _doc_id, tamano in lista_documentos:
        time.sleep(tamano * FACTOR_TIEMPO)
    return time.perf_counter() - inicio


def main():
    print(f" Clasificación concurrente: {NUM_DOCUMENTOS} documentos, {NUM_TRABAJADORES} trabajadores")
    print(" Documentos cargados (id:tamaño):")
    for i in range(0, NUM_DOCUMENTOS, 8):
        fila = "  ".join(f"{d:02d}:{t}" for d, t in documentos[i:i + 8])
        print(f"  {fila}")
    print("-" * 62)

    hilos = []
    for i in range(1, NUM_TRABAJADORES + 1):
        nombre = f"Trabajador-{i}"
        resultados[nombre] = {"documentos": 0, "tamano_total": 0}
        hilos.append(threading.Thread(target=trabajador, args=(nombre,), name=nombre))

    inicio = time.perf_counter()
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    tiempo_concurrente = time.perf_counter() - inicio

    total = sum(r["documentos"] for r in resultados.values())
    print("-" * 62)
    print(f" TOTAL PROCESADO: {total} de {NUM_DOCUMENTOS} documentos")
    print("-" * 62)
    print(" RESUMEN")
    print(f"  {'Trabajador':<14}{'Docs':>5}{'Tamaño':>8}   Documentos asignados")
    for nombre in sorted(resultados):
        ids = sorted(d for d, _t, w in registro if w == nombre)
        lista = ", ".join(f"{d:02d}" for d in ids)
        r = resultados[nombre]
        print(f"  {nombre:<14}{r['documentos']:>5}{r['tamano_total']:>8}   {lista}")

    ids_registrados = [d for d, _t, _w in registro]
    v1 = total == NUM_DOCUMENTOS
    v2 = (len(ids_registrados) == len(set(ids_registrados))
          and sorted(ids_registrados) == list(range(1, NUM_DOCUMENTOS + 1)))
    v3 = not any(h.is_alive() for h in hilos)
    print("-" * 62)
    print(" VERIFICACIONES")
    print(f"  [{'OK' if v1 else 'FALLO'}] 1. La suma por trabajador es {total} (esperado)")
    print(f"  [{'OK' if v2 else 'FALLO'}] 2. Cada ID aparece una sola vez en el registro detallado")
    print(f"  [{'OK' if v3 else 'FALLO'}] 3. Los {NUM_TRABAJADORES} hilos finalizaron sin quedarse bloqueados")

    tiempo_secuencial = procesar_secuencial(documentos)
    tamano_total = sum(t for _d, t in documentos)
    print("-" * 62)
    etiqueta_hilos = f"Versión con {NUM_TRABAJADORES} hilos"
    print(f"  {'Tamaño total de los documentos':<31}: {tamano_total}  (≈ {tamano_total * FACTOR_TIEMPO:.1f} s de trabajo)")
    print(f"  {etiqueta_hilos:<31}: {tiempo_concurrente:.2f} s")
    print(f"  {'Versión secuencial (1 hilo)':<31}: {tiempo_secuencial:.2f} s")
    print(f"  {'Aceleración':<31}: {tiempo_secuencial / tiempo_concurrente:.2f}x")


if __name__ == "__main__":
    main()
