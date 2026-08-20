---
name: implement-small-change
description: Implementa y valida un cambio pequeño y localizado en este repositorio. Úsala para correcciones o capacidades acotadas que puedan completarse en una iteración enfocada; también puede operar como unidad dentro de una ejecución end-to-end. No la uses para cambios multifase, ejecutar una fase ya planificada ni hacer una revisión adversarial.
---

# Implement Small Change

Ejecutar un cambio pequeño de principio a fin sin crear un plan material.

## Modos

- **Standalone:** completar el cambio, actualizar su reporte y detenerse.
- **End-to-end:** completar el cambio y devolver control al bucle. Si deja de ser pequeño, continuar con `plan-long-change` en el mismo workspace. Ejecutar `adversarial-review` solo cuando el handoff lo exija explícitamente.

La solicitud vigente determina el modo. No pedir confirmación solo para cambiar entre unidades ya autorizadas.

## Workspace

Crear o reutilizar `workbench/<slug>/`, usando el ID explícito o un slug estable derivado del cambio. No crear variantes para el mismo objetivo.

Mantener únicamente:

- `handoff.md`: copia literal del handoff recibido; no reinterpretarlo ni reescribirlo;
- `decision.log`: registro append-only de decisiones, supuestos y desviaciones materiales;
- `report.md`: resultado verificable del cambio.

Si el handoff llegó como archivo, conservar también el original. Si llegó en la solicitud, materializar su contenido literalmente. No crear `plan.md` para un cambio pequeño.

Usar para decisiones el formato `D-### | timestamp ISO 8601 | unidad | decisión | evidencia | impacto`.

## Recursos

- Leer [references/small-change-guidelines.md](references/small-change-guidelines.md) antes de fijar el alcance.
- Usar [assets/small-change-report-template.md](assets/small-change-report-template.md) para `report.md`.

## Procedimiento

1. Leer `AGENTS.md`, `handoff.md` y solo el contexto necesario.
2. Inspeccionar `git status`, comportamiento actual, archivos y pruebas cercanas. Preservar cambios ajenos.
3. Confirmar que existe un solo resultado acotado, pocas decisiones abiertas y validación directa.
4. Definir internamente objetivo, alcance, fuera de alcance, aceptación y validaciones.
5. Preguntar solo si la evidencia local no resuelve una decisión material. Agrupar como máximo tres preguntas, recomendar cuando exista base y reanudar automáticamente tras la respuesta.
6. Establecer un baseline proporcional cuando ayude a distinguir fallos preexistentes.
7. Implementar el cambio mínimo coherente, con pruebas cuando cambie comportamiento verificable.
8. Validar incrementalmente con los checks reales disponibles. Si cambian truth o un catalog overlay, ejecutar `python scripts/build-catalog.py --candidate <id> --check`; no inventar un check global cuando el repositorio no lo define.
9. Revisar el diff completo y cada criterio de aceptación.
10. Actualizar `decision.log` solo si hubo decisiones materiales y escribir `report.md` con evidencia real.

La compilación y revisión visual de PDFs solo se realizan cuando una persona las solicita explícitamente, conforme a `AGENTS.md`.

## Escalamiento

Si el trabajo requiere fases, migración, cambios estructurales amplios o continuidad entre sesiones:

- en modo standalone, explicar la evidencia y recomendar `plan-long-change`;
- en modo end-to-end, activar `plan-long-change` sobre el mismo `workbench/<slug>/` y continuar.

## Finalización

Terminar cuando el cambio esté implementado y validado, exista un bloqueo material o se haya escalado. Nunca presentar como completo un comportamiento central no validado.
