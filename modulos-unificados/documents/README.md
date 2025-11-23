# Carpeta de Documentos

Esta carpeta contiene documentos de referencia utilizados por el chatbot educativo.

## Archivos esperados

- `documento_diabetes_guia.pdf`: Documento con información educativa sobre diabetes

## Uso

El chatbot cargará automáticamente los documentos PDF de esta carpeta al iniciar el servidor. Si no encuentra el documento, funcionará sin contexto adicional pero seguirá respondiendo preguntas generales sobre diabetes.

## Cómo agregar documentos

1. Coloca tu archivo PDF en esta carpeta
2. Nombra el archivo como `documento_diabetes_guia.pdf` o actualiza la ruta en `services/chatbot_service.py`
3. Reinicia el servidor para que cargue el nuevo documento
