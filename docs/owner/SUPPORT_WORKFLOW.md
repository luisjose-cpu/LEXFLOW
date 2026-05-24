# Support Workflow

## Flujo

1. Se crea ticket desde Owner Console con tenant opcional, categoria, prioridad y SLA.
2. Owner support revisa metadata no sensible.
3. Si requiere datos protegidos, solicita intervencion temporal desde Owner Console.
4. La intervencion define scopes, motivo y expiracion.
5. Se ejecuta soporte dentro del alcance autorizado.
6. Se cierra la intervencion temporal si el soporte termina antes de expirar.
7. Se crea incidente tecnico si el ticket revela degradacion de API, DB, Redis, storage, IA, WhatsApp, SINOE, jobs o backups.
8. Se resuelve el incidente con motivo operativo cuando el sistema queda estable.
9. Se resuelve ticket desde Owner Console y se registra audit log.

## Categorias iniciales

- SINOE
- Billing
- Integraciones
- Performance
- Acceso
- Datos demo
- Incidente tecnico

## Restricciones

Owner support no debe copiar, descargar ni exponer contenido de clientes, documentos o comunicaciones salvo autorizacion explicita del tenant y registro de auditoria.
