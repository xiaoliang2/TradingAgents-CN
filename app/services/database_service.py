"""
数据库管理服务
"""

import json
import os
import csv
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId
import motor.motor_asyncio
import redis.asyncio as redis
from pymongo.errors import ServerSelectionTimeoutError

from app.core.database import get_mongo_db, get_redis_client, db_manager
from app.core.config import settings

from app.services.database import status_checks as _db_status
from app.services.database import cleanup as _db_cleanup
from app.services.database import backups as _db_backups
from app.services.database.serialization import serialize_document as _serialize_doc

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库管理服务"""

    def __init__(self):
        self.backup_dir = os.path.join(settings.TRADINGAGENTS_DATA_DIR, "backups")
        self.export_dir = os.path.join(settings.TRADINGAGENTS_DATA_DIR, "exports")

        # 确保目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.export_dir, exist_ok=True)

    async def get_database_status(self) -> Dict[str, Any]:
        """获取数据库连接状态（委托子模块）"""
        return await _db_status.get_database_status()

    async def _get_mongodb_status(self) -> Dict[str, Any]:
        """获取MongoDB状态（委托子模块）"""
        return await _db_status.get_mongodb_status()

    async def _get_redis_status(self) -> Dict[str, Any]:
        """获取Redis状态（委托子模块）"""
        return await _db_status.get_redis_status()

    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            db = get_mongo_db()

            # 获取所有集合
            collection_names = await db.list_collection_names()

            collections_info = []
            total_documents = 0
            total_size = 0

            # 并行获取所有集合的统计信息
            import asyncio

            async def get_collection_stats(collection_name: str):
                """获取单个集合的统计信息"""
                try:
                    stats = await db.command("collStats", collection_name)
                    # 使用 collStats 中的 count 字段，避免额外的 count_documents 查询
                    doc_count = stats.get('count', 0)

                    return {
                        "name": collection_name,
                        "documents": doc_count,
                        "size": stats.get('size', 0),
                        "storage_size": stats.get('storageSize', 0),
                        "indexes": stats.get('nindexes', 0),
                        "index_size": stats.get('totalIndexSize', 0)
                    }
                except Exception as e:
                    logger.error(f"获取集合 {collection_name} 统计失败: {e}")
                    return {
                        "name": collection_name,
                        "documents": 0,
                        "size": 0,
                        "storage_size": 0,
                        "indexes": 0,
                        "index_size": 0
                    }

            # 并行获取所有集合的统计
            collections_info = await asyncio.gather(
                *[get_collection_stats(name) for name in collection_names]
            )

            # 计算总计
            for collection_info in collections_info:
                total_documents += collection_info['documents']
                total_size += collection_info['storage_size']

            return {
                "total_collections": len(collection_names),
                "total_documents": total_documents,
                "total_size": total_size,
                "collections": collections_info
            }
        except Exception as e:
            raise Exception(f"获取数据库统计失败: {str(e)}")

    async def test_connections(self) -> Dict[str, Any]:
        """测试数据库连接（委托子模块）"""
        return await _db_status.test_connections()

    async def _test_mongodb_connection(self) -> Dict[str, Any]:
        """测试MongoDB连接（委托子模块）"""
        return await _db_status.test_mongodb_connection()

    async def _test_redis_connection(self) -> Dict[str, Any]:
        """测试Redis连接（委托子模块）"""
        return await _db_status.test_redis_connection()

    async def create_backup(self, name: str, collections: List[str] = None, user_id: str = None) -> Dict[str, Any]:
        """
        创建数据库备份（自动选择最佳方法）

        - 如果 mongodump 可用，使用原生备份（快速）
        - 否则使用 Python 实现（兼容性好但较慢）
        """
        # 检查 mongodump 是否可用
        if _db_backups._check_mongodump_available():
            logger.info("✅ 使用 mongodump 原生备份（推荐）")
            return await _db_backups.create_backup_native(
                name=name,
                backup_dir=self.backup_dir,
                collections=collections,
                user_id=user_id
            )
        else:
            logger.warning("⚠️ mongodump 不可用，使用 Python 备份（较慢）")
            logger.warning("💡 建议安装 MongoDB Database Tools 以获得更快的备份速度")
            return await _db_backups.create_backup(
                name=name,
                backup_dir=self.backup_dir,
                collections=collections,
                user_id=user_id
            )

    async def list_backups(self) -> List[Dict[str, Any]]:
        """获取备份列表（委托子模块）"""
        return await _db_backups.list_backups()

    async def delete_backup(self, backup_id: str) -> None:
        """删除备份（委托子模块）"""
        await _db_backups.delete_backup(backup_id)

    async def cleanup_old_data(self, days: int) -> Dict[str, Any]:
        """清理旧数据（委托子模块）"""
        return await _db_cleanup.cleanup_old_data(days)

    async def cleanup_analysis_results(self, days: int) -> Dict[str, Any]:
        """清理过期分析结果（委托子模块）"""
        return await _db_cleanup.cleanup_analysis_results(days)

    async def cleanup_operation_logs(self, days: int) -> Dict[str, Any]:
        """清理操作日志（委托子模块）"""
        return await _db_cleanup.cleanup_operation_logs(days)

    async def import_data(self, content: bytes, collection: str, format: str = "json",
                         overwrite: bool = False, filename: str = None) -> Dict[str, Any]:
        """导入数据（委托子模块）"""
        return await _db_backups.import_data(content, collection, format=format, overwrite=overwrite, filename=filename)

    async def export_data(self, collections: List[str] = None, format: str = "json", sanitize: bool = False) -> str:
        """导出数据（委托子模块）"""
        return await _db_backups.export_data(collections, export_dir=self.export_dir, format=format, sanitize=sanitize)

    def _serialize_document(self, doc: dict) -> dict:
        """序列化文档，处理特殊类型（委托子模块）"""
        return _serialize_doc(doc)
    
    async def get_all_collections(self) -> List[str]:
        """
        获取所有集合名称
        """
        db = get_mongo_db()
        return await db.list_collection_names()
    
    async def import_data(self, collection_name: str, data: List[Dict[str, Any]], mode: str = "insert") -> Dict[str, Any]:
        """
        直接导入数据列表到指定集合
        
        参数:
            collection_name: 目标集合名称
            data: 要导入的数据列表
            mode: 导入模式，可选值: insert, update, upsert
            
        返回:
            导入结果
        """
        db = get_mongo_db()
        collection = db[collection_name]
        
        success_count = 0
        error_count = 0
        errors = []
        
        # 获取当前日期，格式：YYYY-MM-DD
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 同一日期更新导入同一数据表的为全量覆盖
        # 1. 检查是否有当天导入的数据
        existing_count = await collection.count_documents({"导入日期": current_date})
        
        if existing_count > 0:
            # 2. 如果有当天导入的数据，先删除所有当天的数据
            logger.info(f"📋 检测到表 {collection_name} 中已有 {existing_count} 条 {current_date} 导入的数据")
            logger.info(f"🔄 执行全量覆盖：删除表 {collection_name} 中所有 {current_date} 导入的数据")
            
            delete_result = await collection.delete_many({"导入日期": current_date})
            logger.info(f"✅ 成功删除 {delete_result.deleted_count} 条当天数据")
        
        for i, doc in enumerate(data):
            try:
                # 在所有导入数据中增加一列日期（后端双重保障）
                doc_with_date = doc.copy()
                # 强制使用当前日期作为导入日期，确保全量覆盖逻辑正常工作
                doc_with_date["导入日期"] = current_date
                logger.info(f"📅 为第 {i+1} 行数据添加导入日期: {current_date}")
                
                # 直接插入数据，不进行日期字段转换
                if mode == "insert":
                    # 插入模式：直接插入新文档
                    await collection.insert_one(doc_with_date)
                    success_count += 1
                elif mode == "update":
                    # 更新模式：需要找到匹配的文档
                    # 尝试使用股票代码作为唯一标识符（CSV数据中可能没有_id字段）
                    if "股票代码" in doc_with_date:
                        # 使用股票代码和导入日期作为查询条件
                        query = {
                            "股票代码": doc_with_date["股票代码"],
                            "导入日期": current_date
                        }
                        result = await collection.update_one(
                            query,
                            {"$set": doc_with_date}
                        )
                        if result.matched_count > 0:
                            success_count += 1
                        else:
                            # 如果没有找到匹配的文档，改为插入
                            await collection.insert_one(doc_with_date)
                            success_count += 1
                            logger.info(f"⚠️ 第 {i+1} 行：未找到匹配文档，改为插入")
                    elif "_id" in doc_with_date:
                        # 使用_id作为唯一标识符
                        result = await collection.update_one(
                            {"_id": doc_with_date["_id"]},
                            {"$set": doc_with_date}
                        )
                        if result.matched_count > 0:
                            success_count += 1
                        else:
                            error_count += 1
                            errors.append(f"第 {i+1} 行：未找到匹配的文档")
                    else:
                        # 没有唯一标识符，直接插入
                        await collection.insert_one(doc_with_date)
                        success_count += 1
                        logger.info(f"⚠️ 第 {i+1} 行：无唯一标识符，直接插入")
                elif mode == "upsert":
                    # 新增或更新模式
                    if "股票代码" in doc_with_date:
                        # 使用股票代码和导入日期作为查询条件
                        query = {
                            "股票代码": doc_with_date["股票代码"],
                            "导入日期": current_date
                        }
                        await collection.update_one(
                            query,
                            {"$set": doc_with_date},
                            upsert=True
                        )
                        success_count += 1
                    elif "_id" in doc_with_date:
                        # 使用_id作为唯一标识符
                        await collection.update_one(
                            {"_id": doc_with_date["_id"]},
                            {"$set": doc_with_date},
                            upsert=True
                        )
                        success_count += 1
                    else:
                        # 没有唯一标识符，直接插入
                        await collection.insert_one(doc_with_date)
                        success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"第 {i+1} 行：{str(e)}")
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
