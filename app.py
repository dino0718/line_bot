from fastapi import FastAPI
from routes.callback import router as callback_router
from core.database import init_db

# 啟動 FastAPI
app = FastAPI()

# 初始化 MySQL 資料庫
init_db()

# 掛載路由
app.include_router(callback_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
