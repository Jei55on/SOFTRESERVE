# =============================================================================
# entidad_base.py
# Define la clase abstracta raíz del sistema SOFTRESERVE.
# Toda entidad del dominio (Cliente, Servicio, Reserva) debe heredar de aquí.
# =============================================================================

from abc import ABC, abstractmethod  # ABC = Abstract Base Class; abstractmethod marca métodos obligatorios.
import uuid                           # Generador de identificadores únicos universales.
import datetime                       # Para registrar cuándo fue creada cada entidad.


class EntidadBase(ABC):
    """
    Clase abstracta que representa cualquier entidad persistente del sistema.

    Provee:
    - Un identificador único (UUID4) generado automáticamente.
    - La fecha/hora de creación.
    - Métodos abstractos que TODAS las subclases deben implementar:
        * describir()  → resumen legible de la entidad.
        * validar()    → verifica que los datos propios son coherentes.
    - Método concreto __str__ basado en describir().
    """

    def __init__(self):
        # Generamos un ID único para esta entidad al momento de su creación.
        # uuid.uuid4() produce un identificador aleatorio de 128 bits.
        self._id: str = str(uuid.uuid4())

        # Registramos la fecha y hora exacta en que fue instanciada la entidad.
        self._fecha_creacion: datetime.datetime = datetime.datetime.now()

    # -------------------------------------------------------------------------
    # Propiedades de solo lectura (encapsulación: no se pueden modificar desde
    # fuera de la clase una vez creadas).
    # -------------------------------------------------------------------------

    @property
    def id(self) -> str:
        """Identificador único inmutable de la entidad."""
        return self._id

    @property
    def fecha_creacion(self) -> datetime.datetime:
        """Fecha y hora en que la entidad fue instanciada."""
        return self._fecha_creacion

    # -------------------------------------------------------------------------
    # Métodos abstractos — cada subclase DEBE implementarlos.
    # -------------------------------------------------------------------------

    @abstractmethod
    def describir(self) -> str:
        """
        Devuelve una cadena legible con los datos principales de la entidad.
        Se usa en __str__ y en reportes del sistema.
        """
        pass  # No hay implementación aquí; la subclase la provee.

    @abstractmethod
    def validar(self) -> bool:
        """
        Verifica la coherencia interna de los datos de la entidad.
        Devuelve True si todo está en orden; de lo contrario debe lanzar
        la excepción personalizada correspondiente.
        """
        pass  # Implementado en cada subclase.

    # -------------------------------------------------------------------------
    # Método concreto compartido por todas las subclases.
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        """
        Representación en cadena de la entidad.
        Delegamos en describir() para que cada subclase controle el formato.
        """
        return self.describir()

    def id_corto(self) -> str:
        """
        Devuelve solo los primeros 8 caracteres del UUID para mostrarlo en
        mensajes de usuario sin saturar la pantalla.
        Ejemplo: 'a3f1c2d4' en lugar de 'a3f1c2d4-...-...-...'
        """
        return self._id[:8].upper()
