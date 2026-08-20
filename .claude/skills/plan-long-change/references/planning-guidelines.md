# Planning Guidelines

Las instrucciones del repositorio y el handoff tienen prioridad.

## Fundamentar

Diseñar desde el estado real: flujo actual, contratos, dependencias, pruebas y comandos existentes. Inspeccionar solo áreas relacionadas y citar evidencia concreta en `plan.md`.

## Preguntar

Una decisión es material si cambia alcance, aceptación, arquitectura, comportamiento visible, datos, compatibilidad, seguridad, dependencias, transición u orden de fases.

Resolver durante la ejecución nombres internos, helpers, estilo y detalles reversibles cubiertos por patrones existentes. Separar decisiones confirmadas, supuestos conservadores y preguntas bloqueantes.

## Diseñar fases

Usar pocas fases basadas en resultados, no en capas técnicas. Cada fase debe dejar el repositorio coherente, tener dependencias claras, validaciones reales y criterios observables.

Detallar la primera fase con secuencia y riesgos inmediatos. Para fases posteriores conservar solo objetivo, resultado, dependencias, validación y detalles por refinar.

## Trazabilidad material

- `plan.md` es el plan maestro y conserva estados de fase.
- `decision.log` contiene solo decisiones y desviaciones materiales.
- `report.md` acumula una sección por fase; no duplica el plan.
- `handoff.md` permanece literal e inmutable.

## Validación del plan

Confirmar que:

- objetivo y alcance coinciden con el handoff;
- todos los criterios están cubiertos;
- no quedan bloqueantes ocultos;
- las fases posteriores no están sobrediseñadas;
- los comandos citados existen;
- riesgos y rollback son específicos cuando aplican.
