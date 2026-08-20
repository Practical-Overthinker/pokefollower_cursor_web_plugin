---
name: execute-plan-phase
description: Ejecuta y valida una fase del plan de un cambio largo en workbench, reconcilia su estado y acumula evidencia en el reporte. Úsala cuando exista una fase ejecutable; en modo standalone termina tras esa fase y en modo end-to-end continúa por fases autorizadas. No la uses para crear el plan, resolver un cambio pequeño sin plan ni hacer revisión adversarial.
---

# Execute Plan Phase

Ejecutar una fase aprobada sin perder sus límites ni la continuidad del cambio largo.

## Modos

- **Standalone:** ejecutar la fase identificada, reconciliar artefactos y detenerse.
- **End-to-end:** ejecutar la siguiente fase pendiente y repetir con las siguientes mientras estén autorizadas y no exista un gate material.

La solicitud vigente determina el modo. No pedir confirmación entre fases cuando `handoff.md` ya autoriza la ejecución completa y `plan.md` no declara un gate.

## Workspace

Trabajar exclusivamente con el workspace existente `workbench/<slug>/`:

- `handoff.md`: fuente original inmutable;
- `plan.md`: plan maestro y estado de fases;
- `decision.log`: registro append-only material;
- `report.md`: reporte acumulativo con una sección por ejecución de fase y cierre final.

No crear planes o reportes separados por fase.

Usar para decisiones el formato `D-### | timestamp ISO 8601 | unidad | decisión | evidencia | impacto`.

## Recursos

- Leer [references/execution-guidelines.md](references/execution-guidelines.md) antes de editar.
- Usar [assets/phase-report-template.md](assets/phase-report-template.md) como sección que se añade a `report.md`.

## Procedimiento por fase

1. Leer `AGENTS.md`, `handoff.md`, el plan completo, decisiones y reporte previo.
2. Identificar la fase solicitada en standalone o la primera pendiente en end-to-end. Verificar dependencias, gates y criterios.
3. Inspeccionar `git status`, áreas afectadas, pruebas y vigencia de supuestos. Preservar cambios ajenos.
4. Refinar en `plan.md` solo los detalles de la fase que la evidencia actual permita cerrar.
5. Preguntar únicamente cuando continuar requiera redefinir objetivo, alcance, arquitectura, datos, seguridad, compatibilidad, comportamiento visible o autorización. Agrupar como máximo tres preguntas y reanudar tras la respuesta.
6. Implementar únicamente el resultado de la fase en incrementos pequeños y coherentes.
7. Validar incrementalmente y ejecutar los checks reales exigidos por `AGENTS.md`. Si cambian truth o un catalog overlay, ejecutar `python scripts/build-catalog.py --candidate <id> --check`; no asumir que existe un check global.
8. Revisar el diff completo y comprobar cada criterio de salida con evidencia real.
9. Actualizar la fase en `plan.md` como `Complete`, `Partial` o `Blocked`; no rediseñar fases no afectadas.
10. Añadir a `report.md` una sección con resultado, checks, desviaciones, fallos y siguiente checkpoint. No borrar evidencia de intentos anteriores.
11. Registrar en `decision.log` solo decisiones, supuestos o desviaciones materiales.

La compilación, conteo de páginas y QA visual de PDFs se ejecutan únicamente cuando una persona los solicita explícitamente.

## Continuación

- En standalone, detenerse después de reportar la fase.
- En end-to-end, continuar con la siguiente fase autorizada.
- Si todas las fases pasan, marcar el plan completo y añadir un cierre consolidado a `report.md`.
- Activar `adversarial-review` únicamente si el handoff la exige explícitamente.
- Si una corrección deja de pertenecer al plan, preguntar antes de ampliar alcance.

## Finalización

Una fase solo está completa cuando sus criterios esenciales y validaciones requeridas tienen evidencia. No convertir un resultado parcial o no comprobado en `Complete`.
