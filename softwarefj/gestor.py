# =============================================================================
# gestor.py
# GestorSistema: almacena y administra clientes, servicios y reservas en memoria.
# No usa base de datos; toda la información vive en listas de objetos Python.
# =============================================================================

from cliente import Cliente            # Entidad cliente.
from servicios import Servicio         # Clase abstracta de servicio.
from reserva import Reserva            # Entidad reserva.
from logger import Logger              # Sistema de logs.
from excepciones import (
    ClienteNoEncontradoError,          # Cliente inexistente.
    ServicioNoDisponibleError,         # Servicio no encontrado o deshabilitado.
    ReservaInvalidaError,              # Operación de reserva inválida.
    SistemaFJError,                    # Excepción base del sistema.
)


class GestorSistema:
    """
    Clase central que actúa como repositorio y orquestador del sistema.

    Responsabilidades:
        - Registrar y buscar clientes.
        - Registrar y buscar servicios.
        - Crear, confirmar, cancelar y procesar reservas.
        - Delegar el registro de errores al Logger.

    Toda la información se guarda en listas de Python (sin base de datos).
    """

    def __init__(self):
        # Lista interna de objetos Cliente registrados.
        self._clientes: list[Cliente] = []

        # Lista interna de objetos Servicio registrados.
        self._servicios: list[Servicio] = []

        # Lista interna de objetos Reserva creados.
        self._reservas: list[Reserva] = []

        # Instancia única del logger (Singleton).
        self._log = Logger()

        self._log.info("GestorSistema inicializado. Sistema SOFTRESERVE listo.")

    # =========================================================================
    # Gestión de Clientes
    # =========================================================================

    def registrar_cliente(self, nombre: str, correo: str, telefono: str) -> Cliente:
        """
        Crea y registra un nuevo cliente.

        Parámetros:
            nombre, correo, telefono -- datos del cliente.

        Retorna el objeto Cliente creado.
        Lanza ClienteInvalidoError si los datos son inválidos.
        """
        try:
            # La clase Cliente valida internamente; si falla, lanza excepción.
            cliente = Cliente(nombre, correo, telefono)

        except SistemaFJError as e:
            # Registramos el error y re-lanzamos para que el llamador lo maneje.
            self._log.error(f"Fallo al registrar cliente '{nombre}'", e)
            raise

        else:
            # Solo agregamos a la lista si no hubo excepción.
            self._clientes.append(cliente)
            self._log.info(
                f"Cliente registrado: {cliente.nombre} "
                f"[{cliente.id_corto()}] | {cliente.correo}"
            )
            return cliente

    def buscar_cliente_por_id(self, id_cliente: str) -> Cliente:
        """
        Busca un cliente por su ID completo o corto (primeros 8 chars).

        Lanza ClienteNoEncontradoError si no se encuentra.
        """
        for cliente in self._clientes:
            # Comparamos tanto el ID completo como el ID corto.
            if cliente.id == id_cliente or cliente.id_corto() == id_cliente.upper():
                return cliente

        raise ClienteNoEncontradoError(id_cliente)

    def listar_clientes(self) -> list[Cliente]:
        """Devuelve una copia de la lista de clientes registrados."""
        return list(self._clientes)

    # =========================================================================
    # Gestión de Servicios
    # =========================================================================

    def registrar_servicio(self, servicio: Servicio) -> Servicio:
        """
        Registra un objeto Servicio previamente construido.

        Parámetros:
            servicio -- instancia de una subclase concreta de Servicio.

        Retorna el mismo objeto si fue registrado correctamente.
        """
        try:
            # Verificamos que sea una instancia válida de Servicio.
            if not isinstance(servicio, Servicio):
                raise ReservaInvalidaError(
                    "el argumento no es una instancia de Servicio"
                )

            # Llamamos a validar() para chequeo interno del objeto.
            servicio.validar()

        except SistemaFJError as e:
            self._log.error(f"Fallo al registrar servicio", e)
            raise

        else:
            self._servicios.append(servicio)
            self._log.info(
                f"Servicio registrado: '{servicio.nombre}' "
                f"[{servicio.id_corto()}] | Base: ${servicio.precio_base:,.0f}"
            )
            return servicio

    def buscar_servicio_por_nombre(self, nombre: str) -> Servicio:
        """
        Busca un servicio por nombre (insensible a mayúsculas).

        Lanza ServicioNoDisponibleError si no se encuentra.
        """
        nombre_lower = nombre.lower().strip()
        for servicio in self._servicios:
            if servicio.nombre.lower() == nombre_lower:
                return servicio

        raise ServicioNoDisponibleError(nombre, "no está registrado en el sistema")

    def listar_servicios(self) -> list[Servicio]:
        """Devuelve una copia de la lista de servicios registrados."""
        return list(self._servicios)

    # =========================================================================
    # Gestión de Reservas
    # =========================================================================

    def crear_reserva(
        self,
        cliente: Cliente,
        servicio: Servicio,
        duracion: float,
        **kwargs,
    ) -> Reserva:
        """
        Crea una nueva reserva en estado PENDIENTE.

        Parámetros:
            cliente  -- objeto Cliente existente y activo.
            servicio -- objeto Servicio existente y disponible.
            duracion -- horas o días según el servicio.
            **kwargs -- parámetros opcionales para el cálculo de costo.

        Retorna el objeto Reserva creado.
        """
        try:
            reserva = Reserva(cliente, servicio, duracion, **kwargs)

        except SistemaFJError as e:
            self._log.error(
                f"No se pudo crear reserva para '{getattr(cliente, 'nombre', '?')}'",
                e,
            )
            raise

        else:
            self._reservas.append(reserva)
            self._log.info(
                f"Reserva creada [{reserva.id_corto()}] | "
                f"Cliente: {cliente.nombre} | Servicio: {servicio.nombre} | "
                f"Estado: PENDIENTE"
            )
            return reserva

    def confirmar_reserva(self, reserva: Reserva) -> float:
        """
        Confirma una reserva existente y retorna el costo calculado.

        Lanza cualquier excepción que surja durante la validación del servicio.
        """
        try:
            costo = reserva.confirmar()

        except SistemaFJError as e:
            self._log.error(
                f"No se pudo confirmar reserva [{reserva.id_corto()}]", e
            )
            raise

        return costo

    def cancelar_reserva(self, reserva: Reserva, motivo: str = "") -> None:
        """
        Cancela una reserva registrando el motivo.
        """
        try:
            reserva.cancelar(motivo or "Cancelado desde el gestor")

        except SistemaFJError as e:
            self._log.error(
                f"No se pudo cancelar reserva [{reserva.id_corto()}]", e
            )
            raise

    def procesar_reserva(self, reserva: Reserva) -> None:
        """
        Marca la reserva como procesada (servicio prestado).
        """
        try:
            reserva.procesar()

        except SistemaFJError as e:
            self._log.error(
                f"No se pudo procesar reserva [{reserva.id_corto()}]", e
            )
            raise

    def listar_reservas(self) -> list[Reserva]:
        """Devuelve una copia de todas las reservas del sistema."""
        return list(self._reservas)

    # =========================================================================
    # Reportes
    # =========================================================================

    def reporte_general(self) -> str:
        """
        Genera un resumen estadístico del sistema en texto plano.
        """
        total_clientes = len(self._clientes)
        clientes_activos = sum(1 for c in self._clientes if c.activo)

        total_servicios = len(self._servicios)
        servicios_disponibles = sum(1 for s in self._servicios if s.disponible)

        total_reservas = len(self._reservas)
        # Contamos reservas por estado.
        por_estado = {}
        ingresos_confirmados = 0.0
        for r in self._reservas:
            por_estado[r.estado] = por_estado.get(r.estado, 0) + 1
            if r.estado in ("CONFIRMADA", "PROCESADA"):
                ingresos_confirmados += r.costo

        lineas = [
            "=" * 55,
            "   REPORTE GENERAL — SOFTWARE FJ",
            "=" * 55,
            f"  Clientes registrados : {total_clientes} ({clientes_activos} activos)",
            f"  Servicios registrados: {total_servicios} ({servicios_disponibles} disponibles)",
            f"  Reservas totales     : {total_reservas}",
        ]
        for estado, cantidad in por_estado.items():
            lineas.append(f"    · {estado:12s}: {cantidad}")
        lineas.append(
            f"  Ingresos confirmados : ${ingresos_confirmados:,.2f} COP"
        )
        lineas.append("=" * 55)
        return "\n".join(lineas)
