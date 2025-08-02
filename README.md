# s3-interface
---

## 📄 Descripción

Como parte de un proyecto más grande he extraído algunas plantillas y el código básico para subir, visualizar y descargar ficheros (en este caso solo permite fotos) de un S3 (AWS). Aunque no incluye una lógica real para un login, he subido la plantilla también. Para dar acceso a los recursos de AWS es necesario descargar y configurar 'aws cli'
```bash
sudo apt install aws-cli
aws configure
```
Es necesario haber creado un usuario como mínimo con permisos para S3. Si se añaden permisos de Cost Explorer se puede visualizar el uso, costo y previsión para S3.
---

## 🚀 Características

* Plantilla drag & drop para arrastrar ficheros o selecionarlos desde el ordenador
* Plantilla para visualizar y descargar fotos:
    * **Alta disponibilidad:** El backend genera un link prefirmado que se envía al navegador y desde este se accede al bucket (privado). Esto aprovecha la alta disponibilidad de S3 al no enviar la foto al servidor.
    * **Servidor de bajo costo:** Ideal en caso de un homelab.
    * **Costo:** S3 está pensado para replicabilidad y algunas características ya comentadas enfocadas a uso masivo, como almacenamiento a largo plazo es ligeramente más caro que un Google Drive (2,30 vs 2,00 Euros/mes 100Gb).
* Ideal si habitualmente debes acceder a ficheros de algún proyecto o para descargar informes que se depositan en el S3:
---

## 🛠️ Instalación

La sencillez del frontend permite que con instalar unicamente las dependencias de python el proyecto funcione. Boto3 y Flask. 

```bash
pip install -r requirements.txt
```
y por supuesto tener configurado aws-cli.
---

##  Código
* Estructura de archivos reducida. app.py contiene todo el código python (las 3 rutas principales, alguna función de la API y otras complementarias)
* Cada template incluye el estilo y el código js.
* Sin la autenticación no se puede acceder a subida o descarga. 
---
***Para que el usuario creado tenga acceso a costes no basta con otorgarle permisos de grupo. Se debe activar una opción en el perfil con root access.***
