# =============================================================================
# main.py
# Punto de entrada del sistema SOFTRESERVE.
# Simula 12 operaciones completas: registros válidos e inválidos de clientes,
# creación correcta e incorrecta de servicios, y reservas exitosas y fallidas.
# Demuestra: POO, polimorfismo, encapsulación, excepciones personalizadas,
# try/except, try/except/else, try/except/finally y encadenamiento de excepciones.
# =============================================================================

# Configuramos la salida estándar en UTF-8 para que los caracteres especiales
# se muestren correctamente en Windows (que por defecto usa cp1252).
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Importaciones del sistema ────────────────────────────────────────────────

from gestor import GestorSistema          # Orquestador central del sistema.
from servicios import (
    ReservaSala,                           # Servicio 1: salas de reunión.
    AlquilerEquipo,                        # Servicio 2: equipos tecnológicos.
    AsesoriaEspecializada,                 # Servicio 3: asesorías.
)
from logger import Logger                  # Singleton de registro de eventos.
from excepciones import (
    SistemaFJError,                        # Excepción base para captura genérica.
    ClienteInvalidoError,                  # Datos de cliente inválidos.
    ParametroServicioError,                # Configuración de servicio incorrecta.
    ServicioNoDisponibleError,             # Servicio deshabilitado.
    ReservaInvalidaError,                  # Reserva que viola reglas de negocio.
    DuracionInvalidaError,                 # Duración fuera del rango permitido.
    CapacidadExcedidaError,                # Participantes sobre el límite.
    ReservaCanceladaError,                 # Operar sobre reserva ya cancelada.
)


# =============================================================================
# Utilidades de presentación
# =============================================================================

def titulo(texto: str) -> None:
    """Imprime un encabezado decorativo para separar cada operación."""
    print(f"\n{'─' * 60}")
    print(f"  {texto}")
    print(f"{'─' * 60}")


def ok(mensaje: str) -> None:
    """Imprime un mensaje de éxito con prefijo visual."""
    print(f"  [OK]  {mensaje}")


def fallo(mensaje: str) -> None:
    """Imprime un mensaje de error controlado con prefijo visual."""
    print(f"  [ERR] {mensaje}")


# =============================================================================
# OPERACIONES DEL SISTEMA
# =============================================================================

def main():
    """
    Función principal. Ejecuta 12 operaciones que cubren:
      - Registro de clientes válidos e inválidos.
      - Creación de servicios válidos e inválidos.
      - Creación, confirmación, cancelación y procesamiento de reservas.
      - Manejo de cada tipo de excepción personalizada.
    """

    # Creamos la instancia del gestor (y del logger internamente).
    gestor = GestorSistema()
    log = Logger()  # Misma instancia Singleton ya creada por el gestor.

    print("\n" + "=" * 60)
    print("   SISTEMA SOFTRESERVE — SIMULACIÓN DE OPERACIONES")
    print("=" * 60)

    # =========================================================================
    # OPERACIÓN 1: Registro de clientes VÁLIDOS
    # =========================================================================
    titulo("OP 1 — Registro de clientes válidos")

    # Usamos try/except/else: si no hay error registramos; si hay error, informamos.
    clientes_validos = [
        ("Ana Torres",     "ana.torres@softreserve.com",  "3001234567"),
        ("Carlos Mendoza", "cmendoza@empresa.co",        "+57 310 9876543"),
        ("Laura Ríos",     "lrios@correo.com",           "6012223344"),
    ]

    clientes = []  # Lista local para guardar los objetos creados.

    for nombre, correo, tel in clientes_validos:
        try:
            cliente = gestor.registrar_cliente(nombre, correo, tel)
        except SistemaFJError as e:
            # No debería ocurrir con datos válidos, pero manejamos por robustez.
            fallo(f"Error inesperado al registrar '{nombre}': {e}")
        else:
            # Bloque else: se ejecuta SOLO si no hubo excepción.
            clientes.append(cliente)
            ok(f"Cliente registrado → {cliente.describir()}")

    # =========================================================================
    # OPERACIÓN 2: Registro de cliente con datos INVÁLIDOS
    # =========================================================================
    titulo("OP 2 — Intentos de registro con datos inválidos")

    datos_invalidos = [
        ("",           "sin.nombre@x.com",  "3001111111"),   # Nombre vacío.
        ("12Hacker99", "hack@x.com",        "3002222222"),   # Nombre con números.
        ("Pedro Ruiz", "correo-invalido",   "3003333333"),   # Correo sin '@'.
        ("Sofía Cruz", "sofia@x.com",       "abc-xyz"),      # Teléfono con letras.
    ]

    for nombre, correo, tel in datos_invalidos:
        try:
            gestor.registrar_cliente(nombre, correo, tel)
        except ClienteInvalidoError as e:
            # Capturamos específicamente errores de validación de cliente.
            fallo(f"ClienteInvalidoError capturada → {e}")
        except SistemaFJError as e:
            # Captura genérica de cualquier otro error del sistema.
            fallo(f"SistemaFJError → {e}")

    # =========================================================================
    # OPERACIÓN 3: Creación de servicios VÁLIDOS
    # =========================================================================
    titulo("OP 3 — Creación de servicios válidos")

    try:
        # ── Sala de reuniones ────────────────────────────────────────────────
        sala_a = ReservaSala(
            nombre="Sala A",
            precio_base=80_000,      # $80,000/hora COP sin IVA.
            capacidad_maxima=10,
            equipada=True,           # Incluye proyector y videoconferencia.
        )
        gestor.registrar_servicio(sala_a)
        ok(f"Servicio creado → {sala_a.describir()}")

        # ── Sala sin equipar (más económica) ─────────────────────────────────
        sala_b = ReservaSala(
            nombre="Sala B",
            precio_base=50_000,
            capacidad_maxima=6,
            equipada=False,
        )
        gestor.registrar_servicio(sala_b)
        ok(f"Servicio creado → {sala_b.describir()}")

        # ── Alquiler de portátil ──────────────────────────────────────────────
        portatil = AlquilerEquipo(
            nombre="Portátil HP ProBook",
            tipo_equipo="Portátil HP ProBook 450 G9",
            precio_base=35_000,      # $35,000/día.
            unidades_disp=5,
        )
        gestor.registrar_servicio(portatil)
        ok(f"Servicio creado → {portatil.describir()}")

        # ── Asesoría de software ──────────────────────────────────────────────
        asesoria_sw = AsesoriaEspecializada(
            nombre="Asesoría en Arquitectura de Software",
            especialidad="Diseño y Arquitectura de Software",
            precio_base=120_000,     # $120,000/hora base.
            nivel="senior",
            sesiones_max=5,
        )
        gestor.registrar_servicio(asesoria_sw)
        ok(f"Servicio creado → {asesoria_sw.describir()}")

    except SistemaFJError as e:
        fallo(f"Error al crear servicio: {e}")

    # =========================================================================
    # OPERACIÓN 4: Intento de crear un servicio con parámetros INVÁLIDOS
    # =========================================================================
    titulo("OP 4 — Creación de servicios inválidos (manejo de excepciones)")

    # Caso A: precio_base negativo.
    try:
        servicio_malo = ReservaSala("Sala Fantasma", -5000, 8)
        gestor.registrar_servicio(servicio_malo)
    except ParametroServicioError as e:
        fallo(f"ParametroServicioError → {e}")

    # Caso B: nivel de asesoría inexistente.
    try:
        asesoria_mala = AsesoriaEspecializada(
            "Asesoría X", "Testing", 80_000, nivel="dios"
        )
    except ParametroServicioError as e:
        fallo(f"ParametroServicioError → {e}")

    # Caso C: Alquiler con 0 unidades disponibles (inválido).
    try:
        equipo_malo = AlquilerEquipo("Tablet", "iPad Pro", 20_000, unidades_disp=-1)
    except ParametroServicioError as e:
        fallo(f"ParametroServicioError → {e}")

    # =========================================================================
    # OPERACIÓN 5: Reserva exitosa — Sala equipada con IVA
    # =========================================================================
    titulo("OP 5 — Reserva exitosa de sala equipada (3 horas, 8 personas)")

    # Usamos try/except/else/finally para demostrar las cuatro cláusulas.
    reserva_sala = None
    try:
        # Creamos la reserva en estado PENDIENTE.
        reserva_sala = gestor.crear_reserva(
            cliente=clientes[0],       # Ana Torres.
            servicio=sala_a,           # Sala A (equipada).
            duracion=3,                # 3 horas.
            participantes=8,           # Validado contra capacidad de la sala.
        )
        # Confirmamos: esto calcula el costo y cambia el estado.
        costo = gestor.confirmar_reserva(reserva_sala)

    except DuracionInvalidaError as e:
        fallo(f"Duración inválida → {e}")
    except CapacidadExcedidaError as e:
        fallo(f"Capacidad excedida → {e}")
    except SistemaFJError as e:
        fallo(f"Error del sistema → {e}")
    else:
        # Solo si no hubo error:
        ok(f"Reserva confirmada. Costo: ${costo:,.2f} COP")
        print(reserva_sala.resumen_completo())
    finally:
        # Siempre mostramos el estado final de la reserva.
        if reserva_sala:
            print(f"  [FINALLY] Estado de reserva: {reserva_sala.estado}")

    # =========================================================================
    # OPERACIÓN 6: Reserva exitosa — Alquiler de equipos con descuento por volumen
    # =========================================================================
    titulo("OP 6 — Alquiler de 4 portátiles por 5 días (descuento por volumen)")

    try:
        r_equipo = gestor.crear_reserva(
            cliente=clientes[1],       # Carlos Mendoza.
            servicio=portatil,
            duracion=5,                # 5 días.
            unidades=4,                # 4 portátiles → activa descuento 5%.
        )
        costo = gestor.confirmar_reserva(r_equipo)

    except SistemaFJError as e:
        fallo(f"Error → {e}")
    else:
        ok(f"Alquiler confirmado. Costo con descuento de volumen: ${costo:,.2f} COP")
        ok(r_equipo.describir())

    # =========================================================================
    # OPERACIÓN 7: Reserva exitosa — Asesoría con descuento manual
    # =========================================================================
    titulo("OP 7 — Asesoría senior 2h × 3 sesiones con 10% de descuento")

    try:
        r_asesoria = gestor.crear_reserva(
            cliente=clientes[2],       # Laura Ríos.
            servicio=asesoria_sw,
            duracion=2,                # 2 horas por sesión.
            sesiones=3,                # 3 sesiones.
            descuento=10.0,            # 10 % de descuento manual.
        )
        costo = gestor.confirmar_reserva(r_asesoria)

    except SistemaFJError as e:
        fallo(f"Error → {e}")
    else:
        ok(f"Asesoría confirmada. Costo final con descuento: ${costo:,.2f} COP")
        ok(r_asesoria.describir())

    # =========================================================================
    # OPERACIÓN 8: Intento de reserva con duración fuera de rango
    # =========================================================================
    titulo("OP 8 — Reserva inválida: sala por 12 horas (máximo es 8h)")

    try:
        r_invalida = gestor.crear_reserva(
            cliente=clientes[0],
            servicio=sala_a,
            duracion=12,               # La sala permite máximo 8h.
        )
        # La validación ocurre al confirmar, no al crear.
        gestor.confirmar_reserva(r_invalida)

    except DuracionInvalidaError as e:
        fallo(f"DuracionInvalidaError capturada correctamente → {e}")
    except SistemaFJError as e:
        fallo(f"SistemaFJError → {e}")

    # =========================================================================
    # OPERACIÓN 9: Intento de reserva que excede la capacidad
    # =========================================================================
    titulo("OP 9 — Reserva inválida: 15 personas en Sala B (máximo 6)")

    try:
        r_llena = gestor.crear_reserva(
            cliente=clientes[1],
            servicio=sala_b,
            duracion=2,
            participantes=15,          # Sala B tiene capacidad máxima de 6.
        )
        gestor.confirmar_reserva(r_llena)

    except CapacidadExcedidaError as e:
        fallo(f"CapacidadExcedidaError capturada → {e}")
    except SistemaFJError as e:
        fallo(f"SistemaFJError → {e}")

    # =========================================================================
    # OPERACIÓN 10: Cancelación de una reserva y manejo de doble cancelación
    # =========================================================================
    titulo("OP 10 — Cancelar reserva y demostrar encadenamiento de excepciones")

    # Primero confirmamos la reserva de asesoría de la OP 7.
    try:
        gestor.cancelar_reserva(r_asesoria, "El cliente reprogramó la sesión")

    except SistemaFJError as e:
        fallo(f"No se pudo cancelar → {e}")
    else:
        ok(f"Reserva cancelada. Estado: {r_asesoria.estado}")

    # Intentamos cancelar la misma reserva una segunda vez (debe fallar).
    try:
        gestor.cancelar_reserva(r_asesoria, "Segundo intento")

    except ReservaCanceladaError as e:
        # Encadenamos la excepción con contexto adicional para el log.
        try:
            raise ReservaInvalidaError(
                "intento de doble cancelación detectado"
            ) from e     # 'from e' encadena la excepción original como causa.
        except ReservaInvalidaError as encadenada:
            fallo(
                f"Excepción encadenada capturada → {encadenada} "
                f"| Causa original: {encadenada.__cause__}"
            )
            log.error("Doble cancelación intentada", encadenada)

    # =========================================================================
    # OPERACIÓN 11: Reserva sobre servicio deshabilitado
    # =========================================================================
    titulo("OP 11 — Reserva sobre servicio deshabilitado (ServicioNoDisponibleError)")

    try:
        # Deshabilitamos el portátil temporalmente.
        portatil.deshabilitar()
        ok("Servicio 'Portátil HP ProBook' deshabilitado manualmente.")

        # Intentamos crear y confirmar una reserva del servicio deshabilitado.
        r_deshab = gestor.crear_reserva(
            cliente=clientes[0],
            servicio=portatil,
            duracion=3,
            unidades=2,
        )
        gestor.confirmar_reserva(r_deshab)

    except ServicioNoDisponibleError as e:
        fallo(f"ServicioNoDisponibleError → {e}")
    except SistemaFJError as e:
        fallo(f"SistemaFJError → {e}")
    finally:
        # Siempre volvemos a habilitar el servicio para no afectar operaciones futuras.
        portatil.habilitar()
        print("  [FINALLY] Servicio 'Portátil' rehabilitado.")

    # =========================================================================
    # OPERACIÓN 12: Flujo completo — crear, confirmar y procesar
    # =========================================================================
    titulo("OP 12 — Flujo completo: crear → confirmar → procesar (Sala B, 2h)")

    try:
        r_completa = gestor.crear_reserva(
            cliente=clientes[2],       # Laura Ríos.
            servicio=sala_b,           # Sala B, sin equipar.
            duracion=2,                # 2 horas.
            participantes=4,           # 4 personas (dentro del límite de 6).
            descuento=5.0,             # 5 % de descuento.
        )
        costo = gestor.confirmar_reserva(r_completa)
        ok(f"Reserva confirmada. Costo: ${costo:,.2f} COP")

        # Marcamos como procesada (el servicio fue prestado).
        gestor.procesar_reserva(r_completa)
        ok(f"Reserva procesada. Estado final: {r_completa.estado}")

        print(r_completa.resumen_completo())

    except SistemaFJError as e:
        fallo(f"Error en flujo completo → {e}")

    # =========================================================================
    # REPORTE FINAL
    # =========================================================================
    titulo("REPORTE GENERAL DEL SISTEMA")
    print(gestor.reporte_general())

    # Mostramos la ruta del archivo de logs para que el usuario pueda revisarlo.
    titulo("ARCHIVO DE LOGS")
    log_instance = Logger()
    print(f"  Todos los eventos han sido registrados en:\n  {log_instance.ruta_log()}")
    print("\n" + "=" * 60)
    print("   Simulación finalizada exitosamente.")
    print("=" * 60 + "\n")


# =============================================================================
# Punto de entrada del script
# =============================================================================

if __name__ == "__main__":
    # Protección estándar para que main() solo se ejecute al correr este archivo.
    main()
