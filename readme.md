# DataRetail 360 · Pipeline ETL y Dashboard Comercial

Proyecto semestral de **Estructuras y Visualización de Datos (IDY1102)** para el caso **DataRetail 360** (Q1 2025: enero a marzo).

## Estructura del repositorio
- `notebooks/DataRetail360_ETL_Master-v2.ipynb`: Pipeline ETL (arquitectura Medallion, reglas DAMA, seudonimización SHA-256 Ley 21.719, SCD Tipo 2, Pandera y patrón WAP).
- `app.py` y `diseno.py`: Dashboard ejecutivo interactivo en Streamlit + Plotly conectado a la Capa Oro (`vw_ventas_dashboard`).
- `dataretail360_dwh.db`: Data Warehouse en SQLite (sin PII).
- `logs/etl.jsonl`: Registro estructurado de observabilidad del pipeline.

## Cómo ejecutar el dashboard
```bash
pip install -r requirements.txt
streamlit run app.py