# =============================================================================
# reserva.py
# Define la clase Reserva que integra Cliente + Servicio + duración + estado.
# Implementa confirmación, cancelación y procesamiento con manejo de excepciones.
# =============================================================================

import datetime                         # Para registrar fechas de confirmación y cancelación.
from entidad_base import EntidadBase    # Clase abstracta raíz.
from cliente import Cliente             # Entidad cliente.
from servicios import Servicio          # Clase abstracta de servicio.
from excepciones import (
    ReservaInvalidaError,               # Reserva que viola reglas de negocio.
    ReservaCanceladaError,              # Intento de operar sobre reserva cancelada.
    ReservaYaConfirmadaError,           # Reserva ya confirmada previamente.
    DuracionInvalidaError,              # Duración fuera del rango del servicio.
    CalculoCostoError,                  # Error al calcular el costo.
)


# =============================================================================
# Enumeración de estados de una reserva
# =============================================================================

class EstadoReserva:
    """
    Clase de constantes que define los posibles estados de una reserva.
    No usamos enum del módulo estándar para mantener simplicidad de cuarto semestre.
    """
    PENDIENTE   = "PENDIENTE"    # Creada pero no confirmada.
    CONFIRMADA  = "CONFIRMADA"   # Confirmada y lista para ejecutarse.
    CANCELADA   = "CANCELADA"    # Anulada; no puede volver a activarse.
    PROCESADA   = "PROCESADA"    # El servicio ya fue prestado.


# =============================================================================
# Clase Reserva
# =============================================================================

class Reserva(EntidadBase):
    """
    Representa una reserva de un servicio por parte de un cliente.

    Ciclo de vida:
        PENDIENTE → (confirmar()) → CONFIRMADA → (procesar()) → PROCESADA
        PENDIENTE/CONFIRMADA → (cancelar()) → CANCELADA

    Atributos:
        _cliente    -- objeto Cliente que realiza la reserva.
        _servicio   -- objeto Servicio reservado.
        _duracion   -- unidad de tiempo (horas o días según el servicio).
        _estado     -- estado actual (ver EstadoReserva).
        _costo      -- costo calculado al confirmar la reserva.
        _kwargs     -- parámetros opcionales pasados al cálculo de costo.
    """

    def __init__(
        self,
        cliente: Cliente,
        servicio: Servicio,
        duracion: float,
        **kwargs,
    ):
        """
        Crea una reserva en estado PENDIENTE.

        Parámetros:
            cliente  -- instancia de Cliente (debe estar activo).
            servicio -- instancia de un Servicio (debe estar disponible).
            duracion -- horas o días, según el tipo de servicio.
            **kwargs -- parámetros opcionales para el cálculo de costo
                        (descuento, participantes, unidades, con_iva, etc.).

        Lanza:
            ReservaInvalidaError si cliente o servicio son inválidos.
        """
        super().__init__()  # Genera ID y fecha_creacion.

        # ── Validaciones de entrada ──────────────────────────────────────────

        # El cliente debe ser una instancia válida.
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("el parámetro 'cliente' no es un objeto Cliente")

        # El cliente debe estar activo para poder reservar.
        if not cliente.activo:
            raise ReservaInvalidaError(
                f"el cliente '{cliente.nombre}' está deshabilitado y no puede reservar"
            )

        # El servicio debe ser una instancia de Servicio (o subclase).
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("el parámetro 'servicio' no es un objeto Servicio válido")

        # La duración debe ser un número positivo.
        if not isinstance(duracion, (int, float)) or duracion <= 0:
            raise DuracionInvalidaError(duracion, 0, float("inf"))

        # ── Asignación de atributos ──────────────────────────────────────────
        self._cliente: Cliente = cliente
        self._servicio: Servicio = servicio
        self._duracion: float = float(duracion)
        self._kwargs: dict = kwargs              # Guardamos parámetros opcionales.
        self._estado: str = EstadoReserva.PENDIENTE
        self._costo: float = 0.0                 # Se calcula al confirmar.
        self._fecha_confirmacion: datetime.datetime = None
        self._fecha_cancelacion: datetime.datetime = None
        self._motivo_cancelacion: str = ""

        # Registramos la reserva en el historial del cliente.
        self._cliente.agregar_reserva(self._id)

    # -------------------------------------------------------------------------
    # Propiedades de solo lectura
    # -------------------------------------------------------------------------

    @property
    def cliente(self) -> Cliente:
        return self._cliente

    @property
    def servicio(self) -> Servicio:
        return self._servicio

    @property
    def duracion(self) -> float:
        return self._duracion

    @property
    def estado(self) -> str:
        return self._estado

    @property
    def costo(self) -> float:
        """Costo total confirmado. Es 0 mientras la reserva está PENDIENTE."""
        return self._costo

    @property
    def fecha_confirmacion(self):
        return self._fecha_confirmacion

    # -------------------------------------------------------------------------
    # Operaciones principales
    # -------------------------------------------------------------------------

    def confirmar(self) -> float:
        """
        Confirma la reserva: valida parámetros del servicio y calcula el costo.

        Flujo de excepciones:
            try      → valida disponibilidad del servicio y parámetros.
            except   → captura errores de validación y los re-lanza.
            else     → si no hubo error, guarda el costo y cambia estado.
            finally  → siempre registra el intento de confirmación en el log.

        Retorna el costo total calculado.
        Lanza:
            ReservaCanceladaError    si la reserva ya fue cancelada.
            ReservaYaConfirmadaError si ya estaba confirmada.
            Cualquier excepción de validación del servicio.
        """
        # Importamos el logger aquí para no crear dependencia circular.
        from logger import Logger
        log = Logger()

        # No se puede confirmar una reserva cancelada.
        if self._estado == EstadoReserva.CANCELADA:
            raise ReservaCanceladaError(self.id_corto())

        # No se confirma dos veces.
        if self._estado == EstadoReserva.CONFIRMADA:
            raise ReservaYaConfirmadaError(self.id_corto())

        costo_calculado = 0.0  # Variable temporal usada en el finally.

        try:
            # Validamos los parámetros específicos del servicio antes de calcular.
            self._servicio.validar_parametros(self._duracion, **self._kwargs)

            # Calculamos el costo final llamando al método polimórfico del servicio.
            costo_calculado = self._servicio.calcular_costo(
                self._duracion, **self._kwargs
            )

            # Verificación extra: el costo no debe ser negativo.
            if costo_calculado < 0:
                raise CalculoCostoError(f"resultado negativo: {costo_calculado}")

        except (CalculoCostoError, Exception) as e:
            # Re-lanzamos para que el llamador pueda manejar el error.
            log.error(
                f"Error al confirmar reserva {self.id_corto()} "
                f"(Servicio: {self._servicio.nombre})",
                e,
            )
            raise  # Propagamos la excepción original intacta.

        else:
            # Este bloque SOLO se ejecuta si no hubo ninguna excepción.
            self._costo = costo_calculado
            self._estado = EstadoReserva.CONFIRMADA
            self._fecha_confirmacion = datetime.datetime.now()

            log.info(
                f"Reserva {self.id_corto()} CONFIRMADA | "
                f"Cliente: {self._cliente.nombre} | "
                f"Servicio: {self._servicio.nombre} | "
                f"Costo: ${self._costo:,.2f}"
            )

        finally:
            # Este bloque siempre se ejecuta, haya error o no.
            # Lo usamos para dejar constancia del intento.
            log.info(
                f"Intento de confirmación procesado — Reserva {self.id_corto()} "
                f"→ Estado final: {self._estado}"
            )

        return self._costo

    def cancelar(self, motivo: str = "Sin motivo especificado") -> None:
        """
        Cancela la reserva registrando el motivo.

        Lanza:
            ReservaCanceladaError si ya estaba cancelada.
            ReservaInvalidaError  si ya fue procesada (no se puede cancelar).
        """
        from logger import Logger
        log = Logger()

        if self._estado == EstadoReserva.CANCELADA:
            raise ReservaCanceladaError(self.id_corto())

        if self._estado == EstadoReserva.PROCESADA:
            raise ReservaInvalidaError(
                f"la reserva {self.id_corto()} ya fue procesada y no puede cancelarse"
            )

        try:
            # Cambiamos el estado y registramos la fecha y motivo.
            self._estado = EstadoReserva.CANCELADA
            self._fecha_cancelacion = datetime.datetime.now()
            self._motivo_cancelacion = motivo

        except Exception as e:
            # Ante cualquier error inesperado, encadenamos con contexto.
            raise ReservaInvalidaError(
                f"fallo inesperado al cancelar reserva {self.id_corto()}"
            ) from e  # 'from e' = encadenamiento de excepciones.

        else:
            log.info(
                f"Reserva {self.id_corto()} CANCELADA | "
                f"Motivo: {motivo} | "
                f"Cliente: {self._cliente.nombre}"
            )

    def procesar(self) -> None:
        """
        Marca la reserva como procesada (el servicio fue prestado).
        Solo puede procesarse una reserva CONFIRMADA.

        Lanza:
            ReservaInvalidaError si la reserva no está confirmada.
        """
        from logger import Logger
        log = Logger()

        if self._estado != EstadoReserva.CONFIRMADA:
            raise ReservaInvalidaError(
                f"solo se puede procesar una reserva confirmada. "
                f"Estado actual: {self._estado}"
            )

        self._estado = EstadoReserva.PROCESADA
        log.info(
            f"Reserva {self.id_corto()} PROCESADA | "
            f"Servicio prestado: {self._servicio.nombre} | "
            f"Cliente: {self._cliente.nombre}"
        )

    # -------------------------------------------------------------------------
    # Métodos abstractos implementados
    # -------------------------------------------------------------------------

    def describir(self) -> str:
        """Resumen legible de la reserva."""
        costo_str = f"${self._costo:,.2f}" if self._costo else "Por calcular"
        return (
            f"Reserva [{self.id_corto()}] | "
            f"Cliente: {self._cliente.nombre} | "
            f"Servicio: {self._servicio.nombre} | "
            f"Duración: {self._duracion} u.t. | "
            f"Costo: {costo_str} | "
            f"Estado: {self._estado}"
        )

    def validar(self) -> bool:
        """Verifica que los objetos internos sean coherentes."""
        if self._cliente is None or self._servicio is None:
            raise ReservaInvalidaError("cliente y servicio son obligatorios")
        if self._duracion <= 0:
            raise ReservaInvalidaError("la duración debe ser positiva")
        return True

    def resumen_completo(self) -> str:
        """Devuelve un reporte detallado de la reserva para impresión."""
        lineas = [
            "─" * 55,
            f"  RESERVA: {self._id}",
            f"  Estado : {self._estado}",
            f"  Creada : {self._fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')}",
        ]
        if self._fecha_confirmacion:
            lineas.append(
                f"  Confirm: {self._fecha_confirmacion.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        if self._fecha_cancelacion:
            lineas.append(
                f"  Cancelada: {self._fecha_cancelacion.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            lineas.append(f"  Motivo : {self._motivo_cancelacion}")
        lineas += [
            "  ── Cliente ──",
            f"  {self._cliente.describir()}",
            "  ── Servicio ──",
            f"  {self._servicio.describir()}",
            f"  Duración  : {self._duracion} unidades de tiempo",
            f"  Costo total: ${self._costo:,.2f} COP",
            "─" * 55,
        ]
        return "\n".join(lineas)
