# =============================================================================
# excepciones.py
# Módulo de excepciones personalizadas para el sistema SOFTRESERVE.
# Define todas las clases de error propias del dominio del negocio.
# =============================================================================

class SistemaFJError(Exception):
    """
    Excepción base de la que heredan todas las excepciones del sistema.
    Al centralizar la jerarquía aquí, es posible capturar cualquier error
    propio del sistema con un solo except SistemaFJError.
    """

    def __init__(self, mensaje: str, codigo: int = 0):
        # Llamamos al constructor padre para que el mensaje quede registrado
        # en args[0], comportamiento estándar de Exception.
        super().__init__(mensaje)

        # Código numérico opcional para clasificar el error en el log.
        self.codigo = codigo

        # Guardamos el mensaje para acceso directo sin usar str(e).
        self.mensaje = mensaje

    def __str__(self) -> str:
        # Representación legible: incluye código si fue proporcionado.
        if self.codigo:
            return f"[Código {self.codigo}] {self.mensaje}"
        return self.mensaje


# ---------------------------------------------------------------------------
# Errores relacionados con la entidad Cliente
# ---------------------------------------------------------------------------

class ClienteInvalidoError(SistemaFJError):
    """
    Se lanza cuando los datos de un cliente no superan las validaciones.
    Ejemplos: nombre vacío, correo sin '@', teléfono con letras.
    """

    def __init__(self, campo: str, valor, razon: str = ""):
        # Construimos un mensaje descriptivo indicando qué campo falló.
        mensaje = f"Dato inválido en el campo '{campo}' (valor recibido: '{valor}')"
        if razon:
            # Si se especificó la razón, la añadimos para mayor claridad.
            mensaje += f". Razón: {razon}"
        super().__init__(mensaje, codigo=1001)

        # Guardamos el campo y valor originales para posible inspección externa.
        self.campo = campo
        self.valor = valor


class ClienteNoEncontradoError(SistemaFJError):
    """
    Se lanza cuando se busca un cliente por ID y no existe en el sistema.
    """

    def __init__(self, id_cliente: str):
        mensaje = f"No se encontró ningún cliente con ID '{id_cliente}'."
        super().__init__(mensaje, codigo=1002)
        self.id_cliente = id_cliente


# ---------------------------------------------------------------------------
# Errores relacionados con la entidad Servicio
# ---------------------------------------------------------------------------

class ServicioNoDisponibleError(SistemaFJError):
    """
    Se lanza cuando un servicio existe pero no puede ser reservado,
    por ejemplo porque está deshabilitado o sin stock disponible.
    """

    def __init__(self, nombre_servicio: str, motivo: str = ""):
        mensaje = f"El servicio '{nombre_servicio}' no está disponible."
        if motivo:
            mensaje += f" Motivo: {motivo}"
        super().__init__(mensaje, codigo=2001)
        self.nombre_servicio = nombre_servicio


class ParametroServicioError(SistemaFJError):
    """
    Se lanza cuando los parámetros de configuración de un servicio son
    inválidos (por ejemplo, precio negativo o capacidad cero).
    """

    def __init__(self, parametro: str, valor, razon: str = ""):
        mensaje = f"Parámetro inválido '{parametro}' = '{valor}'"
        if razon:
            mensaje += f". Razón: {razon}"
        super().__init__(mensaje, codigo=2002)
        self.parametro = parametro
        self.valor = valor


class CapacidadExcedidaError(SistemaFJError):
    """
    Se lanza cuando se intenta registrar más participantes de los que
    permite la capacidad máxima del servicio.
    """

    def __init__(self, servicio: str, solicitados: int, maximos: int):
        mensaje = (
            f"El servicio '{servicio}' permite máximo {maximos} participante(s), "
            f"pero se solicitaron {solicitados}."
        )
        super().__init__(mensaje, codigo=2003)
        self.servicio = servicio
        self.solicitados = solicitados
        self.maximos = maximos


# ---------------------------------------------------------------------------
# Errores relacionados con la entidad Reserva
# ---------------------------------------------------------------------------

class ReservaInvalidaError(SistemaFJError):
    """
    Error genérico para operaciones de reserva que no cumplen las reglas
    de negocio (p. ej., reservar sin cliente asignado).
    """

    def __init__(self, detalle: str):
        super().__init__(f"Reserva inválida: {detalle}", codigo=3001)


class DuracionInvalidaError(SistemaFJError):
    """
    Se lanza cuando la duración solicitada está fuera del rango permitido
    por el servicio (mínimo o máximo de horas/días).
    """

    def __init__(self, duracion: float, minimo: float, maximo: float):
        mensaje = (
            f"Duración {duracion}h fuera del rango permitido "
            f"[{minimo}h – {maximo}h]."
        )
        super().__init__(mensaje, codigo=3002)
        self.duracion = duracion
        self.minimo = minimo
        self.maximo = maximo


class ReservaCanceladaError(SistemaFJError):
    """
    Se lanza cuando se intenta operar sobre una reserva que ya fue cancelada.
    """

    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' ya fue cancelada y no puede modificarse.",
            codigo=3003,
        )
        self.id_reserva = id_reserva


class ReservaYaConfirmadaError(SistemaFJError):
    """
    Se lanza cuando se intenta confirmar una reserva que ya está confirmada.
    """

    def __init__(self, id_reserva: str):
        super().__init__(
            f"La reserva '{id_reserva}' ya estaba confirmada previamente.",
            codigo=3004,
        )
        self.id_reserva = id_reserva


# ---------------------------------------------------------------------------
# Errores de cálculo
# ---------------------------------------------------------------------------

class CalculoCostoError(SistemaFJError):
    """
    Se lanza cuando el cálculo de costo produce un resultado inconsistente,
    como un valor negativo o infinito.
    """

    def __init__(self, detalle: str):
        super().__init__(f"Error en cálculo de costo: {detalle}", codigo=4001)
