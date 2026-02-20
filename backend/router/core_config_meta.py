"""Core 配置 Schema 元数据

存放所有静态映射数据，与路由逻辑分离，方便单独维护。
"""

# ==================== Section 图标 ====================

SECTION_ICONS: dict[str, str] = {
    "bot":          "lucide:bot",
    "chat":         "lucide:message-circle",
    "personality":  "lucide:heart",
    "database":     "lucide:database",
    "permissions":  "lucide:shield",
    "http_router":  "lucide:server",
    "advanced":     "lucide:settings",
}

# ==================== 中文名称映射 ====================

SECTION_NAMES_CN: dict[str, str] = {
    "bot":          "Bot 基础",
    "chat":         "聊天",
    "personality":  "人格",
    "database":     "数据库",
    "permissions":  "权限",
    "http_router":  "HTTP 路由",
    "advanced":     "高级",
}

FIELD_NAMES_CN: dict[str, str] = {
    # bot
    "ui_level":                         "UI 详细等级",
    "ui_refresh_interval":              "仪表盘刷新间隔",
    "plugins_dir":                      "插件目录",
    "logs_dir":                         "日志目录",
    "log_level":                        "日志级别",
    "data_dir":                         "数据目录",
    "shutdown_timeout":                 "优雅关闭超时",
    "force_shutdown_after":             "强制关闭等待",
    "llm_preflight_check":              "LLM 预检",
    "llm_preflight_timeout":            "LLM 预检超时",
    "tick_interval":                    "主循环间隔",
    # chat
    "default_chat_mode":                "默认聊天模式",
    "max_context_size":                 "最大上下文条数",
    # personality
    "nickname":                         "Bot 昵称",
    "alias_names":                      "别名列表",
    "personality_core":                 "核心人格",
    "personality_side":                 "人格侧面",
    "identity":                         "身份特征",
    "background_story":                 "背景故事",
    "reply_style":                      "表达风格",
    "safety_guidelines":                "安全底线",
    # database
    "database_type":                    "数据库类型",
    "sqlite_path":                      "SQLite 路径",
    "postgresql_host":                  "PG 服务器地址",
    "postgresql_port":                  "PG 服务器端口",
    "postgresql_database":              "PG 数据库名",
    "postgresql_user":                  "PG 用户名",
    "postgresql_password":              "PG 密码",
    "postgresql_schema":                "PG Schema",
    "postgresql_ssl_mode":              "SSL 模式",
    "postgresql_ssl_ca":                "SSL CA 证书",
    "postgresql_ssl_cert":              "SSL 客户端证书",
    "postgresql_ssl_key":               "SSL 客户端密钥",
    "connection_pool_size":             "连接池大小",
    "connection_timeout":               "连接超时",
    "echo":                             "打印 SQL",
    # permissions
    "owner_list":                       "所有者列表",
    "default_permission_level":         "默认权限级别",
    "allow_operator_promotion":         "允许 OP 提升权限",
    "allow_operator_demotion":          "允许 OP 降低权限",
    "max_operator_promotion_level":     "OP 可提升上限",
    "allow_command_override":           "允许命令权限覆盖",
    "override_requires_owner_approval": "覆盖需 Owner 批准",
    "enable_permission_cache":          "启用权限缓存",
    "permission_cache_ttl":             "权限缓存时效",
    "strict_mode":                      "严格模式",
    "log_permission_denied":            "记录权限拒绝",
    "log_permission_granted":           "记录权限通过",
    # http_router
    "enable_http_router":               "启用 HTTP 路由",
    "http_router_host":                 "监听地址",
    "http_router_port":                 "监听端口",
    "api_keys":                         "API 密钥列表",
    # advanced
    "force_sync_http":                  "强制同步 HTTP",
    "trust_env":                        "信任系统代理",
}

# ==================== 特殊渲染规则 ====================

# 使用高文本框（tall textarea）的字段
TEXTAREA_TALL_FIELDS: frozenset[str] = frozenset({
    "personality_core",
    "personality_side",
    "identity",
    "background_story",
    "reply_style",
})

# 使用 Select 下拉组件的字段及其选项
SELECT_FIELD_OPTIONS: dict[str, list[dict]] = {
    "ui_level": [
        {"value": "minimal",  "label": "minimal  — 最简"},
        {"value": "standard", "label": "standard — 标准"},
        {"value": "verbose",  "label": "verbose  — 详细"},
    ],
    "log_level": [
        {"value": "DEBUG",    "label": "DEBUG    — 调试"},
        {"value": "INFO",     "label": "INFO     — 信息"},
        {"value": "WARNING",  "label": "WARNING  — 警告"},
        {"value": "ERROR",    "label": "ERROR    — 错误"},
        {"value": "CRITICAL", "label": "CRITICAL — 严重"},
    ],
    "default_chat_mode": [
        {"value": "focus",     "label": "focus    — 专注"},
        {"value": "normal",    "label": "normal   — 普通"},
        {"value": "proactive", "label": "proactive— 主动"},
        {"value": "priority",  "label": "priority — 优先"},
    ],
    "database_type": [
        {"value": "sqlite",     "label": "SQLite"},
        {"value": "postgresql", "label": "PostgreSQL"},
    ],
    "default_permission_level": [
        {"value": "owner",    "label": "owner    — 所有者"},
        {"value": "operator", "label": "operator — 管理员"},
        {"value": "user",     "label": "user     — 用户"},
        {"value": "guest",    "label": "guest    — 访客"},
    ],
    "max_operator_promotion_level": [
        {"value": "operator", "label": "operator — 管理员"},
        {"value": "user",     "label": "user     — 用户"},
    ],
    "postgresql_ssl_mode": [
        {"value": "disable",     "label": "disable"},
        {"value": "allow",       "label": "allow"},
        {"value": "prefer",      "label": "prefer"},
        {"value": "require",     "label": "require"},
        {"value": "verify-ca",   "label": "verify-ca"},
        {"value": "verify-full", "label": "verify-full"},
    ],
}

# 使用自定义特殊编辑器组件的字段
# key: field_name → value: specialEditor 标识字符串
SPECIAL_EDITOR_FIELDS: dict[str, str] = {
    "owner_list": "owner_list",
    "api_keys":   "string_array",
    "alias_names": "string_array",
    "safety_guidelines": "string_array",
}
