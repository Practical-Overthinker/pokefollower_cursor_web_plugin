# Small Change Guidelines

Las instrucciones del repositorio tienen prioridad.

## Clasificación

Un cambio es pequeño por su forma, no por líneas o archivos. Debe tener un resultado principal, impacto localizado, pocas decisiones y validación realizable en una iteración.

Escalar cuando aparezcan varias capacidades independientes, migración, compatibilidad temporal, rediseño arquitectónico, cambios de esquema o API, seguridad sensible, rollout o continuidad multifase.

## Alcance

Un cambio adicional pertenece al trabajo solo si es necesario para producir o validar el resultado. Registrar, pero no implementar, mejoras oportunistas y problemas independientes.

## Preguntas

Preguntar por comportamiento visible, contratos, datos, permisos, compatibilidad, dependencias relevantes o aceptación. Resolver sin preguntar nombres internos, helpers, estilo menor y decisiones cubiertas por patrones existentes.

Para ambigüedades no bloqueantes, elegir el supuesto conservador, registrarlo en `decision.log` y continuar.

## Validación

Priorizar checks del caso cambiado y validaciones disponibles del área. Para truth o catalog overlays, validar el catálogo del candidato afectado. No asumir ni añadir una validación transversal que el repositorio no defina.

Clasificar fallos como preexistentes, regresión, ambientales o no resueltos. Corregir regresiones dentro del alcance y reportar honestamente los demás.

## Cierre

Antes de terminar:

- revisar el diff;
- comprobar aceptación con evidencia;
- preservar trabajo ajeno;
- excluir secretos y temporales;
- actualizar `report.md`;
- continuar con revisión adversarial solo si fue solicitada explícitamente.
