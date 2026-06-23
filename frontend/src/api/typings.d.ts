declare namespace API {
  type AgentExecutionStats = {
    taskId?: string
    totalDurationMs?: number
    agentCount?: number
    agentDurations?: Record<string, any>
    overallStatus?: string
    logs?: AgentLog[]
  }

  type AgentLog = {
    id?: number
    taskId?: string
    agentName?: string
    startTime?: string
    endTime?: string
    durationMs?: number
    status?: string
    errorMessage?: string
    prompt?: string
    inputData?: string
    outputData?: string
    createTime?: string
    updateTime?: string
    isDelete?: number
  }

  type ArticleAiModifyOutlineRequest = {
    taskId?: string
    modifySuggestion?: string
  }

  type ArticleConfirmOutlineRequest = {
    taskId?: string
    outline?: OutlineSection[]
  }

  type ArticleConfirmTitleRequest = {
    taskId?: string
    selectedMainTitle?: string
    selectedSubTitle?: string
    userDescription?: string
  }

  type ArticleCreateRequest = {
    topic?: string
    style?: string
    enabledImageMethods?: string[]
  }

  type ArticleQueryRequest = {
    pageNum?: number
    pageSize?: number
    sortField?: string
    sortOrder?: string
    userId?: number
    status?: string
  }

  type ArticleVO = {
    id?: number
    taskId?: string
    userId?: number
    topic?: string
    userDescription?: string
    mainTitle?: string
    subTitle?: string
    titleOptions?: TitleOption[]
    outline?: OutlineItem[]
    content?: string
    fullContent?: string
    coverImage?: string
    images?: ImageItem[]
    status?: string
    phase?: string
    errorMessage?: string
    createTime?: string
    completedTime?: string
  }

  type BaseResponseAgentExecutionStats = {
    code?: number
    data?: AgentExecutionStats
    message?: string
  }

  type BaseResponseArticleVO = {
    code?: number
    data?: ArticleVO
    message?: string
  }

  type BaseResponseBoolean = {
    code?: number
    data?: boolean
    message?: string
  }

  type BaseResponseListOutlineSection = {
    code?: number
    data?: OutlineSection[]
    message?: string
  }

  type BaseResponseListPaymentRecord = {
    code?: number
    data?: PaymentRecord[]
    message?: string
  }

  type BaseResponseLoginUserVO = {
    code?: number
    data?: LoginUserVO
    message?: string
  }

  type BaseResponseLong = {
    code?: number
    data?: number
    message?: string
  }

  type BaseResponsePageArticleVO = {
    code?: number
    data?: PageArticleVO
    message?: string
  }

  type BaseResponsePageUserVO = {
    code?: number
    data?: PageUserVO
    message?: string
  }

  type BaseResponseStatisticsVO = {
    code?: number
    data?: StatisticsVO
    message?: string
  }

  type BaseResponseString = {
    code?: number
    data?: string
    message?: string
  }

  type BaseResponseUser = {
    code?: number
    data?: User
    message?: string
  }

  type BaseResponseUserVO = {
    code?: number
    data?: UserVO
    message?: string
  }

  type BaseResponseVoid = {
    code?: number
    data?: Record<string, any>
    message?: string
  }

  type DeleteRequest = {
    id?: number
  }

  type getArticleParams = {
    taskId: string
  }

  type getExecutionLogsParams = {
    taskId: string
  }

  type getProgressParams = {
    taskId: string
  }

  type getUserByIdParams = {
    id: number
  }

  type getUserVOByIdParams = {
    id: number
  }

  type ImageItem = {
    position?: number
    url?: string
    method?: string
    keywords?: string
    sectionTitle?: string
    description?: string
  }

  type LoginUserVO = {
    id?: number
    userAccount?: string
    userName?: string
    userAvatar?: string
    userProfile?: string
    userRole?: string
    quota?: number
    vipTime?: string
    createTime?: string
    updateTime?: string
  }

  type OutlineItem = {
    section?: number
    title?: string
    points?: string[]
  }

  type OutlineSection = {
    section?: number
    title?: string
    points?: string[]
  }

  type PageArticleVO = {
    records?: ArticleVO[]
    pageNumber?: number
    pageSize?: number
    totalPage?: number
    totalRow?: number
    optimizeCountQuery?: boolean
  }

  type PageUserVO = {
    records?: UserVO[]
    pageNumber?: number
    pageSize?: number
    totalPage?: number
    totalRow?: number
    optimizeCountQuery?: boolean
  }

  type PaymentRecord = {
    id?: number
    userId?: number
    stripeSessionId?: string
    stripePaymentIntentId?: string
    amount?: number
    currency?: string
    status?: string
    productType?: string
    description?: string
    refundTime?: string
    refundReason?: string
    createTime?: string
    updateTime?: string
  }

  type refundParams = {
    reason?: string
  }

  type SseEmitter = {
    timeout?: number
  }

  type StatisticsVO = {
    todayCount?: number
    weekCount?: number
    monthCount?: number
    totalCount?: number
    successRate?: number
    avgDurationMs?: number
    activeUserCount?: number
    totalUserCount?: number
    vipUserCount?: number
    quotaUsed?: number
  }

  type TitleOption = {
    mainTitle?: string
    subTitle?: string
  }

  type User = {
    id?: number
    userAccount?: string
    userPassword?: string
    userName?: string
    userAvatar?: string
    userProfile?: string
    userRole?: string
    quota?: number
    vipTime?: string
    editTime?: string
    createTime?: string
    updateTime?: string
    isDelete?: number
  }

  type UserAddRequest = {
    userName?: string
    userAccount?: string
    userAvatar?: string
    userProfile?: string
    userRole?: string
  }

  type UserLoginRequest = {
    userAccount?: string
    userPassword?: string
  }

  type UserQueryRequest = {
    pageNum?: number
    pageSize?: number
    sortField?: string
    sortOrder?: string
    id?: number
    userName?: string
    userAccount?: string
    userProfile?: string
    userRole?: string
  }

  type UserRegisterRequest = {
    userAccount?: string
    userPassword?: string
    checkPassword?: string
  }

  type UserUpdateRequest = {
    id?: number
    userName?: string
    userAvatar?: string
    userProfile?: string
    userRole?: string
  }

  type UserVO = {
    id?: number
    userAccount?: string
    userName?: string
    userAvatar?: string
    userProfile?: string
    userRole?: string
    createTime?: string
  }

  // ========== 小说相关类型 ==========

  type NovelVO = {
    id?: number
    userId?: number
    title?: string
    genre?: string
    targetReaders?: string
    targetWordCount?: number
    worldSetting?: Record<string, any>
    volumeOutline?: Record<string, any>[]
    styleGuide?: Record<string, any>
    synopsis?: string
    status?: string
    phase?: string
    currentChapterNumber?: number
    currentVolumeNumber?: number
    totalWordCount?: number
    createTime?: string
    updateTime?: string
  }

  type ChapterVO = {
    id?: number
    novelId?: number
    volumeNumber?: number
    chapterNumber?: number
    title?: string
    outline?: Record<string, any>
    chapterMemo?: Record<string, any>
    content?: string
    summary?: string
    endingState?: Record<string, any>
    qualityReport?: Record<string, any>
    wordCount?: number
    characterStates?: Record<string, any>
    contextSnapshotId?: number
    status?: string
    createTime?: string
    updateTime?: string
  }

  type CharacterVO = {
    id?: number
    novelId?: number
    name?: string
    aliases?: string[]
    roleType?: string
    isCore?: boolean
    appearance?: string
    personality?: string
    background?: string
    skills?: string[]
    speechStyle?: string
    currentLocation?: string
    currentStatus?: string
    relationshipMap?: Record<string, any>
    firstAppearanceChapterId?: number
    lastAppearanceChapterId?: number
    notes?: string
    createTime?: string
    updateTime?: string
  }

  type ForeshadowingVO = {
    id?: number
    novelId?: number
    surface?: string
    hiddenTruth?: string
    category?: string
    relatedCharacters?: string[]
    relatedLocations?: string[]
    relatedSkills?: string[]
    plantedChapterId?: number
    targetChapter?: string
    resolvedChapterId?: number
    keywords?: string[]
    importance?: number
    status?: string
    lifecycleStage?: string
    mentionHistory?: Record<string, any>[]
    lastMentionedChapter?: number
    lastActionType?: string
    lastActionChapter?: number
    lastActionNote?: string
    createTime?: string
    updateTime?: string
  }

  type NovelCreateRequest = {
    title?: string
    genre?: string
    targetReaders?: string
    targetWordCount?: number
    coreIdea?: string
    initialCharacters?: Record<string, any>[]
  }

  type NovelIdeaEnhanceRequest = {
    rawIdea?: string
    genre?: string
    targetReaders?: string
    requirements?: string
  }

  type NovelSettingUpdateRequest = {
    worldSetting?: Record<string, any>
    volumeOutline?: Record<string, any>[]
    styleGuide?: Record<string, any>
  }

  type StyleAnalyzeRequest = {
    samples?: string
  }

  type ChapterPlanRequest = {
    authorIntent?: string
  }

  type ChapterGenerateRequest = {
    outline?: Record<string, any>
    chapterId?: number
    authorNote?: string
  }

  type ChapterRegenerateRequest = {
    authorNote?: string
  }

  type ChapterConfirmRequest = {
    content?: string
  }

  type ChapterContentUpdateRequest = {
    content?: string
  }

  type CharacterCreateRequest = {
    name?: string
    aliases?: string[]
    roleType?: string
    isCore?: boolean
    appearance?: string
    personality?: string
    background?: string
    skills?: string[]
    speechStyle?: string
  }

  type CharacterUpdateRequest = {
    name?: string
    aliases?: string[]
    roleType?: string
    isCore?: boolean
    appearance?: string
    personality?: string
    background?: string
    skills?: string[]
    speechStyle?: string
    currentLocation?: string
    currentStatus?: string
    notes?: string
  }

  type ForeshadowingCreateRequest = {
    surface?: string
    hiddenTruth?: string
    category?: string
    relatedCharacters?: string[]
    keywords?: string[]
    targetChapter?: string
    importance?: number
  }

  type ForeshadowingUpdateRequest = {
    surface?: string
    hiddenTruth?: string
    category?: string
    relatedCharacters?: string[]
    keywords?: string[]
    targetChapter?: string
    importance?: number
  }

  type ConsistencyIssue = {
    type?: string
    severity?: string
    description?: string
    chapters?: number[]
    suggestion?: string
    paragraphIndex?: number
    evidenceText?: string
    startOffset?: number
    endOffset?: number
  }

  type ContextSnapshotVO = {
    id?: number
    novelId?: number
    chapterId?: number
    contextData?: Record<string, any>
    promptData?: Record<string, any>
    traceData?: Record<string, any>
    version?: string
    createTime?: string
  }

  type ChapterVersionVO = {
    id?: number
    novelId?: number
    chapterId?: number
    versionType?: string
    content?: string
    contentLength?: number
    contentPreview?: string
    metaData?: Record<string, any>
    createTime?: string
  }

  type ConsistencyReport = {
    issues?: ConsistencyIssue[]
    summary?: string
  }

  type TaskEventVO = {
    type?: string
    data?: any
  }

  type TaskStatusVO = {
    taskId?: string
    taskType?: string
    status?: string
    novelId?: number
    chapterId?: number
    chapterNumber?: number
    phase?: string
    result?: Record<string, any>
    error?: string
    events?: TaskEventVO[]
  }

  type BaseResponseNovelVO = {
    code?: number
    data?: NovelVO
    message?: string
  }

  type BaseResponseDict = {
    code?: number
    data?: Record<string, any>
    message?: string
  }

  type BaseResponseListNovelVO = {
    code?: number
    data?: NovelVO[]
    message?: string
  }

  type BaseResponseListChapterVO = {
    code?: number
    data?: ChapterVO[]
    message?: string
  }

  type BaseResponseChapterVO = {
    code?: number
    data?: ChapterVO
    message?: string
  }

  type BaseResponseListCharacterVO = {
    code?: number
    data?: CharacterVO[]
    message?: string
  }

  type BaseResponseListForeshadowingVO = {
    code?: number
    data?: ForeshadowingVO[]
    message?: string
  }

  type BaseResponseConsistencyReport = {
    code?: number
    data?: ConsistencyReport
    message?: string
  }

  type BaseResponseTaskStatusVO = {
    code?: number
    data?: TaskStatusVO
    message?: string
  }

  type BaseResponseContextSnapshotVO = {
    code?: number
    data?: ContextSnapshotVO
    message?: string
  }

  type BaseResponseListChapterVersionVO = {
    code?: number
    data?: ChapterVersionVO[]
    message?: string
  }

  type getNovelParams = {
    novelId: number
  }

  type getChapterParams = {
    chapterId: number
  }

  type getChapterContextSnapshotParams = {
    chapterId: number
  }

  type getChapterVersionsParams = {
    chapterId: number
    includeContent?: boolean
  }

  type getNovelTaskStatusParams = {
    taskId: string
  }
}
