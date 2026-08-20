# Execution Guidelines

Las instrucciones del repositorio, el handoff y el plan aprobado tienen prioridad.

## Límite de fase

Pertenece a la fase lo necesario para producir y validar su resultado. Registrar como pendiente mejoras generales, trabajo futuro y problemas independientes. Detenerse ante ampliaciones materiales.

## Workspace existente

Inspeccionar `git status`, preservar cambios preexistentes y evitar archivos ya modificados cuando no sea posible separar el trabajo con seguridad. Un árbol sucio solo bloquea si impide atribución o preservación.

## Ejecución incremental

1. Confirmar baseline relevante.
2. Introducir el cambio mínimo coherente.
3. Validar el incremento.
4. Añadir cobertura contra regresiones.
5. Revisar el diff.
6. Ampliar solo si falta un criterio de la fase.

## Evidencia y fallos

Aceptar como evidencia tests, checks estáticos, build, comandos reproducibles o validación manual autorizada. Clasificar fallos como preexistentes, regresión, ambientales o no resueltos.

Ejecutar los checks que el repositorio realmente defina para el área modificada. Para truth o catalog overlays, validar el catálogo del candidato afectado. No añadir un check global, render o QA PDF sin solicitud humana explícita.

## Reconciliación

- Actualizar estado y criterios en `plan.md`.
- Añadir una sección de fase a `report.md`.
- Preservar decisiones históricas.
- Ajustar fases futuras solo cuando la nueva evidencia invalide un supuesto.
- En end-to-end, avanzar sin una aprobación mecánica cuando no exista gate.

## Estados

- **Complete:** criterios esenciales y validación requerida satisfechos.
- **Partial:** existe valor, pero falta un criterio o check relevante.
- **Blocked:** requiere decisión, autoridad, acceso o dependencia externa.
