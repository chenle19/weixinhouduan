from fastapi import APIRouter

from app.schemas.common import ok


router = APIRouter()


@router.get("/routes")
def menu_routes() -> dict:
    return ok([
        {
            "path": "/miniapp",
            "component": "Layout",
            "redirect": "/miniapp/config",
            "name": "Miniapp",
            "meta": {
                "title": "美发小程序",
                "icon": "advert",
                "roles": ["admin"],
                "alwaysShow": True,
            },
            "children": [
                {
                    "path": "config",
                    "component": "miniapp/config",
                    "name": "MiniappConfig",
                    "meta": {
                        "title": "页面配置",
                        "icon": "advert",
                        "roles": ["admin"],
                    },
                }
            ],
        }
    ])
