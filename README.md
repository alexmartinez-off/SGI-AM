# SGI-AM: Sistema de Gestión de Inventario y Almacenamiento

SGI-AM es una aplicación diseñada para facilitar el control y seguimiento de inventario y existencias en tiempo real. Este sistema busca optimizar la gestión de productos en bodega y en uso, permitiendo una trazabilidad eficiente y control informado.

## 🚀 Objetivos del Proyecto

- Controlar el ingreso y salida de productos.
- Minimizar errores humanos y pérdidas de inventario.
- Generar reportes automáticos de stock y movimientos.
- Facilitar la integración con otros sistemas o bases de datos.

## 🛠️ Tecnologías Utilizadas

- Lenguaje principal: **Python**
- Base de datos: **MySQL**
- Framework backend: **Flask**
- UI: **HTML5**, **CSS3**, **Bootstrap**

## 📥 Instalación y Puesta en Marcha

1. **Clona el repositorio:**
   ```sh
   git clone https://github.com/alexmartinez-off/SGI-AM.git
   cd SGI-AM
   ```

2. **Crea y activa el entorno virtual:**
   ```sh
   python -m venv venv
   .\Scripts\activate
   ```

3. **Instala las dependencias:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Crea el archivo de variables de entorno `.env`:**
   - Crea un archivo llamado `.env` en la raíz del proyecto con el siguiente contenido de ejemplo:
     ```
     FLASK_APP=src:app
     FLASK_ENV=development
     SECRET_KEY=tu_clave_secreta
     DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost/sgi_am
     MAIL_SERVER=smtp.tu-servidor.com
     MAIL_PORT=587
     MAIL_USE_TLS=1
     MAIL_USERNAME=tu_correo
     MAIL_PASSWORD=tu_contraseña
     ```


5. **Inicia la aplicación:**
   ```sh
   flask --app src:app run
   ```

## 📁 Estructura Inicial del Proyecto

```
SGI-AM/
│
├── SGI/
│   ├── src/
│   │   ├── accounts/
│   │   │   ├── forms.py
│   │   │   ├── models.py
│   │   │   └── views.py
│   │   ├── inventario/
│   │   │   ├── models.py
│   │   │   └── views.py
│   │   ├── templates/
│   │   ├── static/
│   │   └── app.py
│   ├── requirements.txt
│   └── .env
├── README.md
└── .gitignore
```

## 📌 Estado del Proyecto

🚧 En desarrollo (base funcional implementada, en proceso de mejoras y características).

## 📄 Licencia

Este proyecto está bajo la licencia MIT.

---

> Desarrollado con *Ingenio*💡 en Sucre, Colombia.
