"""
设置管理路由组件
提供WebUI的通用设置管理，如壁纸上传等
"""

import shutil
from pathlib import Path
from typing import Optional
import mimetypes

from fastapi import UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.common.logger import get_logger
from src.common.security import VerifiedDep
from src.plugin_system import BaseRouterComponent
from src.config.config import PROJECT_ROOT

logger = get_logger("WebUI.SettingRouter")

# 数据目录
DATA_DIR = Path(PROJECT_ROOT) / "data" / "webui"
WALLPAPER_DIR = DATA_DIR

# 文件大小限制（50MB）
MAX_FILE_SIZE = 50 * 1024 * 1024

class WallpaperResponse(BaseModel):
    """壁纸上传响应"""
    success: bool
    url: str
    type: str  # 'image' or 'video'
    message: Optional[str] = None

class WebUISettingRouter(BaseRouterComponent):
    """
    WebUI设置管理路由组件
    
    提供以下API端点：
    - POST /wallpaper: 上传壁纸
    - GET /wallpaper: 获取当前壁纸
    - DELETE /wallpaper: 删除当前壁纸
    """
    
    component_name = "setting"
    component_description = "WebUI设置管理接口"
    
    def __init__(self):
        super().__init__()
        # 确保目录存在
        WALLPAPER_DIR.mkdir(parents=True, exist_ok=True)
    
    def register_endpoints(self) -> None:
        """注册所有HTTP端点"""
        
        @self.router.post("/wallpaper", summary="上传壁纸", response_model=WallpaperResponse)
        async def upload_wallpaper(file: UploadFile = File(...), _=VerifiedDep):
            """
            上传WebUI壁纸（支持图片和视频）
            """
            try:
                # 检查文件类型
                content_type = file.content_type or ""
                
                if content_type.startswith("image/"):
                    wallpaper_type = "image"
                    allowed = True
                elif content_type.startswith("video/"):
                    wallpaper_type = "video"
                    # 限制视频格式
                    allowed = content_type in ["video/mp4", "video/webm", "video/ogg"]
                else:
                    raise HTTPException(status_code=400, detail="只支持图片或视频文件")
                
                if not allowed:
                    raise HTTPException(status_code=400, detail="不支持的视频格式，请使用 MP4 或 WebM")
                
                # 获取文件扩展名
                ext = Path(file.filename).suffix
                if not ext:
                    ext = ".mp4" if wallpaper_type == "video" else ".png"
                
                filename = f"current_wallpaper{ext}"
                file_path = WALLPAPER_DIR / filename
                
                # 删除旧的壁纸（如果有不同扩展名的）
                for old_file in WALLPAPER_DIR.glob("current_wallpaper*"):
                    try:
                        old_file.unlink()
                    except Exception:
                        pass
                
                # 保存文件
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # 检查文件大小
                file_size = file_path.stat().st_size
                if file_size > MAX_FILE_SIZE:
                    file_path.unlink()
                    raise HTTPException(
                        status_code=400, 
                        detail=f"文件过大（{file_size / 1024 / 1024:.1f}MB），请上传小于 50MB 的文件"
                    )
                
                # 返回访问URL
                return WallpaperResponse(
                    success=True,
                    url=f"/api/setting/wallpaper/image?t={int(file_path.stat().st_mtime)}",
                    type=wallpaper_type,
                    message="壁纸上传成功"
                )
            
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"上传壁纸失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/wallpaper/image", summary="获取壁纸图片")
        async def get_wallpaper_image():
            """
            获取当前壁纸文件（图片或视频）
            """
            try:
                # 查找当前壁纸
                files = list(WALLPAPER_DIR.glob("current_wallpaper*"))
                if not files:
                    raise HTTPException(status_code=404, detail="未设置壁纸")
                
                file_path = files[0]
                
                # 自动检测 MIME 类型
                mime_type, _ = mimetypes.guess_type(str(file_path))
                
                return FileResponse(
                    file_path,
                    media_type=mime_type,
                    headers={
                        "Cache-Control": "public, max-age=3600",
                        "Accept-Ranges": "bytes"  # 支持视频流式传输
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取壁纸失败: {e}")
                raise HTTPException(status_code=500, detail="获取壁纸失败")

        @self.router.delete("/wallpaper", summary="删除壁纸")
        async def delete_wallpaper(_=VerifiedDep):
            """
            删除当前壁纸
            """
            try:
                files = list(WALLPAPER_DIR.glob("current_wallpaper*"))
                for f in files:
                    f.unlink()
                
                return {"success": True, "message": "壁纸已删除"}
            except Exception as e:
                logger.error(f"删除壁纸失败: {e}")
                return {"success": False, "message": str(e)}
