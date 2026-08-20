---
name: plan-long-change
description: Convierte un handoff amplio en un plan maestro ejecutable por fases dentro de workbench. Úsala cuando el cambio abarque varias áreas, requiera checkpoints o varias sesiones, o el usuario pida planificar; puede detenerse tras el plan o continuar en modo end-to-end. No la uses para cambios pequeños, ejecutar una fase ya planificada ni revisar cambios terminados.
---

# Plan Long Change

Convertir un handoff amplio en un único plan maestro progresivo y fundamentado en el repositorio.

## Modos

- **Standalone:** crear o actualizar el plan, presentarlo y detenerse sin implementar.
- **End-to-end:** crear o actualizar el plan y continuar con `execute-plan-phase` mientras no exista un gate material y la implementación esté autorizada por la solicitud.

No pedir una aprobación redundante si el usuario ya solicitó ejecutar el handoff completo. Una solicitud de planificación solamente no autoriza implementación.

## Workspace

Crear o reutilizar `workbench/<slug>/`, usando el ID explícito o un slug estable derivado del cambio. Mantener:

- `handoff.md`: copia literal e inmutable del handoff recibido;
- `plan.md`: plan maestro, fases, gates, criterios y estado;
- `decision.log`: registro append-only de decisiones, supuestos y desviaciones materiales;
- `report.md`: reporte acumulativo de planificación, fases y cierre.

No crear carpetas o documentos por fase. Si el handoff llegó como archivo, conservar también el original; si llegó en la solicitud, materializar literalmente su contenido.

Usar para decisiones el formato `D-### | timestamp ISO 8601 | unidad | decisión | evidencia | impacto`.

## Recursos

- Leer [references/planning-guidelines.md](references/planning-guidelines.md) antes de diseñar fases.
- Usar [assets/plan-template.md](assets/plan-template.md) para `plan.md`.

## Procedimiento

1. Leer `AGENTS.md`, `handoff.md` y el estado del workspace existente.
2. Inspeccionar `git status`, arquitectura, contratos, pruebas y comandos reales relacionados. Usar historial Git solo cuando aclare decisiones vigentes.
3. Extraer objetivo, alcance, exclusiones, aceptación y decisiones cerradas. Verificar que el trabajo amerite fases.
4. Preguntar solo por decisiones materiales no resolubles localmente. Agrupar como máximo tres preguntas, explicar impacto, ofrecer alternativas reales y recomendar cuando haya evidencia.
5. Crear o actualizar un solo `plan.md`; nunca crear una variante para el mismo objetivo.
6. Diseñar el menor número de fases con resultados coherentes y verificables. Detallar la primera; mantener las posteriores progresivas.
7. Incluir dependencias, gates, validaciones, criterios de salida, riesgos y condiciones de reapertura.
8. Inicializar o actualizar `decision.log` y añadir a `report.md` una sección de planificación con estado y evidencia inspeccionada.
9. Verificar que cada criterio del handoff esté cubierto y que la primera fase no oculte bloqueantes.

No modificar código durante la unidad de planificación.

## Continuación

- En modo standalone, informar la ruta de `plan.md`, resumir fases y detenerse.
- En modo end-to-end, activar `execute-plan-phase` para la primera fase pendiente y continuar sin pedir confirmación mecánica.
- Si el trabajo resulta acotado, en standalone recomendar `implement-small-change`; en end-to-end cambiar a esa skill usando el mismo workspace.

## Finalización

La planificación termina cuando `plan.md` refleja el handoff y el repositorio, todas las decisiones bloqueantes están resueltas y la siguiente acción está identificada con criterios observables.
