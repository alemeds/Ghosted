# Ghosted 👻

Encontrá quién no te sigue de vuelta en Instagram, desde una app web simple
hecha con [Streamlit](https://streamlit.io).

Inspirado en [InstagramUnfollowers](https://github.com/davidarroyo1234/InstagramUnfollowers)
de David Arroyo (MIT License) — ver [NOTICE.md](NOTICE.md) para el detalle de
la atribución. A diferencia del proyecto original (que corre en la consola
del navegador usando tu sesión ya logueada), Ghosted corre como una app
Python/Streamlit que inicia sesión en Instagram con `instagrapi`.

## Cómo funciona

1. Ingresás tu usuario y contraseña de Instagram en el formulario de login.
2. Ghosted escanea tus seguidores y las cuentas que seguís, calculando quién
   no te sigue de vuelta.
3. Podés filtrar, buscar, agregar cuentas a una lista blanca (para que nunca
   aparezcan como candidatas a unfollow) y exportar los resultados a CSV/JSON.
4. Opcionalmente, podés seleccionar cuentas y dejar de seguirlas, con pausas
   configurables entre cada acción para reducir el riesgo de un bloqueo
   temporal de Instagram.

## Seguridad y privacidad

- Tu usuario y contraseña se usan **solo para esta sesión de la app** y viven
  únicamente en memoria (`st.session_state`) mientras la pestaña del
  navegador está abierta. **Nunca se escriben a disco, variables de entorno,
  base de datos ni logs.**
- Al cerrar sesión o cerrar la app, las credenciales y el estado se pierden.
- Pensada para **uso ocasional**, no para dejarla corriendo de forma
  recurrente ni para múltiples usuarios simultáneos con estado persistente.
- Usar esta herramienta puede infringir los Términos de Servicio de
  Instagram (automatización de acciones de la cuenta). Es tu responsabilidad
  evaluar ese riesgo; los tiempos de espera configurables están para
  reducirlo, no para eliminarlo.
- Instagram puede pedir una verificación adicional (challenge por email/SMS,
  no solo 2FA por app autenticadora) en logins que considere sospechosos.
  Ghosted soporta 2FA con código; si aparece un challenge de seguridad, hay
  que resolverlo iniciando sesión desde la app oficial o el sitio web de
  Instagram primero, y volver a intentar acá.

## Instalación

Requiere Python 3.11+.

```bash
git clone https://github.com/alemeds/Ghosted.git
cd Ghosted
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run src/app.py
```

Abre automáticamente `http://localhost:8501` en el navegador.

No hay variables de entorno requeridas: no se guarda ningún secreto fuera de
la sesión activa del navegador.

## Tests

```bash
pip install pytest
pytest
```

## Estructura del proyecto

```
Ghosted/
├── src/
│   ├── app.py              # Entry point Streamlit, orquesta las vistas
│   ├── auth.py              # Login instagrapi, credenciales solo en session_state
│   ├── scanner.py           # Fetch followers/following, cálculo de no-seguidores
│   ├── unfollow.py          # Acción de unfollow con timings/jitter
│   ├── whitelist.py         # Lista blanca (session_state + export/import JSON)
│   ├── timings.py           # Defaults y validación de tiempos configurables
│   └── i18n.py               # Loader de locales/{lang}.json
├── locales/
│   ├── en.json
│   └── es.json
├── tests/
│   ├── test_scanner.py
│   ├── test_whitelist.py
│   └── test_timings.py
├── .streamlit/config.toml   # Tema oscuro
├── requirements.txt
├── NOTICE.md                # Atribución al proyecto original
└── LICENSE
```

## Deploy en Streamlit Community Cloud

1. Subí el repo a GitHub (ya hecho si estás leyendo esto desde ahí).
2. En [share.streamlit.io](https://share.streamlit.io), "New app" → elegí
   este repo, branch `main`, main file path `src/app.py`.
3. No hace falta configurar ningún secret: las credenciales las pone cada
   usuario en tiempo de ejecución, en su propia sesión del navegador.
