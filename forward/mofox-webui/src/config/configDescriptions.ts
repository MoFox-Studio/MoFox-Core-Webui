/**
 * 配置项描述文件
 * 基于 bot_config_template.toml 和 model_config_template.toml
 * 提供配置项的中文名称、描述和分组信息
 */

// 配置字段类型
export type FieldType = 'string' | 'number' | 'boolean' | 'array' | 'object' | 'password' | 'select' | 'textarea'

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
  advanced?: boolean       // 是否为高级选项
}

// 配置分组定义
export interface ConfigGroupDef {
  key: string              // 分组键名
  name: string             // 分组名称
  icon: string             // 图标
  description: string      // 分组描述
  fields: ConfigFieldDef[] // 字段列表
}

// ==================== Bot 配置描述 ====================

export const botConfigGroups: ConfigGroupDef[] = [
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
        key: 'chat.dynamic_distribution_enabled',
        name: '动态消息分发',
        description: '是否启用动态消息分发周期调整',
        type: 'boolean',
        default: true,
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
        key: 'database.enable_database_cache',
        name: '启用数据库缓存',
        description: '启用数据库查询缓存系统，防止内存溢出',
        type: 'boolean',
        default: true,
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
    description: '配置联网搜索功能',
    fields: [
      {
        key: 'web_search.enable_web_search_tool',
        name: '启用联网搜索',
        description: '是否启用联网搜索工具',
        type: 'boolean',
        default: true
      },
      {
        key: 'web_search.enable_url_tool',
        name: '启用 URL 解析',
        description: '是否启用 URL 解析工具',
        type: 'boolean',
        default: true
      },
      {
        key: 'web_search.enabled_engines',
        name: '启用的搜索引擎',
        description: '启用的搜索引擎列表',
        type: 'array',
        default: ['ddg'],
        placeholder: '可选: exa, tavily, ddg, bing, metaso, serper'
      },
      {
        key: 'web_search.tavily_api_keys',
        name: 'Tavily API 密钥',
        description: 'Tavily API 密钥列表，支持轮询机制',
        type: 'array',
        advanced: true
      },
      {
        key: 'web_search.exa_api_keys',
        name: 'EXA API 密钥',
        description: 'EXA API 密钥列表，支持轮询机制',
        type: 'array',
        advanced: true
      }
    ]
  },

  // 视频分析配置
  {
    key: 'video_analysis',
    name: '视频分析',
    icon: 'lucide:video',
    description: '配置视频分析功能',
    fields: [
      {
        key: 'video_analysis.enable',
        name: '启用视频分析',
        description: '是否启用视频分析功能',
        type: 'boolean',
        default: true
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
      }
    ]
  },

  // 权限配置
  {
    key: 'permission',
    name: '权限配置',
    icon: 'lucide:shield',
    description: '配置用户权限和主人身份',
    fields: [
      {
        key: 'permission.master_users',
        name: '主人用户',
        description: '拥有最高权限的用户列表，格式: [["platform", "user_id"], ...]',
        type: 'array',
        placeholder: '例如: [["qq", "123456"]]'
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
