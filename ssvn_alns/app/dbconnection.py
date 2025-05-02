import aiomysql
import sqlalchemy as sa
import asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from config import MYSQL_PASS

loop = asyncio.get_event_loop()

async def connection():
    conn = await aiomysql.connect(host="127.0.0.1", 
                                  port=3306,
                                  user='root', 
                                  password=MYSQL_PASS, 
                                  db="mysql")
    
    cursor = await conn.cursor()
