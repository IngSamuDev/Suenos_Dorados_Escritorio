from routes.autenticacion_routes import router as auth_router
from routes.catalogo_routes import router as catalog_router
from routes.panel_routes import router as dashboard_router
from routes.descuentos_routes import router as descuentos_router
from routes.inventario_routes import router as inventory_router
from routes.logistica_routes import router as logistics_router
from routes.ventas_routes import router as sales_router
from routes.bold_routes import router as bold_router

api_routers = [
    dashboard_router,
    auth_router,
    catalog_router,
    descuentos_router,
    inventory_router,
    sales_router,
    logistics_router,
    bold_router,
]

