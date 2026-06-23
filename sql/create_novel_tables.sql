-- 小说连载助手 - 建表脚本
-- 执行方式：mysql -u root -p < create_novel_tables.sql

USE `ai_passage_creator`;

-- 小说主表
CREATE TABLE IF NOT EXISTS `novel` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `userId` BIGINT NOT NULL COMMENT '用户ID',
    `title` VARCHAR(100) NOT NULL COMMENT '书名',
    `genre` VARCHAR(50) DEFAULT NULL COMMENT '题材：xuanhuan/dushi/xuanyi/kehuang/yanqing/lishi/qita',
    `targetReaders` VARCHAR(20) DEFAULT NULL COMMENT '目标读者：male/female/general',
    `targetWordCount` INT DEFAULT NULL COMMENT '目标总字数',

    `worldSetting` TEXT DEFAULT NULL COMMENT '世界观设定（JSON）',
    `volumeOutline` TEXT DEFAULT NULL COMMENT '卷级大纲（JSON）',
    `styleGuide` TEXT DEFAULT NULL COMMENT '风格指南（JSON）',
    `synopsis` TEXT DEFAULT NULL COMMENT '全书梗概',

    `status` VARCHAR(20) NOT NULL DEFAULT 'ongoing' COMMENT '状态：ongoing/completed/paused',
    `phase` VARCHAR(40) NOT NULL DEFAULT 'PENDING' COMMENT '阶段',
    `currentChapterNumber` INT NOT NULL DEFAULT 0 COMMENT '当前章节数',
    `currentVolumeNumber` INT NOT NULL DEFAULT 1 COMMENT '当前卷号',
    `totalWordCount` INT NOT NULL DEFAULT 0 COMMENT '总字数',

    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `isDelete` SMALLINT NOT NULL DEFAULT 0 COMMENT '是否删除',

    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`userId`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小说表';


-- 章节表
CREATE TABLE IF NOT EXISTS `chapter` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',
    `volumeNumber` INT NOT NULL DEFAULT 1 COMMENT '卷号',
    `chapterNumber` INT NOT NULL COMMENT '章节号',
    `title` VARCHAR(100) DEFAULT NULL COMMENT '章节标题',

    `outline` TEXT DEFAULT NULL COMMENT '本章大纲（JSON）',
    `chapterMemo` LONGTEXT DEFAULT NULL COMMENT '章节备忘录/写作意图（JSON）',
    `content` LONGTEXT DEFAULT NULL COMMENT '正文（Markdown）',
    `summary` TEXT DEFAULT NULL COMMENT '本章摘要（归档时生成，约150字）',
    `endingState` LONGTEXT DEFAULT NULL COMMENT '章节结尾状态快照（JSON）',
    `qualityReport` LONGTEXT DEFAULT NULL COMMENT '生成后质量审稿报告（JSON）',
    `wordCount` INT NOT NULL DEFAULT 0 COMMENT '字数',

    `characterStates` TEXT DEFAULT NULL COMMENT '本章结束时角色状态快照（JSON）',
    `contextSnapshotId` BIGINT DEFAULT NULL COMMENT '上下文快照ID',

    `status` VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '状态：draft/confirmed/revised',

    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `isDelete` SMALLINT NOT NULL DEFAULT 0 COMMENT '是否删除',

    PRIMARY KEY (`id`),
    UNIQUE INDEX `idx_novel_chapter` (`novelId`, `chapterNumber`),
    INDEX `idx_novel_id` (`novelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='章节表';


-- 角色表
CREATE TABLE IF NOT EXISTS `character` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',

    `name` VARCHAR(50) NOT NULL COMMENT '角色名',
    `aliases` TEXT DEFAULT NULL COMMENT '别名列表（JSON）',
    `roleType` VARCHAR(20) DEFAULT NULL COMMENT '类型：protagonist/supporting/antagonist/minor',
    `isCore` SMALLINT NOT NULL DEFAULT 0 COMMENT '是否核心角色（始终注入上下文）',

    `appearance` TEXT DEFAULT NULL COMMENT '外貌',
    `personality` TEXT DEFAULT NULL COMMENT '性格',
    `background` TEXT DEFAULT NULL COMMENT '背景',
    `skills` TEXT DEFAULT NULL COMMENT '技能列表（JSON）',
    `speechStyle` TEXT DEFAULT NULL COMMENT '说话风格',

    `currentLocation` VARCHAR(100) DEFAULT NULL COMMENT '当前位置',
    `currentStatus` TEXT DEFAULT NULL COMMENT '当前状态',
    `relationshipMap` TEXT DEFAULT NULL COMMENT '与其他角色的关系（JSON）',

    `firstAppearanceChapterId` BIGINT DEFAULT NULL COMMENT '首次出场章节ID',
    `lastAppearanceChapterId` BIGINT DEFAULT NULL COMMENT '最后出场章节ID',
    `notes` TEXT DEFAULT NULL COMMENT '零散细节记录',

    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `isDelete` SMALLINT NOT NULL DEFAULT 0 COMMENT '是否删除',

    PRIMARY KEY (`id`),
    INDEX `idx_novel_id` (`novelId`),
    INDEX `idx_name` (`novelId`, `name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';


-- 伏笔表
CREATE TABLE IF NOT EXISTS `foreshadowing` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',

    `surface` TEXT NOT NULL COMMENT '表面信息（读者看到的）',
    `hiddenTruth` TEXT DEFAULT NULL COMMENT '隐藏真相（作者知道的）',
    `category` VARCHAR(20) DEFAULT NULL COMMENT '类型：character/plot/setting/emotion',

    `relatedCharacters` TEXT DEFAULT NULL COMMENT '涉及的角色名（JSON）',
    `relatedLocations` TEXT DEFAULT NULL COMMENT '涉及的地点（JSON）',
    `relatedSkills` TEXT DEFAULT NULL COMMENT '涉及的技能/设定（JSON）',

    `plantedChapterId` BIGINT DEFAULT NULL COMMENT '哪章埋的',
    `targetChapter` VARCHAR(50) DEFAULT NULL COMMENT '计划揭示章节范围，如 80-100',
    `resolvedChapterId` BIGINT DEFAULT NULL COMMENT '实际揭示章节ID（null=未解决）',

    `keywords` TEXT DEFAULT NULL COMMENT '检索关键词（JSON）',
    `importance` SMALLINT NOT NULL DEFAULT 3 COMMENT '重要度 1-5',

    `status` VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT '状态：active/resolved/abandoned',
    `lifecycleStage` VARCHAR(30) NOT NULL DEFAULT 'planted' COMMENT '内部生命周期：planted/open/progressing/near_payoff/pressured',

    `mentionHistory` TEXT DEFAULT NULL COMMENT '历史呼应记录（JSON）',
    `lastMentionedChapter` INT DEFAULT NULL COMMENT '最后一次提及的章节号',
    `lastActionType` VARCHAR(30) DEFAULT NULL COMMENT '最近动作：plant/mention/advance/resolve/defer',
    `lastActionChapter` INT DEFAULT NULL COMMENT '最近动作章节号',
    `lastActionNote` TEXT DEFAULT NULL COMMENT '最近动作说明',

    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    INDEX `idx_novel_status` (`novelId`, `status`),
    INDEX `idx_planted` (`plantedChapterId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='伏笔表';


-- 地点表
CREATE TABLE IF NOT EXISTS `location` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',
    `name` VARCHAR(100) NOT NULL COMMENT '地点名称',
    `description` TEXT DEFAULT NULL COMMENT '地点描述',
    `firstAppearanceChapterId` BIGINT DEFAULT NULL COMMENT '首次出现章节ID',
    `notes` TEXT DEFAULT NULL COMMENT '备注',

    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    INDEX `idx_novel_id` (`novelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地点表';


-- 上下文快照表（调试用）
CREATE TABLE IF NOT EXISTS `context_snapshot` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',
    `chapterId` BIGINT NOT NULL COMMENT '章节ID',
    `contextData` LONGTEXT DEFAULT NULL COMMENT '生成本章时注入的上下文包（JSON）',
    `promptData` LONGTEXT DEFAULT NULL COMMENT '最终写作 Prompt 和规则栈（JSON）',
    `traceData` LONGTEXT DEFAULT NULL COMMENT '上下文检索/裁剪追踪信息（JSON）',
    `version` VARCHAR(20) NOT NULL DEFAULT 'v1' COMMENT '上下文包版本',
    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (`id`),
    INDEX `idx_chapter` (`chapterId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='上下文快照表';


-- 小说运行状态表
CREATE TABLE IF NOT EXISTS `novel_state` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',
    `stateType` VARCHAR(50) NOT NULL COMMENT '状态类型：current_state/reader_expectation/style_memory 等',
    `stateData` LONGTEXT DEFAULT NULL COMMENT '状态内容（JSON）',
    `sourceChapterId` BIGINT DEFAULT NULL COMMENT '来源章节ID',
    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    PRIMARY KEY (`id`),
    UNIQUE INDEX `uk_novel_state_type` (`novelId`, `stateType`),
    INDEX `idx_novel_state_novel` (`novelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小说运行状态表';


-- 章节版本记录表
CREATE TABLE IF NOT EXISTS `chapter_version` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',
    `chapterId` BIGINT NOT NULL COMMENT '章节ID',
    `versionType` VARCHAR(30) NOT NULL COMMENT '版本类型：ai_draft/auto_revised/user_confirmed',
    `content` LONGTEXT DEFAULT NULL COMMENT '版本正文',
    `metaData` LONGTEXT DEFAULT NULL COMMENT '版本元数据（JSON）',
    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (`id`),
    INDEX `idx_chapter_version_chapter` (`chapterId`, `versionType`),
    INDEX `idx_chapter_version_novel` (`novelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='章节版本记录表';
