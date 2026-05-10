# =============================================================================
# servicios.py
# Define la clase abstracta Servicio y los tres servicios especializados:
#   1. ReservaSala       — reserva de salas de reuniones/conferencias.
#   2. AlquilerEquipo    — alquiler de equipos tecnológicos.
#   3. AsesoriaEspecializada — sesiones de asesoría con profesionales.
# =============================================================================

from abc import abstractmethod          # Para declarar métodos abstractos.
from entidad_base import EntidadBase    # Clase raíz del sistema.
from excepciones import (
    ParametroServicioError,             # Parámetros de configuración inválidos.
    ServicioNoDisponibleError,          # Servicio deshabilitado o sin stock.
    CapacidadExcedidaError,             # Participantes exceden el límite.
    CalculoCostoError,                  # Resultado de costo inconsistente.
)


# =============================================================================
# Clase abstracta Servicio
# =============================================================================

class Servicio(EntidadBase):
    """
    Clase abstracta que representa cualquier servicio ofrecido por SOFTRESERVE.

    Define la interfaz que todos los servicios deben cumplir:
        - calcular_costo(duracion, ...)    → retorna el precio según duración.
        - describir_servicio()              → texto explicativo del servicio.
        - validar_parametros(duracion, ...) → verifica que la solicitud sea válida.
        - validar()                         → comprobación interna (heredado).
        - describir()                       → resumen del objeto (heredado).

    También provee:
        - precio_base por hora/unidad como atributo configurable.
        - estado de disponibilidad (disponible / no disponible).
        - impuesto del 19 % (IVA Colombia) aplicable en calcular_costo.
    """

    # IVA estándar aplicable a todos los servicios (19 % en Colombia).
    IVA = 0.19

    def __init__(self, nombre: str, descripcion: str, precio_base: float):
        """
        Parámetros:
            nombre       -- nombre comercial del servicio.
            descripcion  -- texto breve que explica qué incluye el servicio.
            precio_base  -- precio por unidad de tiempo (COP, sin IVA).

        Lanza:
            ParametroServicioError si precio_base no es positivo.
        """
        super().__init__()  # Genera ID y fecha de creación.

        # Validamos el precio antes de asignarlo.
        if not isinstance(precio_base, (int, float)) or precio_base <= 0:
            raise ParametroServicioError(
                "precio_base", precio_base, "debe ser un número positivo"
            )

        # Nombre no puede estar vacío.
        if not nombre or not nombre.strip():
            raise ParametroServicioError("nombre", nombre, "no puede estar vacío")

        self._nombre: str = nombre.strip()
        self._descripcion: str = descripcion.strip() if descripcion else ""
        self._precio_base: float = float(precio_base)

        # Por defecto, el servicio está disponible al crearlo.
        self._disponible: bool = True

    # -------------------------------------------------------------------------
    # Propiedades
    # -------------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @property
    def precio_base(self) -> float:
        return self._precio_base

    @property
    def disponible(self) -> bool:
        return self._disponible

    # -------------------------------------------------------------------------
    # Métodos de gestión de disponibilidad
    # -------------------------------------------------------------------------

    def deshabilitar(self) -> None:
        """Marca el servicio como no disponible para nuevas reservas."""
        self._disponible = False

    def habilitar(self) -> None:
        """Reactiva el servicio."""
        self._disponible = True

    def verificar_disponibilidad(self) -> None:
        """
        Lanza ServicioNoDisponibleError si el servicio está deshabilitado.
        Se invoca al inicio de calcular_costo y validar_parametros.
        """
        if not self._disponible:
            raise ServicioNoDisponibleError(
                self._nombre, "el servicio ha sido deshabilitado por el administrador"
            )

    # -------------------------------------------------------------------------
    # Método concreto de cálculo de IVA (compartido por subclases)
    # -------------------------------------------------------------------------

    def _aplicar_iva(self, subtotal: float) -> float:
        """
        Aplica el IVA al subtotal y retorna el total con impuesto.
        Se usa como utilidad interna en las subclases.
        """
        return subtotal * (1 + self.IVA)

    def _aplicar_descuento(self, total: float, descuento_pct: float) -> float:
        """
        Aplica un porcentaje de descuento sobre el total.
        Parámetros:
            total         -- monto antes del descuento.
            descuento_pct -- porcentaje (0.0 a 100.0).
        """
        if not (0.0 <= descuento_pct <= 100.0):
            raise CalculoCostoError(
                f"descuento {descuento_pct}% fuera del rango válido [0, 100]"
            )
        # Convertimos porcentaje a fracción (ej: 10 → 0.10).
        return total * (1 - descuento_pct / 100.0)

    # -------------------------------------------------------------------------
    # Métodos abstractos — cada servicio especializado los implementa
    # -------------------------------------------------------------------------

    @abstractmethod
    def calcular_costo(self, duracion: float, **kwargs) -> float:
        """
        Calcula el costo total del servicio para la duración indicada.
        Los kwargs permiten parámetros opcionales (descuento, participantes, etc.).
        """
        pass

    @abstractmethod
    def describir_servicio(self) -> str:
        """Texto completo del servicio: qué incluye, condiciones, tarifas."""
        pass

    @abstractmethod
    def validar_parametros(self, duracion: float, **kwargs) -> bool:
        """
        Verifica que la duración y los parámetros opcionales sean válidos
        para este servicio. Lanza excepción si algo no cumple las reglas.
        """
        pass

    # -------------------------------------------------------------------------
    # Métodos concretos heredados de EntidadBase
    # -------------------------------------------------------------------------

    def describir(self) -> str:
        """Resumen corto del servicio para listados."""
        estado = "Disponible" if self._disponible else "No disponible"
        return (
            f"Servicio [{self.id_corto()}] '{self._nombre}' | "
            f"Base: ${self._precio_base:,.0f}/h | {estado}"
        )

    def validar(self) -> bool:
        """Verificación de integridad básica del servicio."""
        if self._precio_base <= 0:
            raise ParametroServicioError(
                "precio_base", self._precio_base, "debe ser positivo"
            )
        return True


# =============================================================================
# Servicio 1: Reserva de Sala
# =============================================================================

class ReservaSala(Servicio):
    """
    Servicio de reserva de salas de reuniones o conferencias.

    Parámetros propios:
        capacidad_maxima -- número máximo de personas admitidas en la sala.
        equipada         -- True si la sala incluye proyector y videoconferencia.

    Reglas de negocio:
        - Duración mínima: 1 hora. Máxima: 8 horas por reserva.
        - Si la sala está equipada, se cobra un recargo del 20 %.
        - Descuento opcional (porcentaje) puede pasarse como kwarg 'descuento'.
        - Si se indica 'participantes', se valida contra capacidad_maxima.
    """

    # Duración mínima y máxima permitida en horas.
    DURACION_MIN = 1.0
    DURACION_MAX = 8.0

    # Recargo por sala equipada (proyector + videoconferencia).
    RECARGO_EQUIPADA = 0.20

    def __init__(
        self,
        nombre: str,
        precio_base: float,
        capacidad_maxima: int,
        equipada: bool = False,
    ):
        """
        Parámetros:
            nombre           -- identificador de la sala (p. ej. 'Sala A').
            precio_base      -- tarifa por hora en COP, sin IVA.
            capacidad_maxima -- máximo de personas que caben.
            equipada         -- True si tiene proyector y videoconferencia.
        """
        super().__init__(
            nombre,
            f"Sala de reuniones con capacidad para {capacidad_maxima} personas.",
            precio_base,
        )

        # Validamos que la capacidad sea un entero positivo.
        if not isinstance(capacidad_maxima, int) or capacidad_maxima < 1:
            raise ParametroServicioError(
                "capacidad_maxima",
                capacidad_maxima,
                "debe ser un entero mayor o igual a 1",
            )

        self._capacidad_maxima: int = capacidad_maxima
        self._equipada: bool = bool(equipada)

    @property
    def capacidad_maxima(self) -> int:
        return self._capacidad_maxima

    @property
    def equipada(self) -> bool:
        return self._equipada

    # -------------------------------------------------------------------------
    # Implementación de métodos abstractos
    # -------------------------------------------------------------------------

    def calcular_costo(self, duracion: float, **kwargs) -> float:
        """
        Calcula el costo total de la reserva de sala.

        Parámetros posicionales:
            duracion -- horas de uso.

        Parámetros opcionales (kwargs):
            descuento    -- porcentaje de descuento sobre el total (0-100).
            participantes -- número de asistentes (para validar capacidad).
            con_iva      -- True/False (por defecto True).

        Retorna el costo en pesos colombianos.
        """
        # Antes de calcular, verificamos que el servicio esté disponible.
        self.verificar_disponibilidad()

        # Validamos duración y parámetros opcionales.
        self.validar_parametros(duracion, **kwargs)

        # Costo base = precio por hora × horas.
        subtotal = self._precio_base * duracion

        # Si la sala está equipada, aplicamos el recargo del 20 %.
        if self._equipada:
            subtotal *= (1 + self.RECARGO_EQUIPADA)

        # Aplicamos IVA si no se indica lo contrario.
        con_iva = kwargs.get("con_iva", True)  # Por defecto incluye IVA.
        if con_iva:
            subtotal = self._aplicar_iva(subtotal)

        # Aplicamos descuento si se proporcionó.
        descuento = kwargs.get("descuento", 0.0)
        if descuento:
            subtotal = self._aplicar_descuento(subtotal, descuento)

        # Verificación de integridad: el costo no puede ser negativo.
        if subtotal < 0:
            raise CalculoCostoError(f"costo calculado negativo: {subtotal}")

        return round(subtotal, 2)  # Redondeamos a 2 decimales.

    def describir_servicio(self) -> str:
        """Descripción detallada de la sala."""
        equipamiento = "Proyector + videoconferencia incluidos" if self._equipada else "Sin equipamiento AV"
        return (
            f"=== {self._nombre} ===\n"
            f"  Capacidad: {self._capacidad_maxima} personas\n"
            f"  Equipamiento: {equipamiento}\n"
            f"  Tarifa base: ${self._precio_base:,.0f}/hora (+ IVA 19%)\n"
            f"  Recargo equipada: {int(self.RECARGO_EQUIPADA * 100)}%\n"
            f"  Duración permitida: {self.DURACION_MIN}h – {self.DURACION_MAX}h"
        )

    def validar_parametros(self, duracion: float, **kwargs) -> bool:
        """
        Valida duración y número de participantes.
        Lanza DuracionInvalidaError o CapacidadExcedidaError según el caso.
        """
        from excepciones import DuracionInvalidaError  # Import local para evitar ciclo.

        # Verificamos que la duración esté en el rango permitido.
        if not isinstance(duracion, (int, float)) or duracion < self.DURACION_MIN or duracion > self.DURACION_MAX:
            raise DuracionInvalidaError(duracion, self.DURACION_MIN, self.DURACION_MAX)

        # Si se indicaron participantes, verificamos contra la capacidad.
        participantes = kwargs.get("participantes", 1)
        if participantes > self._capacidad_maxima:
            raise CapacidadExcedidaError(
                self._nombre, participantes, self._capacidad_maxima
            )

        return True


# =============================================================================
# Servicio 2: Alquiler de Equipo
# =============================================================================

class AlquilerEquipo(Servicio):
    """
    Servicio de alquiler de equipos tecnológicos (portátiles, tabletas, etc.).

    Parámetros propios:
        tipo_equipo   -- nombre del equipo (p. ej. 'Portátil HP ProBook').
        unidades_disp -- cantidad de unidades disponibles para alquiler.

    Reglas de negocio:
        - La duración se expresa en DÍAS (mínimo 1, máximo 30).
        - Se pueden alquilar múltiples unidades a la vez ('unidades' kwarg).
        - Descuento por volumen automático:
            * 3-5 unidades → 5 % de descuento.
            * 6+ unidades  → 10 % de descuento.
        - Descuento adicional manual opcional ('descuento' kwarg).
        - IVA opcional ('con_iva', por defecto True).
    """

    DURACION_MIN = 1    # días mínimos
    DURACION_MAX = 30   # días máximos

    def __init__(
        self,
        nombre: str,
        tipo_equipo: str,
        precio_base: float,
        unidades_disp: int,
    ):
        super().__init__(
            nombre,
            f"Alquiler de {tipo_equipo}.",
            precio_base,
        )

        if not tipo_equipo or not tipo_equipo.strip():
            raise ParametroServicioError("tipo_equipo", tipo_equipo, "no puede estar vacío")

        if not isinstance(unidades_disp, int) or unidades_disp < 0:
            raise ParametroServicioError(
                "unidades_disp", unidades_disp, "debe ser un entero no negativo"
            )

        self._tipo_equipo: str = tipo_equipo.strip()
        self._unidades_disp: int = unidades_disp

    @property
    def tipo_equipo(self) -> str:
        return self._tipo_equipo

    @property
    def unidades_disponibles(self) -> int:
        return self._unidades_disp

    def _descuento_volumen(self, unidades: int) -> float:
        """
        Calcula el porcentaje de descuento automático según volumen.
        Retorna: 0, 5 o 10 (porcentaje).
        """
        if unidades >= 6:
            return 10.0   # 10 % para 6 o más unidades.
        elif unidades >= 3:
            return 5.0    # 5 % para 3 a 5 unidades.
        return 0.0         # Sin descuento para 1 o 2 unidades.

    def calcular_costo(self, duracion: float, **kwargs) -> float:
        """
        Calcula el costo de alquiler.

        Parámetros:
            duracion -- días de alquiler.

        kwargs:
            unidades  -- número de unidades a alquilar (default 1).
            descuento -- porcentaje adicional de descuento (default 0).
            con_iva   -- incluir IVA (default True).
        """
        self.verificar_disponibilidad()
        self.validar_parametros(duracion, **kwargs)

        unidades = kwargs.get("unidades", 1)

        # Costo base = precio/día × días × unidades.
        subtotal = self._precio_base * duracion * unidades

        # Aplicamos descuento por volumen automático.
        desc_volumen = self._descuento_volumen(unidades)
        if desc_volumen > 0:
            subtotal = self._aplicar_descuento(subtotal, desc_volumen)

        # Aplicamos descuento manual adicional si existe.
        descuento_extra = kwargs.get("descuento", 0.0)
        if descuento_extra:
            subtotal = self._aplicar_descuento(subtotal, descuento_extra)

        # IVA por defecto.
        if kwargs.get("con_iva", True):
            subtotal = self._aplicar_iva(subtotal)

        if subtotal < 0:
            raise CalculoCostoError(f"costo negativo calculado: {subtotal}")

        return round(subtotal, 2)

    def describir_servicio(self) -> str:
        return (
            f"=== {self._nombre} ===\n"
            f"  Equipo: {self._tipo_equipo}\n"
            f"  Unidades disponibles: {self._unidades_disp}\n"
            f"  Tarifa base: ${self._precio_base:,.0f}/día (+ IVA 19%)\n"
            f"  Descuento volumen: 3-5 uds → 5% | 6+ uds → 10%\n"
            f"  Duración permitida: {self.DURACION_MIN} – {self.DURACION_MAX} días"
        )

    def validar_parametros(self, duracion: float, **kwargs) -> bool:
        from excepciones import DuracionInvalidaError

        if not isinstance(duracion, (int, float)) or duracion < self.DURACION_MIN or duracion > self.DURACION_MAX:
            raise DuracionInvalidaError(duracion, self.DURACION_MIN, self.DURACION_MAX)

        unidades = kwargs.get("unidades", 1)

        # Las unidades deben ser un entero positivo.
        if not isinstance(unidades, int) or unidades < 1:
            raise ParametroServicioError("unidades", unidades, "debe ser un entero mayor a 0")

        # No se pueden pedir más unidades de las disponibles.
        if unidades > self._unidades_disp:
            raise CapacidadExcedidaError(
                self._nombre, unidades, self._unidades_disp
            )

        return True


# =============================================================================
# Servicio 3: Asesoría Especializada
# =============================================================================

class AsesoriaEspecializada(Servicio):
    """
    Servicio de asesoría o consultoría con un profesional especializado.

    Parámetros propios:
        especialidad    -- área de la asesoría (ej. 'Diseño de software').
        nivel           -- 'junior', 'senior' o 'experto' (afecta el precio).
        sesiones_max    -- máximo de sesiones que se pueden reservar a la vez.

    Reglas de negocio:
        - La duración se expresa en HORAS (mínimo 0.5h, máximo 4h por sesión).
        - El precio varía según nivel:
            * junior  → precio_base × 1.0
            * senior  → precio_base × 1.5
            * experto → precio_base × 2.0
        - Parámetro 'sesiones' kwarg: número de sesiones a reservar.
        - Descuento opcional ('descuento' kwarg).
        - IVA opcional ('con_iva', default True).
    """

    DURACION_MIN = 0.5   # media hora mínima
    DURACION_MAX = 4.0   # 4 horas máximo por sesión

    # Multiplicadores de precio por nivel.
    MULTIPLICADORES = {
        "junior": 1.0,
        "senior": 1.5,
        "experto": 2.0,
    }

    def __init__(
        self,
        nombre: str,
        especialidad: str,
        precio_base: float,
        nivel: str = "senior",
        sesiones_max: int = 10,
    ):
        super().__init__(
            nombre,
            f"Asesoría en {especialidad} — nivel {nivel}.",
            precio_base,
        )

        nivel = nivel.lower().strip()
        if nivel not in self.MULTIPLICADORES:
            raise ParametroServicioError(
                "nivel", nivel, f"debe ser uno de: {list(self.MULTIPLICADORES.keys())}"
            )

        if not isinstance(sesiones_max, int) or sesiones_max < 1:
            raise ParametroServicioError(
                "sesiones_max", sesiones_max, "debe ser un entero positivo"
            )

        self._especialidad: str = especialidad.strip()
        self._nivel: str = nivel
        self._sesiones_max: int = sesiones_max

    @property
    def especialidad(self) -> str:
        return self._especialidad

    @property
    def nivel(self) -> str:
        return self._nivel

    def calcular_costo(self, duracion: float, **kwargs) -> float:
        """
        Calcula el costo de la asesoría.

        Parámetros:
            duracion -- horas por sesión.

        kwargs:
            sesiones  -- número de sesiones (default 1).
            descuento -- porcentaje de descuento (default 0).
            con_iva   -- incluir IVA (default True).
        """
        self.verificar_disponibilidad()
        self.validar_parametros(duracion, **kwargs)

        sesiones = kwargs.get("sesiones", 1)

        # Obtenemos el multiplicador según el nivel del asesor.
        multiplicador = self.MULTIPLICADORES[self._nivel]

        # Costo = precio_base × multiplicador_nivel × horas × sesiones.
        subtotal = self._precio_base * multiplicador * duracion * sesiones

        # Descuento opcional.
        descuento = kwargs.get("descuento", 0.0)
        if descuento:
            subtotal = self._aplicar_descuento(subtotal, descuento)

        # IVA.
        if kwargs.get("con_iva", True):
            subtotal = self._aplicar_iva(subtotal)

        if subtotal < 0:
            raise CalculoCostoError(f"costo negativo: {subtotal}")

        return round(subtotal, 2)

    def describir_servicio(self) -> str:
        mult = self.MULTIPLICADORES[self._nivel]
        return (
            f"=== {self._nombre} ===\n"
            f"  Especialidad: {self._especialidad}\n"
            f"  Nivel asesor: {self._nivel.capitalize()} (×{mult} sobre tarifa base)\n"
            f"  Tarifa base: ${self._precio_base:,.0f}/hora (+ IVA 19%)\n"
            f"  Sesiones máximas por reserva: {self._sesiones_max}\n"
            f"  Duración por sesión: {self.DURACION_MIN}h – {self.DURACION_MAX}h"
        )

    def validar_parametros(self, duracion: float, **kwargs) -> bool:
        from excepciones import DuracionInvalidaError

        if (
            not isinstance(duracion, (int, float))
            or duracion < self.DURACION_MIN
            or duracion > self.DURACION_MAX
        ):
            raise DuracionInvalidaError(duracion, self.DURACION_MIN, self.DURACION_MAX)

        sesiones = kwargs.get("sesiones", 1)
        if not isinstance(sesiones, int) or sesiones < 1:
            raise ParametroServicioError("sesiones", sesiones, "debe ser un entero positivo")

        if sesiones > self._sesiones_max:
            raise CapacidadExcedidaError(
                self._nombre, sesiones, self._sesiones_max
            )

        return True
