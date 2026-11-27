# Trabajo Articulo Moda

Proyecto full-stack del grupo 13: Boutique de Moda "Estilo Urbano".

## Caso de estudio

- Colección MongoDB: `prendas`
- Entidad Pydantic: `ArticuloModa`
- Campos: `prenda`, `talla`, `precio`, `en_exhibicion`, `imagen_url`
- Filtros: `Colección`, `En Exhibición`, `Sin Stock`, `Nueva Prenda`

## Ejecutar localmente

Backend:

```powershell
python -m pip install -r requirements.txt
Set-Location Backend
uvicorn main:app --reload
```

Frontend: abrir `Frontend/index.html` con Live Server. El frontend usa `http://127.0.0.1:8000` en localhost.

Para producción, configure en `Frontend/index.html` el meta `api-base-url` con la URL pública de Render o defina `window.API_BASE_URL` antes de cargar `app.js`.


