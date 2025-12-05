from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
from app.routers.auth_db import get_current_user
from app.services import database_service
from app.core.database import get_mongo_db

# 创建路由器
router = APIRouter(prefix="/api/csv", tags=["csv-import"])

# 配置日志记录器
logger = logging.getLogger(__name__)

# 数据模型
class CSVValidateRequest(BaseModel):
    data: List[Dict[str, Any]]
    columns: List[str]

class CSVImportRequest(BaseModel):
    table: str
    mode: str
    data: List[Dict[str, Any]]
    columns: List[str]

class CSVImportResponse(BaseModel):
    success: bool
    data: dict
    message: str


@router.get("/tables")
async def get_tables():
    """
    获取支持的表列表
    """
    try:
        # 获取数据库服务实例
        db_service = database_service.DatabaseService()
        # 获取数据库中的所有集合名称
        collections = await db_service.get_all_collections()
        # 过滤掉系统集合（以system.开头的集合）
        valid_tables = [col for col in collections if not col.startswith("system.")]
        logger.info(f"✅ 获取表列表成功，共 {len(valid_tables)} 个表")
        return {
            "success": True,
            "data": valid_tables,
            "message": "获取表列表成功"
        }
    except Exception as e:
        logger.error(f"❌ 获取表列表失败: {e}")
        return {
            "success": False,
            "data": [],
            "message": f"获取表列表失败: {str(e)}"
        }


@router.post("/validate")
async def validate_csv(request: CSVValidateRequest):
    """
    验证CSV数据格式
    """
    try:
        data = request.data
        columns = request.columns
        
        # 基本验证
        if not data:
            raise HTTPException(status_code=400, detail="没有要验证的数据")
        
        if not columns:
            raise HTTPException(status_code=400, detail="没有指定列名")
        
        # 验证每一行数据的字段数量是否一致
        for i, row in enumerate(data):
            if len(row) != len(columns):
                raise HTTPException(
                    status_code=400, 
                    detail=f"第 {i+1} 行数据字段数量与列名数量不一致"
                )
        
        logger.info(f"✅ CSV数据验证成功，共 {len(data)} 行，{len(columns)} 列")
        return {
            "success": True,
            "message": "数据格式验证成功",
            "row_count": len(data),
            "column_count": len(columns)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ CSV数据验证失败: {e}")
        raise HTTPException(status_code=500, detail="数据验证失败")


@router.post("/import", response_model=CSVImportResponse)
async def import_csv(request: CSVImportRequest):
    """
    导入CSV数据到指定表
    
    同一日期更新导入同一数据表的为全量覆盖
    """
    try:
        table = request.table
        mode = request.mode
        data = request.data
        columns = request.columns
        
        # 基本验证
        if not table:
            raise HTTPException(status_code=400, detail="请指定目标表")
        
        if mode not in ["insert", "update", "upsert"]:
            raise HTTPException(status_code=400, detail="无效的导入模式")
        
        if not data:
            raise HTTPException(status_code=400, detail="没有要导入的数据")
        
        # 获取数据库服务实例
        db_service = database_service.DatabaseService()
        
        # 调用数据库服务导入数据
        # MongoDB会自动创建不存在的集合，所以不需要显式创建表
        result = await db_service.import_data(
            collection_name=table,
            data=data,
            mode=mode
        )
        
        logger.info(f"✅ 表 {table} 数据导入完成")
        
        logger.info(
            f"✅ CSV数据导入成功，表: {table}, 模式: {mode}, "
            f"成功: {result['success_count']}, 失败: {result['error_count']}"
        )
        
        return {
            "success": True,
            "data": {
                "imported": result["success_count"],
                "failed": result["error_count"]
            },
            "message": f"数据导入完成，成功 {result['success_count']} 条，失败 {result['error_count']} 条"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ CSV数据导入失败: {e}")
        logger.error(f"❌ 错误详情: {str(e)}")
        logger.error(f"❌ 错误类型: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"数据导入失败: {str(e)}")


# 新增：数据筛选请求模型
class DataFilterRequest(BaseModel):
    table: str
    filters: Dict[str, Any] = {}
    page: int = 1
    page_size: int = 20
    sort: str = ""
    order: str = ""


@router.post("/filter")
async def filter_imported_data(request: DataFilterRequest):
    """
    筛选导入的数据
    """
    try:
        table = request.table
        filters = request.filters
        page = request.page
        page_size = request.page_size
        sort = request.sort
        order = request.order
        
        # 基本验证
        if not table:
            raise HTTPException(status_code=400, detail="请指定目标表")
        
        # 计算跳过的条数
        skip = (page - 1) * page_size
        
        # 获取数据库实例
        db = get_mongo_db()
        collection = db[table]
        
        # 构建查询条件
        query = {}
        for key, value in filters.items():
            if value is not None and value != "" and value != "all":
                query[key] = value
        
        # 构建排序条件
        sort_criteria = {}
        if sort:
            sort_criteria[sort] = 1 if order == "ascending" else -1
        
        # 查询数据
        total = await collection.count_documents(query)
        cursor = collection.find(query)
        
        # 应用排序
        if sort_criteria:
            cursor = cursor.sort(sort_criteria)
        
        # 应用分页
        documents = await cursor.skip(skip).limit(page_size).to_list(length=page_size)
        
        # 转换ObjectId为字符串
        for doc in documents:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
        
        logger.info(
            f"✅ 数据筛选完成，表: {table}, "
            f"条件: {filters}, 总记录: {total}, "
            f"第 {page} 页，每页 {page_size} 条"
        )
        
        return {
            "success": True,
            "data": documents,
            "total": total,
            "page": page,
            "page_size": page_size,
            "message": "数据筛选完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 数据筛选失败: {e}")
        return {
            "success": False,
            "data": [],
            "total": 0,
            "page": request.page,
            "page_size": request.page_size,
            "message": f"数据筛选失败: {str(e)}"
        }
