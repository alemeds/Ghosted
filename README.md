# Ghosted 👻

Encontrá quién no te sigue de vuelta en Instagram, desde una app web simple
hecha con [Streamlit](https://streamlit.io).

Inspirado en [InstagramUnfollowers](https://github.com/davidarroyo1234/InstagramUnfollowers)
de David Arroyo (MIT License) — ver [NOTICE.md](NOTICE.md) para el detalle de
la atribución. A diferencia del proyecto original (que corre en la consola
del navegador usando tu sesión ya logueada), Ghosted corre como una app
Python/Streamlit que inicia sesión en Instagram con `instagrapi`.

> **Proyecto educativo.** Ghosted existe para mostrar, de forma práctica,
> cómo se maneja una automatización real contra una API privada no
> documentada (2FA, fingerprint de dispositivo, rate-limiting) y cómo
> manejar sesiones/credenciales con criterios de seguridad razonables. No
> está pensado como producto para uso masivo ni recurrente — ver
> "Seguridad y privacidad" abajo antes de usarlo con tu cuenta real.

## Cómo funciona

1. Iniciás sesión pegando una cookie de sesión ya autenticada (ver detalle
   en "Login" abajo) — es la única forma soportada, evita por completo los
   problemas de 2FA/challenge del login por usuario y contraseña.
2. Ghosted escanea tus seguidores y las cuentas que seguís, calculando quién
   no te sigue de vuelta.
3. Podés filtrar, buscar, agregar cuentas a una lista blanca (para que nunca
   aparezcan como candidatas a unfollow) y exportar los resultados a CSV/JSON.
4. Opcionalmente, podés seleccionar cuentas y dejar de seguirlas, con pausas
   configurables entre cada acción para reducir el riesgo de un bloqueo
   temporal de Instagram. Queda un log descargable (`.txt`) de qué se dejó
   de seguir y cuándo.

La propia app tiene un panel "¿Qué es esto y cómo se usa?" con esta misma
explicación, en el idioma que elijas.

## Login: cookie de sesión

Ghosted solo soporta login por **cookie de sesión** (no usuario/contraseña):
te logueás normalmente en `instagram.com` en tu propio navegador (ahí
Instagram entrega 2FA sin problema, como siempre), exportás las cookies de
esa pestaña con la extensión
[EditThisCookie v3](https://chromewebstore.google.com/detail/editthiscookie-v3/ojfebgpkimhlhcblbalbfjblapadhbol)
(o Cookie-Editor, funciona igual), y pegás el resultado completo en
Ghosted — no hace falta buscar ni editar nada adentro, la app encuentra
sola el campo `sessionid` que necesita.

Esto evita por completo lidiar con el 2FA o los checkpoints de seguridad
de Instagram dentro de la app: para cuando tenés la cookie, ya pasaste esa
verificación en tu propio navegador.

### Cómo exportar la cookie (demo educativa)

La app tiene esta misma guía, más detallada, en un panel desplegable justo
donde se usa. La repetimos acá a propósito — el objetivo es que veas con tus
propios ojos lo fácil que es copiar el acceso completo a una cuenta:

1. **Instalar la extensión** (una vez): buscá "EditThisCookie v3" en la
   Chrome Web Store e instalá la versión oficial del desarrollador
   verificado — nunca una copia de un link suelto.
2. **Exportar:** con `instagram.com` logueado en esa pestaña, abrí la
   extensión y usá su botón de exportar — copia todas las cookies del sitio
   al portapapeles.
3. **Pegar:** volvé a Ghosted y pegá el resultado en el campo de cookie.
   Listo — sin tocar tu contraseña ni un código.
4. **Después de usarla:** borrá lo que copiaste del portapapeles y, si lo
   exportaste a un archivo, eliminalo. No la guardes en texto plano en
   ningún lado.

Esa misma facilidad es el riesgo: cualquiera con acceso a tu sesión de
Chrome (física o remota) puede hacer exactamente lo mismo. Por eso importa
cómo protegés la máquina:

- **Cifrá el disco** (FileVault/BitLocker) — sin esto, una máquina robada
  apagada expone todo, cookies incluidas.
- **Bloqueá la sesión** al alejarte, siempre.
- **Solo instalá extensiones de fuentes verificadas** y revisá qué permisos
  piden — una maliciosa puede exportar cookies en segundo plano, sin que
  hagas ningún clic.
- **Mantené el SO y el navegador actualizados** — la mayoría del malware
  que roba cookies ("infostealers") explota vulnerabilidades ya parcheadas.
- **Ojo con gestores de portapapeles que sincronizan a la nube.**
- **Cerrá sesión de verdad**, no solo cierres la pestaña.

## Seguridad y privacidad

- **Tu contraseña y tu cookie de sesión son, en la práctica, la misma cosa:
  una llave completa a tu cuenta.** Quien tenga cualquiera de las dos puede
  actuar como vos en Instagram sin necesitar ningún código. Nunca las
  compartas ni las pegues en sitios en los que no confíes — tampoco en
  herramientas educativas como esta. Si usás login por cookie, borrala de
  donde la exportaste apenas termines de usar la app, y considerá cerrar esa
  sesión desde la configuración de seguridad de Instagram (eso la invalida).
- Ambas se usan **solo para esta sesión de la app** y viven únicamente en
  memoria (`st.session_state`) mientras la pestaña del navegador está
  abierta. **Nunca se escriben a disco, variables de entorno, base de datos
  ni logs.**
- Al cerrar sesión o cerrar la app, las credenciales y el estado se pierden.
- Pensada para **uso ocasional**, no para dejarla corriendo de forma
  recurrente ni para múltiples usuarios simultáneos con estado persistente.
- Usar esta herramienta puede infringir los Términos de Servicio de
  Instagram (automatización de acciones de la cuenta). Es tu responsabilidad
  evaluar ese riesgo; los tiempos de espera configurables están para
  reducirlo, no para eliminarlo.
- Instagram puede pedir una verificación adicional (challenge por email/SMS,
  no solo 2FA por app autenticadora) en logins que considere sospechosos.
  Si aparece un challenge de seguridad, hay que resolverlo iniciando sesión
  desde la app oficial o el sitio web de Instagram primero, y volver a
  intentar acá — o directamente usar el login por cookie, que no lo dispara.

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
│   ├── auth.py              # Login instagrapi por cookie de sesión, credenciales solo en session_state
│   ├── scanner.py           # Fetch followers/following, cálculo de no-seguidores
│   ├── unfollow.py          # Acción de unfollow con timings/jitter
│   ├── whitelist.py         # Lista blanca (session_state + export/import JSON)
│   ├── timings.py           # Defaults y validación de tiempos configurables
│   └── i18n.py               # Loader de locales/{lang}.json
├── locales/
│   ├── en.json
│   └── es.json
├── tests/
│   ├── test_auth.py
│   ├── test_scanner.py
│   ├── test_whitelist.py
│   └── test_timings.py
├── .streamlit/config.toml   # Tema oscuro base (el selector en la app lo pisa por sesión)
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
