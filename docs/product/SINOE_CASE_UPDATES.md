# SINOE Case Updates

## User Value

SINOE updates connect judicial mailbox activity to Expediente 360. The law firm can see monitored sources, latest checks, updates, alerts and timeline events without losing tenant control or auditability.

## Settings

`Settings -> Integraciones -> SINOE` provides:

- Usuario SINOE
- Contrasena SINOE
- Estado de conexion
- Ultima verificacion
- Probar conexion
- Actualizar expedientes
- Desactivar integracion

The password input is write-only and is never rehydrated into the browser.

## Expediente 360

Each case can show:

- SINOE source
- external case number
- district/site/reference label
- status
- last checked at
- last result
- pending CAPTCHA state
- review action
- SINOE update history

## Update Result

When the mock adapter detects a new update, LEXFLOW creates:

- `judicial_update`
- `case_event`
- `notification`
- `judicial_evidence`
- `audit_log`

Client visibility is not automatic. SINOE updates remain internal unless later approved by an explicit portal visibility flow.
