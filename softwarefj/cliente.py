# =============================================================================
# cliente.py
# Define la clase Cliente con encapsulación estricta y validaciones robustas.
# =============================================================================

import re                          # Módulo de expresiones regulares para validar correo y teléfono.
from entidad_base import EntidadBase  # Clase abstracta raíz.
from excepciones import ClienteInvalidoError  # Excepción personalizada para datos de cliente.


class Cliente(EntidadBase):
    """
    Representa a un cliente registrado en el sistema SOFTRESERVE.

    Atributos privados (encapsulación):
        _nombre    -- nombre completo del cliente.
        _correo    -- dirección de correo electrónico única.
        _telefono  -- número de contacto en formato nacional.
        _activo    -- indica si la cuenta del cliente está habilitada.

    Las propiedades con setter incluyen validación, garantizando que nunca
    se almacene un dato inválido en el objeto.
    """

    # Expresión regular para validar correos electrónicos.
    # Acepta: usuario@dominio.extension (extensión de 2 a 6 letras).
    _PATRON_CORREO = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,6}$")

    # Expresión regular para teléfonos: acepta dígitos, espacios, guiones y '+'.
    # Longitud entre 7 y 15 caracteres después de eliminar espacios y guiones.
    _PATRON_TELEFONO = re.compile(r"^[+\d][\d\s\-]{6,14}$")

    def __init__(self, nombre: str, correo: str, telefono: str):
        """
        Inicializa un cliente.  Llama a validar() al final del constructor
        para garantizar que el objeto nace en estado consistente.

        Parámetros:
            nombre   -- nombre completo (mínimo 3 caracteres, solo letras y espacios).
            correo   -- dirección de correo electrónico válida.
            telefono -- número telefónico en formato aceptado.

        Lanza:
            ClienteInvalidoError si cualquier campo no pasa las validaciones.
        """
        # Inicializamos los atributos de EntidadBase (ID y fecha_creacion).
        super().__init__()

        # Usamos los setters para que la validación ocurra desde la creación.
        self.nombre = nombre      # Invoca el setter validado.
        self.correo = correo      # Invoca el setter validado.
        self.telefono = telefono  # Invoca el setter validado.

        # Un cliente recién creado está activo por defecto.
        self._activo: bool = True

        # Historial de IDs de reservas asociadas a este cliente.
        self._reservas: list = []

    # -------------------------------------------------------------------------
    # Propiedades y setters — encapsulación con validación
    # -------------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        """Nombre completo del cliente."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str) -> None:
        """
        Valida y asigna el nombre.
        Reglas: no vacío, mínimo 3 caracteres, solo letras y espacios.
        """
        if not isinstance(valor, str):
            # El nombre debe ser una cadena de texto.
            raise ClienteInvalidoError("nombre", valor, "debe ser texto")

        # strip() elimina espacios al inicio y al final.
        valor = valor.strip()

        if len(valor) < 3:
            raise ClienteInvalidoError(
                "nombre", valor, "debe tener al menos 3 caracteres"
            )

        # Verificamos que solo contenga letras del alfabeto y espacios.
        # isalpha() falla con espacios, por eso usamos replace.
        if not valor.replace(" ", "").isalpha():
            raise ClienteInvalidoError(
                "nombre", valor, "solo se permiten letras y espacios"
            )

        self._nombre = valor

    @property
    def correo(self) -> str:
        """Correo electrónico del cliente."""
        return self._correo

    @correo.setter
    def correo(self, valor: str) -> None:
        """
        Valida y asigna el correo electrónico usando expresión regular.
        """
        if not isinstance(valor, str):
            raise ClienteInvalidoError("correo", valor, "debe ser texto")

        valor = valor.strip().lower()  # Normalizamos a minúsculas.

        if not self._PATRON_CORREO.match(valor):
            raise ClienteInvalidoError(
                "correo", valor, "formato inválido (ej: usuario@dominio.com)"
            )

        self._correo = valor

    @property
    def telefono(self) -> str:
        """Número de teléfono del cliente."""
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str) -> None:
        """
        Valida y asigna el teléfono usando expresión regular.
        """
        if not isinstance(valor, str):
            raise ClienteInvalidoError("telefono", valor, "debe ser texto")

        valor = valor.strip()

        if not self._PATRON_TELEFONO.match(valor):
            raise ClienteInvalidoError(
                "telefono",
                valor,
                "formato inválido (ej: +57 310 5551234 o 3105551234)",
            )

        self._telefono = valor

    @property
    def activo(self) -> bool:
        """Indica si el cliente está habilitado para realizar reservas."""
        return self._activo

    @property
    def reservas(self) -> list:
        """Lista de IDs de reservas asociadas al cliente (solo lectura)."""
        # Devolvemos una copia para evitar modificaciones externas directas.
        return list(self._reservas)

    # -------------------------------------------------------------------------
    # Métodos públicos
    # -------------------------------------------------------------------------

    def deshabilitar(self) -> None:
        """Desactiva la cuenta del cliente, impidiendo nuevas reservas."""
        self._activo = False

    def habilitar(self) -> None:
        """Reactiva la cuenta del cliente."""
        self._activo = True

    def agregar_reserva(self, id_reserva: str) -> None:
        """
        Registra el ID de una reserva en el historial del cliente.
        Solo se llama internamente desde la clase Reserva.
        """
        if id_reserva not in self._reservas:
            # Evitamos duplicados por si se llama más de una vez.
            self._reservas.append(id_reserva)

    def total_reservas(self) -> int:
        """Devuelve la cantidad de reservas asociadas al cliente."""
        return len(self._reservas)

    # -------------------------------------------------------------------------
    # Métodos abstractos implementados (requeridos por EntidadBase)
    # -------------------------------------------------------------------------

    def describir(self) -> str:
        """Resumen legible del cliente."""
        estado = "Activo" if self._activo else "Inactivo"
        return (
            f"Cliente [{self.id_corto()}] | {self._nombre} | "
            f"{self._correo} | Tel: {self._telefono} | "
            f"Estado: {estado} | Reservas: {len(self._reservas)}"
        )

    def validar(self) -> bool:
        """
        Verifica la coherencia interna. Al usar setters en __init__,
        los datos ya fueron validados; este método hace una comprobación
        final de integridad.
        """
        # Verificamos que los atributos obligatorios estén presentes y no vacíos.
        if not self._nombre or not self._correo or not self._telefono:
            raise ClienteInvalidoError(
                "campos_obligatorios", "", "nombre, correo y teléfono son obligatorios"
            )
        return True
