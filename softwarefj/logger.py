# =============================================================================
# logger.py
# Módulo de registro de eventos y errores del sistema SOFTRESERVE.
# Escribe en un archivo de texto plano con marca de tiempo.
# =============================================================================

import os          # Para obtener la ruta absoluta del archivo de log.
import datetime    # Para incluir la fecha y hora exacta en cada entrada.


class Logger:
    """
    Clase encargada de registrar eventos, errores y operaciones en un
    archivo de log persistente. Utiliza el patrón Singleton para que
    exista una única instancia durante toda la ejecución del programa.
    """

    # Atributo de clase que almacenará la instancia única (patrón Singleton).
    _instancia = None

    def __new__(cls, ruta_archivo: str = "softreserve.log"):
        """
        Sobrescribimos __new__ para implementar Singleton:
        si ya existe una instancia, la devolvemos; si no, la creamos.
        """
        if cls._instancia is None:
            # Primera llamada: creamos la instancia normalmente.
            cls._instancia = super().__new__(cls)
            # Guardamos la ruta del archivo en la instancia.
            cls._instancia._ruta = ruta_archivo
            # Indicamos que aún no se ha inicializado completamente.
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self, ruta_archivo: str = "softreserve.log"):
        """
        Inicializa el logger solo la primera vez (Singleton).
        Crea el archivo de log si no existe y escribe la cabecera.
        """
        if self._inicializado:
            # Si ya fue inicializado, no hacemos nada.
            return

        # Guardamos la ruta final del archivo de log.
        self._ruta = ruta_archivo

        # Abrimos en modo 'a' (append) para no borrar logs anteriores.
        # Si el archivo no existe, Python lo crea automáticamente.
        with open(self._ruta, "a", encoding="utf-8") as archivo:
            # Escribimos una línea de separación para distinguir ejecuciones.
            archivo.write("\n" + "=" * 70 + "\n")
            archivo.write(
                f"  SISTEMA SOFTRESERVE — Sesión iniciada: "
                f"{self._timestamp()}\n"
            )
            archivo.write("=" * 70 + "\n")

        # Marcamos como inicializado para no repetir la cabecera.
        self._inicializado = True

    # -------------------------------------------------------------------------
    # Métodos públicos de registro
    # -------------------------------------------------------------------------

    def info(self, mensaje: str) -> None:
        """
        Registra un evento informativo (operación exitosa, estado del sistema).
        """
        self._escribir("INFO", mensaje)

    def advertencia(self, mensaje: str) -> None:
        """
        Registra una advertencia: situación inusual que no detiene el sistema.
        """
        self._escribir("ADVERTENCIA", mensaje)

    def error(self, mensaje: str, excepcion: Exception = None) -> None:
        """
        Registra un error. Si se pasa la excepción, incluye su tipo y texto.
        Parámetros:
            mensaje   -- descripción humana del contexto del error.
            excepcion -- objeto de excepción capturado (opcional).
        """
        # Construimos el texto del error con tipo y mensaje de la excepción.
        detalle = mensaje
        if excepcion is not None:
            # type(excepcion).__name__ da el nombre de la clase de la excepción.
            detalle += f" | {type(excepcion).__name__}: {excepcion}"

            # Si la excepción tiene causa encadenada (__cause__), la registramos.
            if excepcion.__cause__ is not None:
                detalle += f" | Causa original: {excepcion.__cause__}"

        self._escribir("ERROR", detalle)

    def critico(self, mensaje: str, excepcion: Exception = None) -> None:
        """
        Registra un error crítico que pudo comprometer la estabilidad del
        sistema, incluyendo causa encadenada si la hay.
        """
        detalle = mensaje
        if excepcion is not None:
            detalle += f" | {type(excepcion).__name__}: {excepcion}"
        self._escribir("CRÍTICO", detalle)

    # -------------------------------------------------------------------------
    # Métodos privados
    # -------------------------------------------------------------------------

    def _escribir(self, nivel: str, mensaje: str) -> None:
        """
        Escribe una línea formateada en el archivo de log.
        Formato: [TIMESTAMP] [NIVEL] mensaje
        """
        linea = f"[{self._timestamp()}] [{nivel:12s}] {mensaje}\n"
        try:
            # Abrimos en modo append para no perder entradas anteriores.
            with open(self._ruta, "a", encoding="utf-8") as archivo:
                archivo.write(linea)
        except OSError as e:
            # Si no podemos escribir el log, al menos lo mostramos en consola
            # para no perder la información silenciosamente.
            print(f"[LOGGER-FALLBACK] No se pudo escribir en log: {e}")
            print(linea, end="")

    @staticmethod
    def _timestamp() -> str:
        """
        Devuelve la fecha y hora actual como cadena con formato ISO-8601 corto.
        Ejemplo de salida: '2025-05-10 14:32:05'
        """
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def ruta_log(self) -> str:
        """Devuelve la ruta del archivo de log para inspección externa."""
        return os.path.abspath(self._ruta)
