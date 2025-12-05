from src.plugin_system.base.plugin_metadata import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="WebUI Auth Plugin",
    description="提供WebUI前端登录验证功能的插件，包含固定端口发现服务和API Key验证接口",
    usage="该插件在系统启动时自动启动发现服务器(端口12138)，前端通过此服务获取主程序IP和端口，然后使用API Key进行登录验证",
    version="1.0.0",
    author="MoFox Team",
    license="MIT",
    repository_url="https://github.com/MoFox-Studio",
    keywords=["webui", "auth", "login", "api", "authentication"],
    categories=["系统", "认证", "WebUI"],
    extra={
        "is_built_in": False,
        "plugin_type": "system",
    },
)