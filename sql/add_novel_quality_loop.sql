-- AI Novel quality loop upgrade
-- Adds structured chapter memory, context snapshots, version history, and hook lifecycle fields.

ALTER TABLE `chapter`
    ADD COLUMN `chapterMemo` LONGTEXT DEFAULT NULL COMMENT '章节备忘录/写作意图（JSON）' AFTER `outline`,
    ADD COLUMN `endingState` LONGTEXT DEFAULT NULL COMMENT '章节结尾状态快照（JSON）' AFTER `summary`,
    ADD COLUMN `qualityReport` LONGTEXT DEFAULT NULL COMMENT '生成后质量审稿报告（JSON）' AFTER `endingState`;

ALTER TABLE `context_snapshot`
    MODIFY COLUMN `contextData` LONGTEXT DEFAULT NULL COMMENT '生成本章时注入的上下文包（JSON）',
    ADD COLUMN `promptData` LONGTEXT DEFAULT NULL COMMENT '最终写作 Prompt 和规则栈（JSON）' AFTER `contextData`,
    ADD COLUMN `traceData` LONGTEXT DEFAULT NULL COMMENT '上下文检索/裁剪追踪信息（JSON）' AFTER `promptData`,
    ADD COLUMN `version` VARCHAR(20) NOT NULL DEFAULT 'v1' COMMENT '上下文包版本' AFTER `traceData`;

CREATE TABLE IF NOT EXISTS `novel_state` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',
    `stateType` VARCHAR(50) NOT NULL COMMENT '状态类型：current_state/reader_expectation/style_memory 等',
    `stateData` LONGTEXT DEFAULT NULL COMMENT '状态内容（JSON）',
    `sourceChapterId` BIGINT DEFAULT NULL COMMENT '来源章节ID',
    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updateTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_novel_state_type` (`novelId`, `stateType`),
    KEY `idx_novel_state_novel` (`novelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='小说运行状态表';

CREATE TABLE IF NOT EXISTS `chapter_version` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT 'id',
    `novelId` BIGINT NOT NULL COMMENT '小说ID',
    `chapterId` BIGINT NOT NULL COMMENT '章节ID',
    `versionType` VARCHAR(30) NOT NULL COMMENT '版本类型：ai_draft/auto_revised/user_confirmed',
    `content` LONGTEXT DEFAULT NULL COMMENT '版本正文',
    `metaData` LONGTEXT DEFAULT NULL COMMENT '版本元数据（JSON）',
    `createTime` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    KEY `idx_chapter_version_chapter` (`chapterId`, `versionType`),
    KEY `idx_chapter_version_novel` (`novelId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='章节版本记录表';

ALTER TABLE `foreshadowing`
    ADD COLUMN `lifecycleStage` VARCHAR(30) NOT NULL DEFAULT 'planted' COMMENT '内部生命周期：planted/open/progressing/near_payoff/pressured' AFTER `status`,
    ADD COLUMN `lastActionType` VARCHAR(30) DEFAULT NULL COMMENT '最近动作：plant/mention/advance/resolve/defer' AFTER `lastMentionedChapter`,
    ADD COLUMN `lastActionChapter` INT DEFAULT NULL COMMENT '最近动作章节号' AFTER `lastActionType`,
    ADD COLUMN `lastActionNote` TEXT DEFAULT NULL COMMENT '最近动作说明' AFTER `lastActionChapter`;
