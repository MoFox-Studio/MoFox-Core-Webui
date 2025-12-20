/**
 * 配置项描述文件
 * 基于 bot_config_template.toml 和 model_config_template.toml
 * 提供配置项的中文名称、描述和分组信息
 */

// 配置字段类型
export type FieldType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'password' | 'select' | 'textarea' 

// 配置字段类型扩展
export type SpecialEditorType = 'master_users' | 'expression_rules' | 'reaction_rules' | 'model_extra_params' | 'web_search_engines' | 'chat_list'

// 配置字段定义
export interface ConfigFieldDef {
  key: string              // 配置键名
  name: string             // 显示名称
  description: string      // 详细描述
  type: FieldType          // 字段类型
  default?: unknown        // 默认值
  placeholder?: string     // 占位符
  options?: { value: string; label: string }[]  // 选项（用于 select 类型）
  min?: number             // 最小值（用于 number 类型）
  max?: number             // 最大值（用于 number 类型）
  step?: number            // 步进值（用于 number 类型）
  advanced?: boolean       // 是否为高级选项（显示高级选项时显示）
  expert?: boolean         // 是否为专家选项（需要打勾专家模式才显示）
  specialEditor?: SpecialEditorType  // 特殊编辑器类型
  hidden?: boolean         // 是否隐藏（由特殊编辑器管理）
  readonly?: boolean       // 是否只读（不允许修改）
}

// 配置分组定义
export interface ConfigGroupDef {
  key: string              // 分组键名
  name: string             // 分组名称
  icon: string             // 图标
  description: string      // 分组描述
  fields: ConfigFieldDef[] // 字段列表
  expert?: boolean         // 整个分组是否为专家模式（需要打勾专家模式才显示）
  hasSpecialEditor?: boolean  // 是否包含特殊编辑器
  hidden?: boolean         // 是否隐藏（由特殊编辑器管理）
}

// ==================== Bot 配置描述 ====================

export const botConfigGroups: ConfigGroupDef[] = [
  // 内部配置（版本信息）
  {
    key: 'inner',
    name: '版本信息',
    icon: 'lucide:info',
    description: '配置文件版本信息（只读）',
    fields: [
      {
        key: 'inner.version',
        name: '配置版本',
        description: '配置文件版本号，格式：主版本号.次版本号.修订号',
        type: 'string',
        readonly: true,
        placeholder: '例如: 7.9.6',
      }
    ]
  },

  // 机器人基础配置
  {
    key: 'bot',
    name: '机器人基础配置',
    icon: 'lucide:bot',
    description: '配置机器人的基本信息和身份',
    fields: [
      {
        key: 'bot.platform',
        name: '平台',
        description: '机器人运行的平台类型',
        type: 'select',
        default: 'qq',
        options: [
          { value: 'qq', label: 'QQ' },
          { value: 'telegram', label: 'Telegram' },
          { value: 'discord', label: 'Discord' }
        ]
      },
      {
        key: 'bot.qq_account',
        name: 'QQ 账号',
        description: 'MoFox-Bot 的 QQ 账号，用于登录和消息收发',
        type: 'number',
        placeholder: '例如: 1145141919810'
      },
      {
        key: 'bot.nickname',
        name: '昵称',
        description: '机器人的昵称，用户可以通过这个名字称呼机器人',
        type: 'string',
        default: '墨狐',
        placeholder: '例如: 墨狐'
      },
      {
        key: 'bot.alias_names',
        name: '别名',
        description: '机器人的其他称呼，用户也可以通过这些名字与机器人互动',
        type: 'array',
        default: [],
        placeholder: '例如: 狐狐, 墨墨'
      }
    ]
  },

  // 命令配置
  {
    key: 'command',
    name: '命令配置',
    icon: 'lucide:terminal',
    description: '配置命令触发方式',
    fields: [
      {
        key: 'command.command_prefixes',
        name: '命令前缀',
        description: '触发命令的前缀字符，可以配置多个',
        type: 'array',
        default: ['/'],
        placeholder: '例如: /, !, #'
      }
    ]
  },

  // 人格配置
  {
    key: 'personality',
    name: '人格配置',
    icon: 'lucide:heart',
    description: '配置机器人的性格特点和身份设定',
    fields: [
      {
        key: 'personality.personality_core',
        name: '核心人格',
        description: '描述人格的核心特质，建议50字以内',
        type: 'textarea',
        default: '是一个积极向上的女大学生',
        placeholder: '例如: 是一个积极向上的女大学生'
      },
      {
        key: 'personality.personality_side',
        name: '人格侧面',
        description: '描述人格的一些侧面特质，可以用一句话或几句话',
        type: 'textarea',
        placeholder: '用一句话或几句话描述人格的侧面特质'
      },
      {
        key: 'personality.identity',
        name: '身份设定',
        description: '描述外貌、性别、身高、职业、属性等',
        type: 'textarea',
        default: '年龄为19岁,是女孩子,身高为160cm,有黑色的短发',
        placeholder: '例如: 年龄为19岁,是女孩子,身高为160cm'
      },
      {
        key: 'personality.background_story',
        name: '背景故事',
        description: '详细的世界观、背景故事、复杂人际关系等。机器人不会主动复述这些设定',
        type: 'textarea',
        placeholder: '填写详细的世界观、背景故事等'
      },
      {
        key: 'personality.reply_style',
        name: '回复风格',
        description: '描述机器人说话的表达风格和表达习惯',
        type: 'textarea',
        default: '回复可以简短一些。可以参考贴吧，知乎和微博的回复风格，回复不要浮夸，不要用夸张修辞，平淡一些。',
        placeholder: '描述回复风格...'
      },
      {
        key: 'personality.safety_guidelines',
        name: '互动规则',
        description: '机器人在任何情况下都必须遵守的原则',
        type: 'array',
        placeholder: '添加互动准则...'
      },
      {
        key: 'personality.compress_personality',
        name: '压缩人格',
        description: '开启后会精简人格信息，节省 token 消耗并提高回复性能，但会丢失一些信息',
        type: 'boolean',
        default: false
      },
      {
        key: 'personality.compress_identity',
        name: '压缩身份',
        description: '开启后会精简身份信息，节省 token 消耗并提高回复性能，但会丢失一些信息',
        type: 'boolean',
        default: false
      }
    ]
  },

  // 聊天设置
  {
    key: 'chat',
    name: '聊天设置',
    icon: 'lucide:message-circle',
    description: '机器人的聊天通用设置',
    fields: [
      {
        key: 'chat.allow_reply_self',
        name: '允许回复自己',
        description: '是否允许回复自己说的话',
        type: 'boolean',
        default: false
      },
      {
        key: 'chat.private_chat_inevitable_reply',
        name: '私聊必然回复',
        description: '私聊消息是否必然回复',
        type: 'boolean',
        default: false
      },
      {
        key: 'chat.max_context_size',
        name: '上下文长度',
        description: '对话时保留的历史消息数量',
        type: 'number',
        default: 25,
        min: 1,
        max: 100
      },
      {
        key: 'chat.thinking_timeout',
        name: '思考超时时间',
        description: '一次回复最长思考规划时间（秒），超过这个时间的思考会放弃',
        type: 'number',
        default: 60,
        min: 10,
        max: 300
      },
      {
        key: 'chat.enable_message_cache',
        name: '启用消息缓存',
        description: '启用后，处理中收到的消息会被缓存，处理完成后统一刷新到未读列表',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'chat.interruption_enabled',
        name: '启用消息打断',
        description: '是否启用消息打断系统',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'chat.allow_reply_interruption',
        name: '允许回复打断',
        description: '是否允许在正在生成回复时打断',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'chat.interruption_max_limit',
        name: '最大打断次数',
        description: '每个聊天流的最大打断次数',
        type: 'number',
        default: 5,
        min: 1,
        max: 20,
        advanced: true
      },
      {
        key: 'chat.interruption_min_probability',
        name: '最低打断概率',
        description: '最低打断概率（反比例函数趋近的下限值）',
        type: 'number',
        default: 0.05,
        min: 0,
        max: 1,
        step: 0.01,
        advanced: true
      },
      {
        key: 'chat.dynamic_distribution_enabled',
        name: '动态消息分发',
        description: '是否启用动态消息分发周期调整',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'chat.dynamic_distribution_base_interval',
        name: '基础分发间隔',
        description: '基础分发间隔（秒）',
        type: 'number',
        default: 5.0,
        min: 1,
        max: 60,
        step: 0.5,
        advanced: true
      },
      {
        key: 'chat.dynamic_distribution_min_interval',
        name: '最小分发间隔',
        description: '最小分发间隔（秒）',
        type: 'number',
        default: 1.0,
        min: 0.1,
        max: 10,
        step: 0.1,
        advanced: true
      },
      {
        key: 'chat.dynamic_distribution_max_interval',
        name: '最大分发间隔',
        description: '最大分发间隔（秒）',
        type: 'number',
        default: 30.0,
        min: 10,
        max: 120,
        step: 1,
        advanced: true
      },
      {
        key: 'chat.dynamic_distribution_jitter_factor',
        name: '分发扰动因子',
        description: '分发间隔随机扰动因子',
        type: 'number',
        default: 0.2,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'chat.max_concurrent_distributions',
        name: '最大并发数',
        description: '最大并发处理的消息流数量',
        type: 'number',
        default: 10,
        min: 1,
        max: 50,
        advanced: true
      },
      {
        key: 'chat.enable_decision_history',
        name: '启用决策历史',
        description: '是否启用决策历史功能',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'chat.decision_history_length',
        name: '决策历史长度',
        description: '决策历史记录的长度，用于增强上下文连续性',
        type: 'number',
        default: 3,
        min: 1,
        max: 10,
        advanced: true
      },
      {
        key: 'chat.enable_multiple_replies',
        name: '允许多重回复',
        description: '是否允许多个回复动作',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'chat.multiple_replies_strategy',
        name: '多重回复策略',
        description: '多重回复处理策略',
        type: 'select',
        default: 'keep_first',
        options: [
          { value: 'keep_first', label: '保留第一个' },
          { value: 'keep_best', label: '保留最佳' },
          { value: 'keep_last', label: '保留最后一个' }
        ],
        advanced: true
      },
      {
        key: 'chat.allow_reply_to_emoji',
        name: '允许回复表情包',
        description: '是否允许回复表情包消息',
        type: 'boolean',
        default: false
      }
    ]
  },

  // 消息接收配置
  {
    key: 'message_receive',
    name: '消息接收',
    icon: 'lucide:inbox',
    description: '消息过滤和静默配置',
    fields: [
      {
        key: 'message_receive.ban_words',
        name: '屏蔽词',
        description: '包含这些词的消息将被过滤，不会被机器人读取',
        type: 'array',
        placeholder: '添加屏蔽词...'
      },
      {
        key: 'message_receive.ban_msgs_regex',
        name: '屏蔽正则',
        description: '符合这些正则表达式的消息将被过滤',
        type: 'array',
        placeholder: '添加正则表达式...',
        advanced: true
      },
      {
        key: 'message_receive.mute_group_list',
        name: '静默群组',
        description: '在这些群组中，只有被 @ 或回复时才会响应',
        type: 'array',
        placeholder: '添加群号...'
      }
    ]
  },

  // 数据库配置
  {
    key: 'database',
    name: '数据库配置',
    icon: 'lucide:database',
    description: '配置数据存储方式',
    fields: [
      {
        key: 'database.database_type',
        name: '数据库类型',
        description: '选择使用的数据库类型',
        type: 'select',
        default: 'sqlite',
        options: [
          { value: 'sqlite', label: 'SQLite（轻量级，推荐）' },
          { value: 'postgresql', label: 'PostgreSQL（高性能）' }
        ]
      },
      {
        key: 'database.sqlite_path',
        name: 'SQLite 路径',
        description: 'SQLite 数据库文件路径',
        type: 'string',
        default: 'data/MaiBot.db',
        placeholder: '例如: data/MaiBot.db'
      },
      {
        key: 'database.postgresql_host',
        name: 'PostgreSQL 主机',
        description: 'PostgreSQL 服务器地址',
        type: 'string',
        default: 'localhost',
        advanced: true
      },
      {
        key: 'database.postgresql_port',
        name: 'PostgreSQL 端口',
        description: 'PostgreSQL 服务器端口',
        type: 'number',
        default: 5432,
        advanced: true
      },
      {
        key: 'database.postgresql_database',
        name: '数据库名',
        description: 'PostgreSQL 数据库名',
        type: 'string',
        default: 'maibot',
        advanced: true
      },
      {
        key: 'database.postgresql_user',
        name: '用户名',
        description: 'PostgreSQL 用户名',
        type: 'string',
        default: 'postgres',
        advanced: true
      },
      {
        key: 'database.postgresql_password',
        name: '密码',
        description: 'PostgreSQL 密码',
        type: 'password',
        advanced: true
      },
      {
        key: 'database.postgresql_schema',
        name: 'PostgreSQL 模式名',
        description: 'PostgreSQL 模式名（schema）',
        type: 'string',
        default: 'public',
        advanced: true
      },
      {
        key: 'database.postgresql_ssl_mode',
        name: 'PostgreSQL SSL 模式',
        description: 'SSL模式: disable, allow, prefer, require, verify-ca, verify-full',
        type: 'select',
        default: 'prefer',
        options: [
          { value: 'disable', label: '禁用' },
          { value: 'allow', label: '允许' },
          { value: 'prefer', label: '优先使用' },
          { value: 'require', label: '必需' },
          { value: 'verify-ca', label: '验证CA' },
          { value: 'verify-full', label: '完全验证' }
        ],
        advanced: true
      },
      {
        key: 'database.postgresql_ssl_ca',
        name: 'SSL CA证书路径',
        description: 'SSL CA证书路径',
        type: 'string',
        placeholder: '/path/to/ca.pem',
        advanced: true
      },
      {
        key: 'database.postgresql_ssl_cert',
        name: 'SSL客户端证书路径',
        description: 'SSL客户端证书路径',
        type: 'string',
        placeholder: '/path/to/cert.pem',
        advanced: true
      },
      {
        key: 'database.postgresql_ssl_key',
        name: 'SSL客户端密钥路径',
        description: 'SSL客户端密钥路径',
        type: 'string',
        placeholder: '/path/to/key.pem',
        advanced: true
      },
      {
        key: 'database.connection_pool_size',
        name: '连接池大小',
        description: '数据库连接池大小（PostgreSQL 有效）',
        type: 'number',
        default: 10,
        min: 1,
        max: 100,
        advanced: true
      },
      {
        key: 'database.connection_timeout',
        name: '连接超时时间',
        description: '数据库连接超时时间（秒）',
        type: 'number',
        default: 10,
        min: 1,
        max: 120,
        advanced: true
      },
      {
        key: 'database.batch_action_storage_enabled',
        name: '批量动作记录存储',
        description: '启用后将多个动作一次性写入数据库，提升性能',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'database.enable_database_cache',
        name: '启用数据库缓存',
        description: '启用数据库查询缓存系统，防止内存溢出',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'database.cache_l1_max_size',
        name: 'L1缓存最大条目数',
        description: 'L1缓存最大条目数（热数据，内存占用约1-5MB）',
        type: 'number',
        default: 1000,
        min: 100,
        max: 10000,
        advanced: true
      },
      {
        key: 'database.cache_l1_ttl',
        name: 'L1缓存生存时间',
        description: 'L1缓存生存时间（秒）',
        type: 'number',
        default: 300,
        min: 60,
        max: 3600,
        advanced: true
      },
      {
        key: 'database.cache_l2_max_size',
        name: 'L2缓存最大条目数',
        description: 'L2缓存最大条目数（温数据，内存占用约10-50MB）',
        type: 'number',
        default: 10000,
        min: 1000,
        max: 100000,
        advanced: true
      },
      {
        key: 'database.cache_l2_ttl',
        name: 'L2缓存生存时间',
        description: 'L2缓存生存时间（秒）',
        type: 'number',
        default: 1800,
        min: 300,
        max: 7200,
        advanced: true
      },
      {
        key: 'database.cache_cleanup_interval',
        name: '缓存清理间隔',
        description: '缓存清理任务执行间隔（秒）',
        type: 'number',
        default: 60,
        min: 10,
        max: 600,
        advanced: true
      },
      {
        key: 'database.cache_max_memory_mb',
        name: '缓存最大内存占用',
        description: '缓存最大内存占用（MB），超过此值将触发强制清理',
        type: 'number',
        default: 10,
        min: 1,
        max: 100,
        advanced: true
      },
      {
        key: 'database.cache_max_item_size_mb',
        name: '单条目最大大小',
        description: '单个缓存条目最大大小（MB），超过此值将不缓存',
        type: 'number',
        default: 1,
        min: 0.1,
        max: 10,
        step: 0.1,
        advanced: true
      }
    ]
  },

  // 表情包配置
  {
    key: 'emoji',
    name: '表情包配置',
    icon: 'lucide:smile',
    description: '配置表情包收集和发送行为',
    fields: [
      {
        key: 'emoji.emoji_chance',
        name: '表情包概率',
        description: '激活表情包动作的概率（0-1）',
        type: 'number',
        default: 0.6,
        min: 0,
        max: 1,
        step: 0.1
      },
      {
        key: 'emoji.emoji_activate_type',
        name: '激活类型',
        description: '表情包激活方式',
        type: 'select',
        default: 'llm',
        options: [
          { value: 'random', label: '随机激活' },
          { value: 'llm', label: 'AI 判断激活' }
        ]
      },
      {
        key: 'emoji.max_reg_num',
        name: '最大收集数量',
        description: '表情包最大注册数量',
        type: 'number',
        default: 60,
        min: 10,
        max: 500
      },
      {
        key: 'emoji.do_replace',
        name: '替换表情包',
        description: '开启则在达到最大数量时删除（替换）表情包',
        type: 'boolean',
        default: true
      },
      {
        key: 'emoji.check_interval',
        name: '检查间隔',
        description: '检查表情包（注册，破损，删除）的时间间隔（分钟）',
        type: 'number',
        default: 10,
        min: 1,
        max: 60
      },
      {
        key: 'emoji.steal_emoji',
        name: '偷取表情包',
        description: '是否偷取表情包，让机器人可以将一些表情包据为己有',
        type: 'boolean',
        default: true
      },
      {
        key: 'emoji.content_filtration',
        name: '内容过滤',
        description: '是否启用表情包过滤，只有符合要求的表情包才会被保存',
        type: 'boolean',
        default: false
      },
      {
        key: 'emoji.filtration_prompt',
        name: '过滤要求',
        description: '表情包过滤要求，只有符合该要求的表情包才会被保存',
        type: 'string',
        default: '符合公序良俗',
        placeholder: '例如: 符合公序良俗'
      },
      {
        key: 'emoji.enable_emotion_analysis',
        name: '情感分析',
        description: '启用表情包感情关键词二次识别',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'emoji.emoji_selection_mode',
        name: '选择模式',
        description: '表情选择模式',
        type: 'select',
        default: 'emotion',
        options: [
          { value: 'emotion', label: '情感标签' },
          { value: 'description', label: '详细描述' }
        ],
        advanced: true
      },
      {
        key: 'emoji.max_context_emojis',
        name: '上下文表情包数量',
        description: '每次随机传递给LLM的表情包详细描述的最大数量，0为全部',
        type: 'number',
        default: 30,
        min: 0,
        max: 100,
        advanced: true
      }
    ]
  },

  // 记忆系统配置
  {
    key: 'memory',
    name: '记忆系统',
    icon: 'lucide:brain',
    description: '基于知识图谱 + 语义向量的混合记忆架构',
    fields: [
      {
        key: 'memory.enable',
        name: '启用记忆系统',
        description: '是否启用记忆系统',
        type: 'boolean',
        default: true
      },
      {
        key: 'memory.data_dir',
        name: '数据目录',
        description: '记忆数据存储目录',
        type: 'string',
        default: 'data/memory_graph'
      },
      {
        key: 'memory.search_top_k',
        name: '检索数量',
        description: '默认检索返回数量',
        type: 'number',
        default: 10,
        min: 1,
        max: 50
      },
      {
        key: 'memory.search_min_importance',
        name: '最小重要性',
        description: '最小重要性阈值（0.0-1.0）',
        type: 'number',
        default: 0.4,
        min: 0,
        max: 1,
        step: 0.1
      },
      {
        key: 'memory.search_similarity_threshold',
        name: '相似度阈值',
        description: '向量相似度阈值',
        type: 'number',
        default: 0.6,
        min: 0,
        max: 1,
        step: 0.1
      },
      {
        key: 'memory.enable_query_optimization',
        name: '查询优化',
        description: '启用查询优化（使用小模型分析对话历史，生成综合性搜索查询）',
        type: 'boolean',
        default: true
      },
      {
        key: 'memory.enable_path_expansion',
        name: '路径扩展',
        description: '启用路径评分扩展算法，通过路径传播和分数聚合来发现相关记忆',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'memory.forgetting_enabled',
        name: '自动遗忘',
        description: '是否启用自动遗忘机制',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'memory.vector_collection_name',
        name: '向量集合名称',
        description: '向量集合名称',
        type: 'string',
        default: 'memory_nodes',
        advanced: true
      },
      {
        key: 'memory.vector_db_path',
        name: '向量数据库路径',
        description: '向量数据库路径（使用独立的chromadb实例）',
        type: 'string',
        default: 'data/memory_graph/chroma_db',
        advanced: true
      },
      {
        key: 'memory.path_expansion_max_hops',
        name: '路径扩展最大跳数',
        description: '路径扩展最大跳数（建议1-3）',
        type: 'number',
        default: 2,
        min: 1,
        max: 5,
        advanced: true
      },
      {
        key: 'memory.path_expansion_damping_factor',
        name: '路径分数衰减因子',
        description: '路径分数衰减因子（PageRank风格，0.85推荐）',
        type: 'number',
        default: 0.85,
        min: 0.5,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.enable_memory_deduplication',
        name: '记忆去重',
        description: '启用检索结果去重（合并相似记忆）',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'memory.memory_deduplication_threshold',
        name: '记忆去重阈值',
        description: '记忆相似度阈值（0.85表示85%相似即合并）',
        type: 'number',
        default: 0.85,
        min: 0.5,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.forgetting_activation_threshold',
        name: '激活度阈值',
        description: '激活度阈值（低于此值的记忆会被遗忘）',
        type: 'number',
        default: 0.1,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.forgetting_min_importance',
        name: '最小保护重要性',
        description: '最小保护重要性（高于此值的记忆不会被遗忘）',
        type: 'number',
        default: 0.8,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.activation_decay_rate',
        name: '激活度衰减率',
        description: '激活度衰减率（每天衰减10%）',
        type: 'number',
        default: 0.9,
        min: 0.5,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.perceptual_max_blocks',
        name: '感知记忆最大容量',
        description: '记忆堆最大容量（全局）',
        type: 'number',
        default: 50,
        min: 10,
        max: 200,
        advanced: true
      },
      {
        key: 'memory.perceptual_block_size',
        name: '记忆块消息数',
        description: '每个记忆块包含的消息数量',
        type: 'number',
        default: 5,
        min: 1,
        max: 20,
        advanced: true
      },
      {
        key: 'memory.short_term_max_memories',
        name: '短期记忆最大数量',
        description: '短期记忆最大数量',
        type: 'number',
        default: 30,
        min: 10,
        max: 100,
        advanced: true
      },
      {
        key: 'memory.short_term_transfer_threshold',
        name: '短期转移阈值',
        description: '转移到长期记忆的重要性阈值',
        type: 'number',
        default: 0.6,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.long_term_auto_transfer_interval',
        name: '自动转移间隔',
        description: '自动转移间隔（秒）',
        type: 'number',
        default: 180,
        min: 60,
        max: 600,
        advanced: true
      },
      {
        key: 'memory.path_expansion_max_branches',
        name: '每节点最大分叉数',
        description: '每节点最大分叉数（控制探索广度）',
        type: 'number',
        default: 10,
        min: 1,
        max: 50,
        advanced: true
      },
      {
        key: 'memory.path_expansion_merge_strategy',
        name: '路径合并策略',
        description: '路径合并策略',
        type: 'select',
        default: 'weighted_geometric',
        options: [
          { value: 'weighted_geometric', label: '加权几何平均' },
          { value: 'max_bonus', label: '最大值加成' }
        ],
        advanced: true
      },
      {
        key: 'memory.path_expansion_pruning_threshold',
        name: '路径剪枝阈值',
        description: '路径剪枝阈值（新路径分数需达到已有路径的百分比）',
        type: 'number',
        default: 0.9,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.path_expansion_path_score_weight',
        name: '路径分数权重',
        description: '路径分数在最终评分中的权重',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.path_expansion_importance_weight',
        name: '重要性权重',
        description: '重要性在最终评分中的权重',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.path_expansion_recency_weight',
        name: '时效性权重',
        description: '时效性在最终评分中的权重',
        type: 'number',
        default: 0.2,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.activation_propagation_strength',
        name: '激活传播强度',
        description: '激活传播强度（传播到相关记忆的激活度比例）',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'memory.activation_propagation_depth',
        name: '激活传播深度',
        description: '激活传播深度（最多传播几层，建议1-2）',
        type: 'number',
        default: 1,
        min: 1,
        max: 5,
        advanced: true
      },
      {
        key: 'memory.auto_activate_base_strength',
        name: '自动激活基础强度',
        description: '记忆被检索时自动激活的基础强度',
        type: 'number',
        default: 0.1,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.auto_activate_max_count',
        name: '自动激活最大数量',
        description: '单次搜索最多自动激活的记忆数量',
        type: 'number',
        default: 10,
        min: 1,
        max: 50,
        advanced: true
      },
      {
        key: 'memory.perceptual_similarity_threshold',
        name: '感知相似度阈值',
        description: '感知记忆相似度阈值（0-1）',
        type: 'number',
        default: 0.55,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.perceptual_topk',
        name: '感知TopK召回',
        description: '感知记忆TopK召回数量',
        type: 'number',
        default: 3,
        min: 1,
        max: 20,
        advanced: true
      },
      {
        key: 'memory.perceptual_activation_threshold',
        name: '感知激活阈值',
        description: '激活阈值（召回次数→短期）',
        type: 'number',
        default: 3,
        min: 1,
        max: 10,
        advanced: true
      },
      {
        key: 'memory.short_term_search_top_k',
        name: '短期记忆搜索TopK',
        description: '短期记忆搜索时返回的最大数量',
        type: 'number',
        default: 5,
        min: 1,
        max: 20,
        advanced: true
      },
      {
        key: 'memory.short_term_decay_factor',
        name: '短期衰减因子',
        description: '短期记忆衰减因子',
        type: 'number',
        default: 0.98,
        min: 0.9,
        max: 1,
        step: 0.01,
        advanced: true
      },
      {
        key: 'memory.long_term_batch_size',
        name: '长期批量转移大小',
        description: '长期记忆批量转移大小',
        type: 'number',
        default: 10,
        min: 1,
        max: 50,
        advanced: true
      },
      {
        key: 'memory.long_term_decay_factor',
        name: '长期衰减因子',
        description: '长期记忆衰减因子',
        type: 'number',
        default: 0.95,
        min: 0.8,
        max: 1,
        step: 0.01,
        advanced: true
      },
      {
        key: 'memory.node_merger_similarity_threshold',
        name: '节点去重相似度阈值',
        description: '节点去重相似度阈值',
        type: 'number',
        default: 0.85,
        min: 0.5,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'memory.node_merger_context_match_required',
        name: '节点合并要求上下文匹配',
        description: '节点合并是否要求上下文匹配',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'memory.node_merger_merge_batch_size',
        name: '节点合并批量大小',
        description: '节点合并批量处理大小',
        type: 'number',
        default: 50,
        min: 10,
        max: 200,
        advanced: true
      },
      {
        key: 'memory.max_memory_nodes_per_memory',
        name: '每条记忆最大节点数',
        description: '每条记忆最多包含的节点数',
        type: 'number',
        default: 10,
        min: 1,
        max: 50,
        advanced: true
      },
      {
        key: 'memory.max_related_memories',
        name: '最大相关记忆数',
        description: '激活传播时最多影响的相关记忆数',
        type: 'number',
        default: 5,
        min: 1,
        max: 20,
        advanced: true
      }
    ]
  },

  // 情绪系统
  {
    key: 'mood',
    name: '情绪系统',
    icon: 'lucide:heart-pulse',
    description: '配置机器人的情绪变化',
    fields: [
      {
        key: 'mood.enable_mood',
        name: '启用情绪系统',
        description: '是否启用情绪系统',
        type: 'boolean',
        default: true
      },
      {
        key: 'mood.mood_update_threshold',
        name: '更新阈值',
        description: '情绪更新阈值，越高更新越慢',
        type: 'number',
        default: 1,
        min: 1,
        max: 10
      }
    ]
  },

  // 工具配置
  {
    key: 'tool',
    name: '工具配置',
    icon: 'lucide:wrench',
    description: '配置机器人可用的工具',
    fields: [
      {
        key: 'tool.enable_tool',
        name: '启用工具',
        description: '是否在普通聊天中启用工具',
        type: 'boolean',
        default: true
      }
    ]
  },

  // 语音配置
  {
    key: 'voice',
    name: '语音配置',
    icon: 'lucide:mic',
    description: '配置语音识别功能',
    fields: [
      {
        key: 'voice.enable_asr',
        name: '启用语音识别',
        description: '启用后机器人可以识别语音消息，需要配置语音识别模型',
        type: 'boolean',
        default: true
      },
      {
        key: 'voice.asr_provider',
        name: '识别提供商',
        description: '语音识别提供商',
        type: 'select',
        default: 'api',
        options: [
          { value: 'api', label: 'API（推荐）' },
          { value: 'local', label: '本地（消耗大量CPU）' }
        ]
      }
    ]
  },

  // 网络搜索配置
  {
    key: 'web_search',
    name: '网络搜索',
    icon: 'lucide:search',
    description: '配置联网搜索功能，支持多种搜索引擎',
    hasSpecialEditor: true,
    fields: [
      {
        key: 'web_search.enable_web_search_tool',
        name: '启用联网搜索',
        description: '是否启用联网搜索工具，允许机器人在需要时搜索网络信息',
        type: 'boolean',
        default: true
      },
      {
        key: 'web_search.enable_url_tool',
        name: '启用 URL 解析',
        description: '是否启用 URL 解析工具，允许机器人解析和获取网页内容',
        type: 'boolean',
        default: true
      },
      {
        key: 'web_search.enabled_engines',
        name: '启用的搜索引擎',
        description: '选择要启用的搜索引擎',
        type: 'array',
        default: ['ddg'],
        specialEditor: 'web_search_engines'
      },
      {
        key: 'web_search.search_strategy',
        name: '搜索策略',
        description: '多引擎搜索时的执行策略',
        type: 'select',
        default: 'single',
        options: [
          { value: 'single', label: '单引擎（使用第一个可用引擎）' },
          { value: 'parallel', label: '并行（同时使用所有启用的引擎）' },
          { value: 'fallback', label: '降级（按顺序尝试，失败则下一个）' }
        ]
      },
      {
        key: 'web_search.tavily_api_keys',
        name: 'Tavily API 密钥',
        description: 'Tavily搜索引擎API密钥列表，支持多密钥轮询',
        type: 'array',
        hidden: true,
        placeholder: '添加Tavily API密钥...'
      },
      {
        key: 'web_search.exa_api_keys',
        name: 'EXA API 密钥',
        description: 'EXA搜索引擎API密钥列表，支持多密钥轮询',
        type: 'array',
        hidden: true,
        placeholder: '添加EXA API密钥...'
      },
      {
        key: 'web_search.metaso_api_keys',
        name: 'Metaso API 密钥',
        description: 'Metaso搜索引擎API密钥列表，支持多密钥轮询',
        type: 'array',
        hidden: true,
        placeholder: '添加Metaso API密钥...'
      },
      {
        key: 'web_search.serper_api_keys',
        name: 'Serper API 密钥',
        description: 'Serper搜索引擎API密钥列表，支持多密钥轮询',
        type: 'array',
        hidden: true,
        placeholder: '添加Serper API密钥...'
      },
      {
        key: 'web_search.searxng_instances',
        name: 'SearXNG 实例',
        description: 'SearXNG实例URL列表',
        type: 'array',
        hidden: true,
        placeholder: '添加SearXNG实例URL...'
      },
      {
        key: 'web_search.searxng_api_keys',
        name: 'SearXNG API 密钥',
        description: 'SearXNG实例API密钥列表',
        type: 'array',
        hidden: true,
        placeholder: '添加SearXNG API密钥...'
      }
    ]
  },

  // 视频分析配置（简单模式）
  {
    key: 'video_analysis',
    name: '视频分析',
    icon: 'lucide:video',
    description: '配置视频分析功能，高级选项请在专家模式中配置',
    fields: [
      {
        key: 'video_analysis.enable',
        name: '启用视频分析',
        description: '是否启用视频分析功能',
        type: 'boolean',
        default: true
      },
      {
        key: 'video_analysis.ffmpeg_path',
        name: 'FFmpeg 路径',
        description: 'FFmpeg可执行文件路径，用于视频处理',
        type: 'string',
        placeholder: '例如: /usr/bin/ffmpeg 或 C:/ffmpeg/bin/ffmpeg.exe'
      },
      {
        key: 'video_analysis.analysis_mode',
        name: '分析模式',
        description: '视频分析模式',
        type: 'select',
        default: 'batch_frames',
        options: [
          { value: 'frame_by_frame', label: '逐帧分析（非常慢）' },
          { value: 'batch_frames', label: '批量分析（推荐）' },
          { value: 'auto', label: '自动选择' }
        ]
      },
      {
        key: 'video_analysis.frame_extraction_mode',
        name: '抽帧模式',
        description: '视频抽帧模式',
        type: 'select',
        default: 'keyframe',
        options: [
          { value: 'keyframe', label: '智能关键帧（推荐）' },
          { value: 'fixed_number', label: '固定总帧数' },
          { value: 'time_interval', label: '按时间间隔' }
        ]
      },
      {
        key: 'video_analysis.max_frames',
        name: '最大分析帧数',
        description: '最大分析帧数',
        type: 'number',
        default: 16,
        min: 1,
        max: 100
      }
    ]
  },

  // 回复后处理
  {
    key: 'response_post_process',
    name: '回复后处理',
    icon: 'lucide:wand-2',
    description: '配置回复的后处理功能',
    fields: [
      {
        key: 'response_post_process.enable_response_post_process',
        name: '启用后处理',
        description: '是否启用回复后处理，包括错别字生成器、回复分割器',
        type: 'boolean',
        default: true
      }
    ]
  },

  // 中文错别字
  {
    key: 'chinese_typo',
    name: '中文错别字',
    icon: 'lucide:text-cursor',
    description: '让机器人偶尔打出错别字，更像真人',
    fields: [
      {
        key: 'chinese_typo.enable',
        name: '启用错别字',
        description: '是否启用中文错别字生成器',
        type: 'boolean',
        default: true
      },
      {
        key: 'chinese_typo.error_rate',
        name: '错字概率',
        description: '单字替换概率',
        type: 'number',
        default: 0.001,
        min: 0,
        max: 0.1,
        step: 0.001
      },
      {
        key: 'chinese_typo.min_freq',
        name: '最小字频阈值',
        description: '最小字频阈值',
        type: 'number',
        default: 9,
        min: 1,
        max: 100,
        advanced: true
      },
      {
        key: 'chinese_typo.tone_error_rate',
        name: '声调错误概率',
        description: '声调错误概率',
        type: 'number',
        default: 0.005,
        min: 0,
        max: 0.1,
        step: 0.001,
        advanced: true
      },
      {
        key: 'chinese_typo.word_replace_rate',
        name: '整词替换概率',
        description: '整词替换概率',
        type: 'number',
        default: 0.006,
        min: 0,
        max: 0.1,
        step: 0.001
      }
    ]
  },

  // 回复分割
  {
    key: 'response_splitter',
    name: '回复分割',
    icon: 'lucide:split',
    description: '将长回复分割成多条消息',
    fields: [
      {
        key: 'response_splitter.enable',
        name: '启用分割',
        description: '是否启用回复分割器',
        type: 'boolean',
        default: true
      },
      {
        key: 'response_splitter.split_mode',
        name: '分割模式',
        description: '回复分割模式',
        type: 'select',
        default: 'punctuation',
        options: [
          { value: 'llm', label: 'AI 决定' },
          { value: 'punctuation', label: '基于标点符号' }
        ]
      },
      {
        key: 'response_splitter.max_length',
        name: '最大长度',
        description: '回复允许的最大长度',
        type: 'number',
        default: 512,
        min: 100,
        max: 2000
      },
      {
        key: 'response_splitter.max_sentence_num',
        name: '最大句子数',
        description: '回复允许的最大句子数',
        type: 'number',
        default: 8,
        min: 1,
        max: 20
      },
      {
        key: 'response_splitter.enable_kaomoji_protection',
        name: '颜文字保护',
        description: '是否启用颜文字保护，避免颜文字被错误分割',
        type: 'boolean',
        default: true,
        advanced: true
      }
    ]
  },

  // 日志配置
  {
    key: 'log',
    name: '日志配置',
    icon: 'lucide:file-text',
    description: '配置日志输出',
    fields: [
      {
        key: 'log.log_level',
        name: '日志级别',
        description: '全局日志级别',
        type: 'select',
        default: 'INFO',
        options: [
          { value: 'DEBUG', label: 'DEBUG（调试）' },
          { value: 'INFO', label: 'INFO（信息）' },
          { value: 'WARNING', label: 'WARNING（警告）' },
          { value: 'ERROR', label: 'ERROR（错误）' },
          { value: 'CRITICAL', label: 'CRITICAL（严重）' }
        ]
      },
      {
        key: 'log.console_log_level',
        name: '控制台日志级别',
        description: '控制台输出的日志级别',
        type: 'select',
        default: 'INFO',
        options: [
          { value: 'DEBUG', label: 'DEBUG' },
          { value: 'INFO', label: 'INFO' },
          { value: 'WARNING', label: 'WARNING' },
          { value: 'ERROR', label: 'ERROR' },
          { value: 'CRITICAL', label: 'CRITICAL' }
        ]
      },
      {
        key: 'log.file_log_level',
        name: '文件日志级别',
        description: '文件输出的日志级别',
        type: 'select',
        default: 'DEBUG',
        options: [
          { value: 'DEBUG', label: 'DEBUG' },
          { value: 'INFO', label: 'INFO' },
          { value: 'WARNING', label: 'WARNING' },
          { value: 'ERROR', label: 'ERROR' },
          { value: 'CRITICAL', label: 'CRITICAL' }
        ]
      },
      {
        key: 'log.file_retention_days',
        name: '日志保留天数',
        description: '文件日志保留天数，0=禁用文件日志，-1=永不删除',
        type: 'number',
        default: 30,
        min: -1,
        max: 365
      },
      {
        key: 'log.date_style',
        name: '日期格式',
        description: '日志日期格式',
        type: 'string',
        default: 'm-d H:i:s',
        placeholder: 'm-d H:i:s',
        advanced: true
      },
      {
        key: 'log.log_level_style',
        name: '日志级别样式',
        description: '日志级别样式',
        type: 'select',
        default: 'lite',
        options: [
          { value: 'FULL', label: '完整' },
          { value: 'compact', label: '紧凑' },
          { value: 'lite', label: '精简' }
        ],
        advanced: true
      },
      {
        key: 'log.color_text',
        name: '日志文本颜色',
        description: '日志文本颜色',
        type: 'select',
        default: 'full',
        options: [
          { value: 'none', label: '无颜色' },
          { value: 'title', label: '仅标题' },
          { value: 'full', label: '全部' }
        ],
        advanced: true
      },
      {
        key: 'log.suppress_libraries',
        name: '屏蔽库列表',
        description: '完全屏蔽的第三方库日志列表',
        type: 'array',
        placeholder: '例如: faiss, httpx, urllib3',
        advanced: true
      },
      {
        key: 'log.library_log_levels',
        name: '库日志级别',
        description: '设置特定库的日志级别，格式为对象 { "库名": "日志级别" }',
        type: 'object',
        placeholder: '例如: { "aiohttp": "WARNING" }',
        advanced: true
      }
    ]
  },

  // 规划系统
  {
    key: 'planning_system',
    name: '规划系统',
    icon: 'lucide:calendar',
    description: '配置日程生成和月度计划',
    fields: [
      {
        key: 'planning_system.schedule_enable',
        name: '启用日程生成',
        description: '是否启用每日日程生成功能',
        type: 'boolean',
        default: false
      },
      {
        key: 'planning_system.schedule_guidelines',
        name: '日程指南',
        description: '日程生成的指导原则',
        type: 'textarea',
        advanced: true
      },
      {
        key: 'planning_system.monthly_plan_enable',
        name: '启用月度计划',
        description: '是否启用月度计划系统',
        type: 'boolean',
        default: false
      },
      {
        key: 'planning_system.max_plans_per_month',
        name: '每月最大计划数',
        description: '每月最多生成的计划数量',
        type: 'number',
        default: 10,
        min: 1,
        max: 50
      },
      {
        key: 'planning_system.monthly_plan_guidelines',
        name: '月度计划指南',
        description: '月度计划生成的指导原则',
        type: 'textarea',
        advanced: true
      },
      {
        key: 'planning_system.avoid_repetition_days',
        name: '避免重复天数',
        description: '避免在多少天内重复使用同一个月度计划',
        type: 'number',
        default: 7,
        min: 1,
        max: 30,
        advanced: true
      },
      {
        key: 'planning_system.completion_threshold',
        name: '完成阈值',
        description: '一个月度计划被使用多少次后算作完成',
        type: 'number',
        default: 3,
        min: 1,
        max: 10,
        advanced: true
      }
    ]
  },

  // Notice 配置
  {
    key: 'notice',
    name: 'Notice 消息',
    icon: 'lucide:bell',
    description: '配置 Notice 消息的处理方式',
    fields: [
      {
        key: 'notice.enable_notice_trigger_chat',
        name: '允许触发聊天',
        description: '是否允许 notice 消息触发聊天流程',
        type: 'boolean',
        default: false
      },
      {
        key: 'notice.notice_in_prompt',
        name: '展示在提示词中',
        description: '是否在提示词中展示最近的 notice 消息',
        type: 'boolean',
        default: true
      },
      {
        key: 'notice.notice_prompt_limit',
        name: '展示数量上限',
        description: '在提示词中展示的最大 notice 数量',
        type: 'number',
        default: 5,
        min: 1,
        max: 20
      },
      {
        key: 'notice.notice_time_window',
        name: '时间窗口',
        description: 'notice时间窗口（秒），只有这个时间范围内的notice会在提示词中展示',
        type: 'number',
        default: 1800,
        min: 60,
        max: 7200,
        advanced: true
      },
      {
        key: 'notice.max_notices_per_chat',
        name: '每个聊天保留数量',
        description: '每个聊天保留的notice数量上限',
        type: 'number',
        default: 30,
        min: 5,
        max: 100,
        advanced: true
      },
      {
        key: 'notice.notice_retention_time',
        name: '保留时间',
        description: 'notice保留时间（秒）',
        type: 'number',
        default: 3600,
        min: 300,
        max: 86400,
        advanced: true
      }
    ]
  },

  // 权限配置
  {
    key: 'permission',
    name: '权限配置',
    icon: 'lucide:shield',
    description: '配置用户权限和主人身份',
    hasSpecialEditor: true,
    fields: [
      {
        key: 'permission.master_users',
        name: '主人用户',
        description: '拥有最高权限的用户列表，无视所有权限节点。格式为二维数组: [[平台, 用户ID], ...]',
        type: 'array',
        placeholder: '例如: [["qq", "123456"]]',
        specialEditor: 'master_users'
      },
      {
        key: 'permission.master_prompt.enable',
        name: '启用主人提示',
        description: '是否启用主人/非主人提示注入',
        type: 'boolean',
        default: false
      },
      {
        key: 'permission.master_prompt.master_hint',
        name: '主人提示词',
        description: '与主人交流时的提示词',
        type: 'textarea',
        default: '你正在与自己的主人交流，注意展现亲切与尊重。'
      },
      {
        key: 'permission.master_prompt.non_master_hint',
        name: '非主人提示词',
        description: '与非主人交流时的提示词',
        type: 'textarea',
        default: '对方并非你的主人，请保持常规互动风格。'
      }
    ]
  },

  // 调试配置
  {
    key: 'debug',
    name: '调试配置',
    icon: 'lucide:bug',
    description: '开发调试相关配置',
    fields: [
      {
        key: 'debug.show_prompt',
        name: '显示提示词',
        description: '是否显示 prompt 内容，用于调试',
        type: 'boolean',
        default: false
      }
    ]
  },

  // ==================== 以下为新增配置组 ====================

  // 表达学习系统
  {
    key: 'expression',
    name: '表达学习系统',
    icon: 'lucide:sparkles',
    description: '配置机器人学习和使用表达方式的行为',
    hasSpecialEditor: true,
    fields: [
      {
        key: 'expression.mode',
        name: '表达模式',
        description: '表达方式模式选择',
        type: 'select',
        default: 'exp_model',
        options: [
          { value: 'classic', label: '经典模式（随机抽样 + LLM选择）' },
          { value: 'exp_model', label: '表达模型模式（机器学习预测）' }
        ]
      },
      {
        key: 'expression.expiration_days',
        name: '过期天数',
        description: '表达方式过期天数，超过此天数未激活的表达方式将被清理',
        type: 'number',
        default: 1,
        min: 1,
        max: 30
      },
      {
        key: 'expression.rules',
        name: '表达规则',
        description: '表达学习规则列表，可为不同聊天流配置独立的学习规则',
        type: 'array',
        specialEditor: 'expression_rules'
      }
    ]
  },

  // 反应规则系统
  {
    key: 'reaction',
    name: '反应规则系统',
    icon: 'lucide:zap',
    description: '基于关键词或正则表达式的自动回复规则',
    hasSpecialEditor: true,
    fields: [
      {
        key: 'reaction.rules',
        name: '反应规则',
        description: '自动回复规则列表，支持关键词匹配和正则表达式匹配',
        type: 'array',
        specialEditor: 'reaction_rules'
      }
    ]
  },

  // 插件HTTP端点系统
  {
    key: 'plugin_http_system',
    name: '插件HTTP端点',
    icon: 'lucide:plug',
    description: '配置插件的HTTP端点功能和安全设置',
    fields: [
      {
        key: 'plugin_http_system.enable_plugin_http_endpoints',
        name: '启用HTTP端点',
        description: '总开关，用于启用或禁用所有插件的HTTP端点功能',
        type: 'boolean',
        default: true
      },
      {
        key: 'plugin_http_system.plugin_api_rate_limit_enable',
        name: '启用速率限制',
        description: '是否为插件暴露的API启用全局速率限制',
        type: 'boolean',
        default: true
      },
      {
        key: 'plugin_http_system.plugin_api_rate_limit_default',
        name: '默认速率限制',
        description: '默认的速率限制策略，格式: "次数/时间单位"（如100/minute）',
        type: 'string',
        default: '100/minute',
        placeholder: '例如: 100/minute, 1000/hour'
      },
      {
        key: 'plugin_http_system.plugin_api_valid_keys',
        name: 'API认证密钥',
        description: '用于访问需要认证的插件API的有效密钥列表',
        type: 'array',
        placeholder: '添加API密钥...'
      }
    ]
  },

  // KFC心流聊天器
  {
    key: 'kokoro_flow_chatter',
    name: 'KFC 心流聊天器',
    icon: 'lucide:heart-handshake',
    description: '专为私聊设计的深度情感交互处理器，复用全局人设和情感框架',
    fields: [
      {
        key: 'kokoro_flow_chatter.enable',
        name: '启用KFC',
        description: '开启后KFC将接管所有私聊消息；关闭后私聊将由AFC处理',
        type: 'boolean',
        default: true
      },
      {
        key: 'kokoro_flow_chatter.mode',
        name: '工作模式',
        description: '统一模式响应更快，分离模式控制更精细',
        type: 'select',
        default: 'split',
        options: [
          { value: 'unified', label: '统一模式（单次LLM调用，响应快）' },
          { value: 'split', label: '分离模式（Planner+Replyer，控制精细）' }
        ]
      },
      {
        key: 'kokoro_flow_chatter.max_wait_seconds_default',
        name: '默认等待时间',
        description: 'AI发送消息后愿意等待用户回复的时间（秒）',
        type: 'number',
        default: 300,
        min: 60,
        max: 3600
      },
      {
        key: 'kokoro_flow_chatter.enable_continuous_thinking',
        name: '持续心理活动',
        description: '是否在等待期间启用心理活动更新',
        type: 'boolean',
        default: true
      },
      // KFC主动思考子配置
      {
        key: 'kokoro_flow_chatter.proactive_thinking.enabled',
        name: 'KFC主动思考',
        description: '是否启用KFC的私聊主动思考（想一想要不要联系对方）',
        type: 'boolean',
        default: true
      },
      {
        key: 'kokoro_flow_chatter.proactive_thinking.silence_threshold_seconds',
        name: '沉默触发阈值',
        description: '用户沉默超过此时长（秒）可能触发主动思考',
        type: 'number',
        default: 7200,
        min: 300,
        max: 86400
      },
      {
        key: 'kokoro_flow_chatter.proactive_thinking.min_affinity_for_proactive',
        name: '最低好感度',
        description: '需要达到的最低好感度才会开始主动关心',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1
      },
      {
        key: 'kokoro_flow_chatter.proactive_thinking.min_interval_between_proactive',
        name: '主动间隔',
        description: '两次主动思考之间的最小间隔（秒）',
        type: 'number',
        default: 1800,
        min: 300,
        max: 86400
      },
      {
        key: 'kokoro_flow_chatter.proactive_thinking.quiet_hours_start',
        name: '勿扰开始时间',
        description: '勿扰开始时间，格式: HH:MM',
        type: 'string',
        default: '23:00',
        placeholder: '23:00'
      },
      {
        key: 'kokoro_flow_chatter.proactive_thinking.quiet_hours_end',
        name: '勿扰结束时间',
        description: '勿扰结束时间，格式: HH:MM',
        type: 'string',
        default: '07:00',
        placeholder: '07:00'
      },
      {
        key: 'kokoro_flow_chatter.proactive_thinking.trigger_probability',
        name: '触发概率',
        description: '每次检查时主动发起的概率（0-1），避免过于频繁打扰',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1
      }
    ]
  },

  // 跨群上下文
  {
    key: 'cross_context',
    name: '跨群上下文',
    icon: 'lucide:share-2',
    description: '跨群聊/私聊上下文共享配置，基于用户中心检索',
    fields: [
      {
        key: 'cross_context.enable',
        name: '启用跨群上下文',
        description: '总开关，用于一键启用或禁用此功能',
        type: 'boolean',
        default: true
      },
      {
        key: 'cross_context.s4u_mode',
        name: 'S4U模式',
        description: '用户中心上下文检索模式',
        type: 'select',
        default: 'whitelist',
        options: [
          { value: 'whitelist', label: '白名单模式' },
          { value: 'blacklist', label: '黑名单模式' }
        ]
      },
      {
        key: 'cross_context.s4u_limit',
        name: '消息条数',
        description: 'S4U模式下从每个聊天中获取目标用户的消息条数',
        type: 'number',
        default: 10,
        min: 1,
        max: 50
      },
      {
        key: 'cross_context.s4u_stream_limit',
        name: '聊天流数量',
        description: 'S4U模式下最多检索多少个不同的聊天流',
        type: 'number',
        default: 3,
        min: 1,
        max: 20
      },
      {
        key: 'cross_context.s4u_whitelist_chats',
        name: '白名单',
        description: '白名单列表，格式: ["platform:type:id", ...]',
        type: 'array',
        placeholder: '例如: qq:group:123456',
        specialEditor: 'chat_list'
      },
      {
        key: 'cross_context.s4u_blacklist_chats',
        name: '黑名单',
        description: '黑名单列表，格式: ["platform:type:id", ...]',
        type: 'array',
        placeholder: '例如: qq:private:789',
        specialEditor: 'chat_list'
      }
    ]
  },

  // 兴趣流系统
  {
    key: 'affinity_flow',
    name: '兴趣流系统',
    icon: 'lucide:activity',
    description: '配置机器人的兴趣评分和回复决策系统',
    fields: [
      {
        key: 'affinity_flow.enable_normal_mode',
        name: '启用Normal模式',
        description: '启用后在专注模式回复后会自动切换，根据兴趣度决定是否回复',
        type: 'boolean',
        default: true
      },
      {
        key: 'affinity_flow.reply_action_interest_threshold',
        name: '回复兴趣阈值',
        description: '回复动作的兴趣阈值',
        type: 'number',
        default: 0.75,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        key: 'affinity_flow.non_reply_action_interest_threshold',
        name: '非回复兴趣阈值',
        description: '非回复动作的兴趣阈值',
        type: 'number',
        default: 0.65,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        key: 'affinity_flow.high_match_interest_threshold',
        name: '高匹配兴趣阈值',
        description: '高匹配兴趣阈值',
        type: 'number',
        default: 0.6,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'affinity_flow.medium_match_interest_threshold',
        name: '中匹配兴趣阈值',
        description: '中匹配兴趣阈值',
        type: 'number',
        default: 0.4,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'affinity_flow.low_match_interest_threshold',
        name: '低匹配兴趣阈值',
        description: '低匹配兴趣阈值',
        type: 'number',
        default: 0.2,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'affinity_flow.high_match_keyword_multiplier',
        name: '高匹配关键词倍率',
        description: '高匹配关键词兴趣倍率',
        type: 'number',
        default: 4,
        min: 1,
        max: 10,
        step: 0.5,
        advanced: true
      },
      {
        key: 'affinity_flow.medium_match_keyword_multiplier',
        name: '中匹配关键词倍率',
        description: '中匹配关键词兴趣倍率',
        type: 'number',
        default: 2.5,
        min: 1,
        max: 10,
        step: 0.5,
        advanced: true
      },
      {
        key: 'affinity_flow.low_match_keyword_multiplier',
        name: '低匹配关键词倍率',
        description: '低匹配关键词兴趣倍率',
        type: 'number',
        default: 1.15,
        min: 1,
        max: 10,
        step: 0.05,
        advanced: true
      },
      {
        key: 'affinity_flow.no_reply_threshold_adjustment',
        name: '不回复阈值调整值',
        description: '不回复兴趣阈值调整值',
        type: 'number',
        default: 0.02,
        min: 0,
        max: 0.2,
        step: 0.01,
        advanced: true
      },
      {
        key: 'affinity_flow.reply_cooldown_reduction',
        name: '回复冷却减少',
        description: '回复后减少的不回复计数',
        type: 'number',
        default: 2,
        min: 1,
        max: 10,
        advanced: true
      },
      {
        key: 'affinity_flow.max_no_reply_count',
        name: '最大不回复次数',
        description: '最大不回复计数次数',
        type: 'number',
        default: 5,
        min: 1,
        max: 20,
        advanced: true
      },
      {
        key: 'affinity_flow.enable_post_reply_boost',
        name: '回复后连续对话',
        description: '启用回复后阈值降低机制，使bot更容易进行连续对话',
        type: 'boolean',
        default: true
      },
      {
        key: 'affinity_flow.post_reply_threshold_reduction',
        name: '阈值降低值',
        description: '回复后初始阈值降低值',
        type: 'number',
        default: 0.1,
        min: 0,
        max: 0.5,
        step: 0.05,
        advanced: true
      },
      {
        key: 'affinity_flow.post_reply_boost_max_count',
        name: '阈值降低持续次数',
        description: '回复后阈值降低的最大持续次数',
        type: 'number',
        default: 3,
        min: 1,
        max: 10,
        advanced: true
      },
      {
        key: 'affinity_flow.post_reply_boost_decay_rate',
        name: '阈值降低衰减率',
        description: '每次回复后阈值降低衰减率（0-1，越小衰减越快）',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'affinity_flow.keyword_match_weight',
        name: '关键词匹配权重',
        description: '兴趣关键词匹配度权重',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'affinity_flow.mention_bot_weight',
        name: '提及bot权重',
        description: '提及bot分数权重',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'affinity_flow.relationship_weight',
        name: '人物关系权重',
        description: '人物关系分数权重',
        type: 'number',
        default: 0.2,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'affinity_flow.strong_mention_interest_score',
        name: '强提及分数',
        description: '被@、被回复、私聊时的兴趣分',
        type: 'number',
        default: 2.0,
        min: 0,
        max: 5,
        step: 0.1,
        advanced: true
      },
      {
        key: 'affinity_flow.weak_mention_interest_score',
        name: '弱提及分数',
        description: '文本匹配bot名字或别名时的兴趣分',
        type: 'number',
        default: 0.8,
        min: 0,
        max: 2,
        step: 0.1,
        advanced: true
      },
      {
        key: 'affinity_flow.base_relationship_score',
        name: '基础关系分',
        description: '基础人物关系分',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'affinity_flow.match_count_bonus',
        name: '匹配数加成值',
        description: '匹配数关键词加成值',
        type: 'number',
        default: 0.01,
        min: 0,
        max: 0.5,
        step: 0.01,
        advanced: true
      },
      {
        key: 'affinity_flow.max_match_bonus',
        name: '最大匹配加成值',
        description: '最大匹配数加成值',
        type: 'number',
        default: 0.1,
        min: 0,
        max: 1,
        step: 0.05,
        advanced: true
      },
      {
        key: 'affinity_flow.mention_bot_adjustment_threshold',
        name: '提及bot调整阈值',
        description: '提及bot后的调整阈值',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      }
    ]
  },

  // 主动思考（群聊）
  {
    key: 'proactive_thinking',
    name: '主动思考',
    icon: 'lucide:lightbulb',
    description: '主动发起对话功能配置，用于群聊和私聊（当KFC关闭时）',
    fields: [
      {
        key: 'proactive_thinking.enable',
        name: '启用主动思考',
        description: '是否启用主动发起对话功能',
        type: 'boolean',
        default: true
      },
      {
        key: 'proactive_thinking.base_interval',
        name: '基础间隔',
        description: '基础触发间隔（秒）',
        type: 'number',
        default: 1800,
        min: 60,
        max: 86400
      },
      {
        key: 'proactive_thinking.min_interval',
        name: '最小间隔',
        description: '最小触发间隔（秒），兴趣分数高时会接近此值',
        type: 'number',
        default: 600,
        min: 60,
        max: 3600
      },
      {
        key: 'proactive_thinking.max_interval',
        name: '最大间隔',
        description: '最大触发间隔（秒），兴趣分数低时会接近此值',
        type: 'number',
        default: 7200,
        min: 1800,
        max: 86400
      },
      {
        key: 'proactive_thinking.use_interest_score',
        name: '动态调整',
        description: '是否根据兴趣分数动态调整间隔',
        type: 'boolean',
        default: true
      },
      {
        key: 'proactive_thinking.enable_time_strategy',
        name: '时间策略',
        description: '是否启用时间策略（根据时段调整频率）',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'proactive_thinking.quiet_hours_start',
        name: '安静时段开始',
        description: '安静时段开始时间，格式: HH:MM',
        type: 'string',
        default: '00:00',
        placeholder: '00:00',
        advanced: true
      },
      {
        key: 'proactive_thinking.quiet_hours_end',
        name: '安静时段结束',
        description: '安静时段结束时间，格式: HH:MM',
        type: 'string',
        default: '07:00',
        placeholder: '07:00',
        advanced: true
      },
      {
        key: 'proactive_thinking.max_daily_proactive',
        name: '每日最大次数',
        description: '每个聊天流每天最多主动发言次数，0表示不限制',
        type: 'number',
        default: 0,
        min: 0,
        max: 100,
        advanced: true
      },
      {
        key: 'proactive_thinking.whitelist_mode',
        name: '启用白名单模式',
        description: '启用后只对白名单中的聊天流生效',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'proactive_thinking.blacklist_mode',
        name: '启用黑名单模式',
        description: '启用后排除黑名单中的聊天流',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'proactive_thinking.whitelist_private',
        name: '私聊白名单',
        description: '私聊白名单，格式: ["qq:12345:private"]',
        type: 'array',
        placeholder: 'qq:12345:private',
        advanced: true
      },
      {
        key: 'proactive_thinking.whitelist_group',
        name: '群聊白名单',
        description: '群聊白名单，格式: ["qq:123456:group"]',
        type: 'array',
        placeholder: 'qq:123456:group',
        advanced: true
      },
      {
        key: 'proactive_thinking.blacklist_private',
        name: '私聊黑名单',
        description: '私聊黑名单，格式: ["qq:12345:private"]',
        type: 'array',
        placeholder: 'qq:12345:private',
        advanced: true
      },
      {
        key: 'proactive_thinking.blacklist_group',
        name: '群聊黑名单',
        description: '群聊黑名单，格式: ["qq:999999:group"]',
        type: 'array',
        placeholder: 'qq:999999:group',
        advanced: true
      },
      {
        key: 'proactive_thinking.min_interest_score',
        name: '最低兴趣分数',
        description: '最低兴趣分数阈值，低于此值不会主动思考',
        type: 'number',
        default: 0.0,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'proactive_thinking.max_interest_score',
        name: '最高兴趣分数',
        description: '最高兴趣分数阈值，高于此值不会主动思考',
        type: 'number',
        default: 1.0,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'proactive_thinking.interest_score_factor',
        name: '兴趣分数影响因子',
        description: '兴趣分数影响因子（1.0-3.0）',
        type: 'number',
        default: 2.0,
        min: 1,
        max: 3,
        step: 0.1,
        advanced: true
      },
      {
        key: 'proactive_thinking.active_hours_multiplier',
        name: '活跃时段间隔倍数',
        description: '活跃时段间隔倍数，<1表示更频繁，>1表示更稀疏',
        type: 'number',
        default: 0.7,
        min: 0.1,
        max: 3,
        step: 0.1,
        advanced: true
      },
      {
        key: 'proactive_thinking.reply_reset_enabled',
        name: '回复后重置计时器',
        description: 'bot回复后是否重置定时器',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'proactive_thinking.topic_throw_cooldown',
        name: '主动发言冷却时间',
        description: '主动发言后的冷却时间（秒），期间暂停主动思考，0表示不暂停',
        type: 'number',
        default: 3600,
        min: 0,
        max: 86400,
        advanced: true
      },
      {
        key: 'proactive_thinking.do_nothing_weight',
        name: '无操作权重',
        description: 'do_nothing动作的基础权重',
        type: 'number',
        default: 0.4,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'proactive_thinking.simple_bubble_weight',
        name: '简单冒泡权重',
        description: 'simple_bubble动作的基础权重',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'proactive_thinking.throw_topic_weight',
        name: '抛出话题权重',
        description: 'throw_topic动作的基础权重',
        type: 'number',
        default: 0.3,
        min: 0,
        max: 1,
        step: 0.1,
        advanced: true
      },
      {
        key: 'proactive_thinking.enable_statistics',
        name: '启用统计',
        description: '是否启用统计功能',
        type: 'boolean',
        default: true,
        advanced: true
      },
      {
        key: 'proactive_thinking.log_decisions',
        name: '记录决策日志',
        description: '是否记录每次决策的详细日志',
        type: 'boolean',
        default: false,
        advanced: true
      }
    ]
  },

  // 自定义提示词
  {
    key: 'custom_prompt',
    name: '自定义提示词',
    icon: 'lucide:message-square-text',
    description: '自定义部分提示词内容',
    fields: [
      {
        key: 'custom_prompt.image_prompt',
        name: '图片描述提示词',
        description: '用于描述图片内容的提示词',
        type: 'textarea',
        placeholder: '请用中文描述这张图片的内容...'
      },
      {
        key: 'custom_prompt.planner_custom_prompt_content',
        name: 'AFC决策器提示词',
        description: 'AFC决策器自定义提示词内容，留空则不生效',
        type: 'textarea',
        placeholder: '例如: 请在聊天中多用一些EMOJI_ACTION'
      }
    ]
  },

  // 依赖管理
  {
    key: 'dependency_management',
    name: '依赖管理',
    icon: 'lucide:package',
    description: '插件Python依赖管理配置',
    fields: [
      {
        key: 'dependency_management.auto_install',
        name: '自动安装',
        description: '是否启用自动安装Python依赖包',
        type: 'boolean',
        default: true
      },
      {
        key: 'dependency_management.auto_install_timeout',
        name: '安装超时',
        description: '安装超时时间（秒）',
        type: 'number',
        default: 300,
        min: 60,
        max: 1800
      },
      {
        key: 'dependency_management.use_mirror',
        name: '使用镜像源',
        description: '是否使用PyPI镜像源（推荐，可加速下载）',
        type: 'boolean',
        default: true
      },
      {
        key: 'dependency_management.mirror_url',
        name: '镜像源URL',
        description: 'PyPI镜像源URL',
        type: 'string',
        default: 'https://pypi.tuna.tsinghua.edu.cn/simple',
        placeholder: 'https://pypi.tuna.tsinghua.edu.cn/simple'
      },
      {
        key: 'dependency_management.install_log_level',
        name: '安装日志级别',
        description: '依赖安装日志级别',
        type: 'select',
        default: 'INFO',
        options: [
          { value: 'DEBUG', label: 'DEBUG' },
          { value: 'INFO', label: 'INFO' },
          { value: 'WARNING', label: 'WARNING' },
          { value: 'ERROR', label: 'ERROR' }
        ],
        advanced: true
      }
    ]
  },

  // ==================== 专家模式配置组 ====================

  // LPMM知识库（专家模式）
  {
    key: 'lpmm_knowledge',
    name: 'LPMM知识库',
    icon: 'lucide:book-open',
    description: 'LPMM知识库配置，包含各种阈值和TopK参数',
    expert: true,
    fields: [
      {
        key: 'lpmm_knowledge.enable',
        name: '启用知识库',
        description: '是否启用LPMM知识库',
        type: 'boolean',
        default: false
      },
      {
        key: 'lpmm_knowledge.enable_summary',
        name: '启用总结',
        description: '是否启用知识库总结功能',
        type: 'boolean',
        default: true
      },
      {
        key: 'lpmm_knowledge.rag_synonym_search_top_k',
        name: '同义词TopK',
        description: '同义词搜索返回的最大数量',
        type: 'number',
        default: 10,
        min: 1,
        max: 50
      },
      {
        key: 'lpmm_knowledge.rag_synonym_threshold',
        name: '同义词阈值',
        description: '同义词相似度阈值（高于此值的词语会被认为是同义词）',
        type: 'number',
        default: 0.8,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        key: 'lpmm_knowledge.info_extraction_workers',
        name: '提取线程数',
        description: '实体提取同时执行线程数，非Pro模型不要设置超过5',
        type: 'number',
        default: 3,
        min: 1,
        max: 10
      },
      {
        key: 'lpmm_knowledge.qa_relation_search_top_k',
        name: '关系搜索TopK',
        description: '关系搜索返回的最大数量',
        type: 'number',
        default: 10,
        min: 1,
        max: 50
      },
      {
        key: 'lpmm_knowledge.qa_relation_threshold',
        name: '关系阈值',
        description: '关系相似度阈值',
        type: 'number',
        default: 0.5,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        key: 'lpmm_knowledge.qa_paragraph_search_top_k',
        name: '段落搜索TopK',
        description: '段落搜索返回的最大数量（不能过小）',
        type: 'number',
        default: 1000,
        min: 100,
        max: 5000
      },
      {
        key: 'lpmm_knowledge.qa_paragraph_threshold',
        name: '段落阈值',
        description: '段落相似度阈值',
        type: 'number',
        default: 0.4,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        key: 'lpmm_knowledge.qa_paragraph_node_weight',
        name: '段落节点权重',
        description: '段落节点在图搜索&PPR计算中的权重',
        type: 'number',
        default: 0.05,
        min: 0,
        max: 1,
        step: 0.01
      },
      {
        key: 'lpmm_knowledge.qa_ent_filter_top_k',
        name: '实体过滤TopK',
        description: '实体过滤返回的最大数量',
        type: 'number',
        default: 10,
        min: 1,
        max: 50
      },
      {
        key: 'lpmm_knowledge.qa_ppr_damping',
        name: 'PPR阻尼系数',
        description: 'PageRank阻尼系数',
        type: 'number',
        default: 0.8,
        min: 0,
        max: 1,
        step: 0.05
      },
      {
        key: 'lpmm_knowledge.qa_res_top_k',
        name: '结果TopK',
        description: '最终提供的文段数量',
        type: 'number',
        default: 3,
        min: 1,
        max: 20
      },
      {
        key: 'lpmm_knowledge.embedding_dimension',
        name: '嵌入维度',
        description: '嵌入向量维度，应该与模型的输出维度一致',
        type: 'number',
        default: 1024,
        min: 256,
        max: 4096
      }
    ]
  },

  // 视频分析高级配置（专家模式，基础配置在简单模式）
  {
    key: 'video_analysis_expert',
    name: '视频分析高级配置',
    icon: 'lucide:video',
    description: '视频分析的高级配置选项',
    expert: true,
    fields: [
      {
        key: 'video_analysis.frame_interval_seconds',
        name: '抽帧间隔',
        description: '按时间间隔抽帧的秒数（仅在time_interval模式下生效）',
        type: 'number',
        default: 2.0,
        min: 0.5,
        max: 30,
        step: 0.5
      },
      {
        key: 'video_analysis.frame_quality',
        name: '帧图像质量',
        description: '帧图像JPEG质量（1-100）',
        type: 'number',
        default: 80,
        min: 1,
        max: 100
      },
      {
        key: 'video_analysis.max_image_size',
        name: '最大图像尺寸',
        description: '单帧最大图像尺寸（像素）',
        type: 'number',
        default: 800,
        min: 200,
        max: 2000
      },
      {
        key: 'video_analysis.enable_frame_timing',
        name: '帧时间信息',
        description: '是否在分析中包含帧的时间信息',
        type: 'boolean',
        default: true
      },
      {
        key: 'video_analysis.rust_keyframe_threshold',
        name: '关键帧检测阈值',
        description: '关键帧检测阈值，值越大关键帧越少',
        type: 'number',
        default: 2.0,
        min: 0.5,
        max: 10,
        step: 0.5
      },
      {
        key: 'video_analysis.rust_use_simd',
        name: '启用SIMD',
        description: '启用SIMD优化（推荐）',
        type: 'boolean',
        default: true
      },
      {
        key: 'video_analysis.rust_block_size',
        name: '处理块大小',
        description: '处理块大小，较大值可能提高高分辨率视频性能',
        type: 'number',
        default: 8192,
        min: 1024,
        max: 65536
      },
      {
        key: 'video_analysis.rust_threads',
        name: '线程数',
        description: '线程数，0表示自动检测',
        type: 'number',
        default: 0,
        min: 0,
        max: 32
      },
      {
        key: 'video_analysis.batch_analysis_prompt',
        name: '批量分析提示词',
        description: '批量分析时使用的提示词模板',
        type: 'textarea'
      }
    ]
  },

  // 消息总线（专家模式）
  {
    key: 'message_bus',
    name: '消息总线',
    icon: 'lucide:network',
    description: '消息总线高级网络配置，用于自定义服务器设置',
    expert: true,
    fields: [
      {
        key: 'message_bus.auth_token',
        name: '认证令牌',
        description: '认证令牌，用于API验证，为空则不启用验证',
        type: 'array',
        placeholder: '添加认证令牌...'
      },
      {
        key: 'message_bus.use_custom',
        name: '使用自定义服务器',
        description: '是否启用自定义的message_bus服务器，需要设置新端口',
        type: 'boolean',
        default: false
      },
      {
        key: 'message_bus.host',
        name: '主机地址',
        description: '消息总线服务器主机地址',
        type: 'string',
        default: '127.0.0.1',
        placeholder: '127.0.0.1'
      },
      {
        key: 'message_bus.port',
        name: '端口',
        description: '消息总线服务器端口，不能与.env重复',
        type: 'number',
        default: 8090,
        min: 1024,
        max: 65535
      },
      {
        key: 'message_bus.mode',
        name: '模式',
        description: '连接模式',
        type: 'select',
        default: 'ws',
        options: [
          { value: 'ws', label: 'WebSocket' },
          { value: 'tcp', label: 'TCP' }
        ]
      },
      {
        key: 'message_bus.use_wss',
        name: '使用WSS',
        description: '是否使用WSS安全连接（仅支持ws模式）',
        type: 'boolean',
        default: false
      },
      {
        key: 'message_bus.cert_file',
        name: 'SSL证书路径',
        description: 'SSL证书文件路径，仅在use_wss=true时有效',
        type: 'string',
        placeholder: '/path/to/cert.pem'
      },
      {
        key: 'message_bus.key_file',
        name: 'SSL密钥路径',
        description: 'SSL密钥文件路径，仅在use_wss=true时有效',
        type: 'string',
        placeholder: '/path/to/key.pem'
      }
    ]
  }
]

// ==================== Model 配置描述 ====================

export const modelConfigGroups: ConfigGroupDef[] = [
  // API 提供商配置
  {
    key: 'api_providers',
    name: 'API 服务提供商',
    icon: 'lucide:cloud',
    description: '配置 AI 模型的 API 服务提供商',
    fields: [
      {
        key: 'name',
        name: '提供商名称',
        description: 'API 服务商名称，用于在模型配置中引用',
        type: 'string',
        placeholder: '例如: DeepSeek, OpenAI, SiliconFlow'
      },
      {
        key: 'base_url',
        name: 'API 地址',
        description: 'API 服务商的 BaseURL',
        type: 'string',
        placeholder: '例如: https://api.deepseek.com/v1'
      },
      {
        key: 'api_key',
        name: 'API 密钥',
        description: 'API 密钥，支持单个密钥或密钥列表轮询',
        type: 'password',
        placeholder: '输入 API Key'
      },
      {
        key: 'client_type',
        name: '客户端类型',
        description: '请求客户端类型',
        type: 'select',
        default: 'openai',
        options: [
          { value: 'openai', label: 'OpenAI 兼容' },
          { value: 'aiohttp_gemini', label: 'Gemini（Google）' }
        ]
      },
      {
        key: 'max_retry',
        name: '最大重试次数',
        description: '单个模型 API 调用失败时的最大重试次数',
        type: 'number',
        default: 2,
        min: 0,
        max: 10
      },
      {
        key: 'timeout',
        name: '请求超时',
        description: 'API 请求超时时间（秒）',
        type: 'number',
        default: 30,
        min: 5,
        max: 300
      },
      {
        key: 'retry_interval',
        name: '重试间隔',
        description: '重试间隔时间（秒）',
        type: 'number',
        default: 10,
        min: 1,
        max: 60
      }
    ]
  },

  // 模型配置
  {
    key: 'models',
    name: '模型配置',
    icon: 'lucide:cpu',
    description: '配置可用的 AI 模型',
    fields: [
      {
        key: 'model_identifier',
        name: '模型标识符',
        description: 'API 服务商提供的模型标识符',
        type: 'string',
        placeholder: '例如: deepseek-chat, gpt-4'
      },
      {
        key: 'name',
        name: '模型名称',
        description: '模型的自定义名称，在任务配置中使用',
        type: 'string',
        placeholder: '例如: deepseek-v3'
      },
      {
        key: 'api_provider',
        name: 'API 提供商',
        description: '对应在 api_providers 中配置的服务商名称',
        type: 'string',
        placeholder: '例如: DeepSeek'
      },
      {
        key: 'price_in',
        name: '输入价格',
        description: '输入价格，用于 API 调用统计（元/M token）',
        type: 'number',
        default: 0,
        min: 0,
        step: 0.1
      },
      {
        key: 'price_out',
        name: '输出价格',
        description: '输出价格，用于 API 调用统计（元/M token）',
        type: 'number',
        default: 0,
        min: 0,
        step: 0.1
      },
      {
        key: 'force_stream_mode',
        name: '强制流式输出',
        description: '如果模型不支持非流式输出，请启用此选项',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'anti_truncation',
        name: '防截断',
        description: '当模型输出不完整时，系统会自动重试',
        type: 'boolean',
        default: false,
        advanced: true
      },
      {
        key: 'enable_prompt_perturbation',
        name: '提示词扰动',
        description: '启用提示词扰动，整合内容混淆和注意力优化',
        type: 'boolean',
        default: false,
        advanced: true
      }
    ]
  }
]

// 模型任务配置描述
export const modelTaskConfigs: Record<string, { name: string; description: string }> = {
  'utils': {
    name: '通用工具模型',
    description: '用于表情包模块、取名模块、关系模块等组件，是必须配置的模型'
  },
  'utils_small': {
    name: '轻量工具模型',
    description: '消耗量较大的组件使用，建议使用速度较快的小模型'
  },
  'replyer': {
    name: '回复模型',
    description: '首要回复模型，还用于表达器和表达方式学习'
  },
  'planner': {
    name: '决策模型',
    description: '负责决定机器人该做什么的模型'
  },
  'emotion': {
    name: '情绪模型',
    description: '负责机器人的情绪变化'
  },
  'mood': {
    name: '心情模型',
    description: '负责机器人的心情变化'
  },
  'maizone': {
    name: 'Maizone 模型',
    description: 'Maizone 功能使用的模型'
  },
  'vlm': {
    name: '图像识别模型',
    description: '用于图像内容识别的视觉语言模型'
  },
  'emoji_vlm': {
    name: '表情包识别模型',
    description: '专用于表情包识别的视觉语言模型'
  },
  'utils_video': {
    name: '视频分析模型',
    description: '专用于视频内容分析的模型'
  },
  'voice': {
    name: '语音识别模型',
    description: '用于语音消息识别的模型'
  },
  'tool_use': {
    name: '工具调用模型',
    description: '需要使用支持工具调用的模型'
  },
  'schedule_generator': {
    name: '日程生成模型',
    description: '用于生成每日日程表的模型'
  },
  'anti_injection': {
    name: '反注入检测模型',
    description: '用于检测 prompt 注入攻击，建议使用快速的小模型'
  },
  'monthly_plan_generator': {
    name: '月度计划模型',
    description: '用于生成月度计划的模型'
  },
  'relationship_tracker': {
    name: '关系追踪模型',
    description: '用于用户关系追踪的模型'
  },
  'embedding': {
    name: '嵌入模型',
    description: '用于文本向量化的嵌入模型'
  },
  'lpmm_entity_extract': {
    name: 'LPMM 实体提取',
    description: '知识库实体提取模型'
  },
  'lpmm_rdf_build': {
    name: 'LPMM RDF 构建',
    description: '知识库 RDF 构建模型'
  },
  'lpmm_qa': {
    name: 'LPMM 问答',
    description: '知识库问答模型'
  },
  'memory_short_term_builder': {
    name: '短期记忆构建',
    description: '感知记忆到短期记忆的格式化模型'
  },
  'memory_short_term_decider': {
    name: '短期记忆决策',
    description: '决定短期记忆合并/更新/新建/丢弃的模型'
  },
  'memory_long_term_builder': {
    name: '长期记忆构建',
    description: '短期记忆到长期图结构的构建模型'
  },
  'memory_judge': {
    name: '记忆检索裁判',
    description: '判断记忆检索是否充足的模型'
  }
}

// 预设的 API 提供商模板
export const providerPresets = [
  {
    name: 'DeepSeek',
    icon: 'lucide:brain-circuit',
    base_url: 'https://api.deepseek.com/v1',
    client_type: 'openai',
    description: 'DeepSeek 官方 API'
  },
  {
    name: 'OpenAI',
    icon: 'simple-icons:openai',
    base_url: 'https://api.openai.com/v1',
    client_type: 'openai',
    description: 'OpenAI 官方 API'
  },
  {
    name: 'SiliconFlow',
    icon: 'lucide:cpu',
    base_url: 'https://api.siliconflow.cn/v1',
    client_type: 'openai',
    description: '硅基流动，支持多种模型'
  },
  {
    name: 'Google Gemini',
    icon: 'simple-icons:google',
    base_url: 'https://generativelanguage.googleapis.com/v1beta',
    client_type: 'aiohttp_gemini',
    description: 'Google Gemini API（需要特殊客户端）'
  },
  {
    name: '通义千问',
    icon: 'lucide:brain',
    base_url: 'https://dashscope.aliyuncs.com/api/v1',
    client_type: 'openai',
    description: '阿里云通义千问'
  },
  {
    name: 'Claude',
    icon: 'simple-icons:anthropic',
    base_url: 'https://api.anthropic.com',
    client_type: 'openai',
    description: 'Anthropic Claude API'
  },
  {
    name: '自定义',
    icon: 'lucide:settings',
    base_url: '',
    client_type: 'openai',
    description: '自定义 OpenAI 兼容 API'
  }
]

// 导出辅助函数
export function getFieldDescription(groupKey: string, fieldKey: string): ConfigFieldDef | undefined {
  const groups = [...botConfigGroups, ...modelConfigGroups]
  const group = groups.find(g => g.key === groupKey)
  if (!group) return undefined
  return group.fields.find(f => f.key === fieldKey || f.key === `${groupKey}.${fieldKey}`)
}

export function getGroupByKey(key: string): ConfigGroupDef | undefined {
  return [...botConfigGroups, ...modelConfigGroups].find(g => g.key === key)
}
