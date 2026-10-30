Nombre: Ian Andres Yujra Condori
## 4. Respuestas a las preguntas

### ¿Por qué `queue.Queue` es apropiada para compartir trabajos?

Porque es una cola thread-safe: tiene su propio candado interno, así que put() y get() / get_nowait() son operaciones atómicas. Si dos hilos piden un documento al mismo tiempo, la cola garantiza que cada elemento se entrega a un solo hilo, por lo que ningún documento se procesa dos veces ni se pierde, sin que tengamos que sincronizar nada a mano. Además implementa el patrón productor–consumidor (FIFO), permite repartir el trabajo dinámicamente y con get_nowait() + queue.Empty da una forma limpia de saber cuándo ya no queda trabajo.

### ¿Qué protege `Lock` y qué pasaría si se actualizara el resumen sin él?

El lock protege la sección crítica donde se modifican los datos compartidos: el diccionario resultados`(contador de documentos y tamaño total de cada trabajador), la lista registro y la impresión en consola.

Una instrucción como resultados[nombre]["documentos"] += 1 no es atómica: internamente es leer el valor → sumar 1 → escribir el valor. Sin el lock, el sistema operativo puede cambiar de hilo entre esos pasos y se produce una condición de carrera: dos hilos leen el mismo valor viejo y uno de los incrementos se pierde. El resultado serían conteos incorrectos (por ejemplo, un total de 23 en lugar de 24) que aparecen de forma aleatoria y son difíciles de reproducir, además de líneas de salida mezcladas. Con with lock: solo un hilo a la vez entra a esa sección, y el lock se libera automáticamente aunque ocurra una excepción.

### ¿Qué cambiarías si cada documento tuviera que guardarse en un archivo real?

- Reemplazaría time.sleep() por la escritura real con with open(...). Cada documento se guardaría en *su propio archivo con nombre único (por ejemplo salida/DOC-07.txt`), así los hilos no escriben sobre el mismo archivo y no hace falta lock para la escritura.
- Si todos tuvieran que escribir en un archivo común(un log o un índice), protegería esa escritura con un lock, o mejor, usaría un hilo escritor dedicado que lea de una segunda cola, para que un solo hilo toque el archivo.
- Agregaría manejo de errores (try/except/finally): si falla la escritura (disco lleno, permisos), registrar el error o reintentar, y llamar a task_done() en el finally para no dejar la cola inconsistente. Solo contaría el documento como procesado si se guardó bien.
- Para evitar archivos a medias, escribiría primero en un archivo temporal y luego lo renombraría (os.replace), que es una operación atómica.
- Los hilos son buena opción aquí porque escribir en disco es E/S y Python libera el GIL mientras espera al disco; si el trabajo fuera de cálculo pesado usaría multiprocessing.

## 5. Reto adicional

### ¿Por qué la diferencia puede ser pequeña en este ejemplo artificial?

- El trabajo es simulado con time.sleep(). Mientras un hilo "duerme" no usa CPU y Python libera el GIL, por eso aquí sí se ven ~3.5x. Pero si el trabajo fuera cálculo real en CPU (clasificar texto, por ejemplo), en CPython el GIL solo deja que un hilo ejecute código Python a la vez y la versión con 4 hilos tardaría casi lo mismo que la secuencial (o un poco más, por el costo de crear y cambiar entre hilos).
- Son pocos documentos y muy cortos: en total se ahorran unos 5 segundos. El costo de crear hilos, adquirir el lock y hacer cambios de contexto pesa proporcionalmente más cuando las tareas son tan pequeñas.
- Nunca se llega a 4x exacto por el desbalance del final: el tiempo total lo marca el último trabajador en terminar. Si al final a uno le toca un documento de tamaño 5, los otros tres ya están ociosos esperándolo (en la ejecución 2 lo ideal era 8.3 / 4 ≈ 2.08 s y se obtuvo 2.20 s).


