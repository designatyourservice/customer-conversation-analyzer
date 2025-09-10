-- Script para criar banco SQLite e importar dados CSV do Talqui
-- Execução: sqlite3 talqui.db < create_talqui_database.sql

-- Criar tabelas temporárias para importar CSVs
CREATE TABLE temp_messages (
    tenantID TEXT,
    contactID TEXT,
    messageID TEXT,
    sessionID TEXT,
    operatorID TEXT,
    messageAutonomous TEXT,
    messageExternalID TEXT,
    messageChannel TEXT,
    messageDirection TEXT,
    messageKey TEXT,
    messageValue TEXT,
    messageMeta TEXT,
    messageStatus TEXT,
    messageFingerprint TEXT,
    createdAt TEXT,
    updatedAt TEXT
);

CREATE TABLE temp_operator (
    organizationID TEXT,
    tenantID TEXT,
    contactID TEXT,
    sessionID TEXT,
    operatorID TEXT,
    sessionChannel TEXT,
    pluginConnectionID TEXT,
    sessionTags TEXT,
    sessionLastTag TEXT,
    sessionActive TEXT,
    sessionKind TEXT,
    sessionInitiator TEXT,
    sessionType TEXT,
    sessionStatus TEXT,
    sessionMeta TEXT,
    sessionLastMessageID TEXT,
    sessionRatingStars TEXT,
    sessionRatingAt TEXT,
    queuedAt TEXT,
    manualAt TEXT,
    closedAt TEXT,
    closeMotive TEXT,
    createdAt TEXT,
    updatedAt TEXT,
    __sessionMessagesCount TEXT,
    __sessionMostActiveOperatorID TEXT,
    __sessionDuration TEXT,
    __sessionQueueDuration TEXT,
    __sessionManualDuration TEXT,
    operatorFirstname TEXT
);

CREATE TABLE temp_sessions_plugin (
    organizationID TEXT,
    tenantID TEXT,
    contactID TEXT,
    sessionID TEXT,
    operatorID TEXT,
    sessionChannel TEXT,
    pluginConnectionID TEXT,
    sessionTags TEXT,
    sessionLastTag TEXT,
    sessionActive TEXT,
    sessionKind TEXT,
    sessionInitiator TEXT,
    sessionType TEXT,
    sessionStatus TEXT,
    sessionMeta TEXT,
    sessionLastMessageID TEXT,
    sessionRatingStars TEXT,
    sessionRatingAt TEXT,
    queuedAt TEXT,
    manualAt TEXT,
    closedAt TEXT,
    closeMotive TEXT,
    createdAt TEXT,
    updatedAt TEXT,
    __sessionMessagesCount TEXT,
    __sessionMostActiveOperatorID TEXT,
    __sessionDuration TEXT,
    __sessionQueueDuration TEXT,
    __sessionManualDuration TEXT,
    pluginConnectionLabel TEXT
);

-- Importar dados dos CSVs
.mode csv
.headers on
.import talqui-messages.csv temp_messages
.import talqui-operator.csv temp_operator  
.import talqui-sessions-plugin.csv temp_sessions_plugin

-- Criar tabela principal com JOIN session-centric
CREATE TABLE talqui_unified AS
WITH sessions_merged AS (
    -- Merge das tabelas de sessão (operator + plugin)
    SELECT 
        organizationID,
        tenantID,
        contactID,
        sessionID,
        operatorID,
        sessionChannel,
        pluginConnectionID,
        sessionTags,
        sessionLastTag,
        CASE WHEN sessionActive = 'True' THEN 1 ELSE 0 END as sessionActive,
        sessionKind,
        sessionInitiator,
        sessionType,
        CAST(sessionStatus as INTEGER) as sessionStatus,
        sessionMeta,
        sessionLastMessageID,
        CAST(sessionRatingStars as REAL) as sessionRatingStars,
        datetime(sessionRatingAt) as sessionRatingAt,
        datetime(queuedAt) as queuedAt,
        datetime(manualAt) as manualAt,
        datetime(closedAt) as closedAt,
        closeMotive,
        datetime(createdAt) as session_createdAt,
        datetime(updatedAt) as session_updatedAt,
        CAST(__sessionMessagesCount as INTEGER) as sessionMessagesCount,
        __sessionMostActiveOperatorID,
        CAST(__sessionDuration as INTEGER) as sessionDuration,
        CAST(__sessionQueueDuration as REAL) as sessionQueueDuration,
        CAST(__sessionManualDuration as REAL) as sessionManualDuration,
        operatorFirstname as operator_info,
        'operator' as data_source
    FROM temp_operator
    
    UNION ALL
    
    SELECT 
        organizationID,
        tenantID,
        contactID,
        sessionID,
        operatorID,
        sessionChannel,
        pluginConnectionID,
        sessionTags,
        sessionLastTag,
        CASE WHEN sessionActive = 'True' THEN 1 ELSE 0 END as sessionActive,
        sessionKind,
        sessionInitiator,
        sessionType,
        CAST(sessionStatus as INTEGER) as sessionStatus,
        sessionMeta,
        sessionLastMessageID,
        CAST(sessionRatingStars as REAL) as sessionRatingStars,
        datetime(sessionRatingAt) as sessionRatingAt,
        datetime(queuedAt) as queuedAt,
        datetime(manualAt) as manualAt,
        datetime(closedAt) as closedAt,
        closeMotive,
        datetime(createdAt) as session_createdAt,
        datetime(updatedAt) as session_updatedAt,
        CAST(__sessionMessagesCount as INTEGER) as sessionMessagesCount,
        __sessionMostActiveOperatorID,
        CAST(__sessionDuration as INTEGER) as sessionDuration,
        CAST(__sessionQueueDuration as REAL) as sessionQueueDuration,
        CAST(__sessionManualDuration as REAL) as sessionManualDuration,
        pluginConnectionLabel as operator_info,
        'plugin' as data_source
    FROM temp_sessions_plugin
)

-- JOIN principal: Sessions LEFT JOIN Messages
SELECT 
    -- Chaves primárias
    s.sessionID,
    m.messageID,
    
    -- Identificadores hierárquicos
    s.organizationID,
    s.tenantID,
    s.contactID,
    s.operatorID,
    
    -- Dados de sessão
    s.sessionChannel,
    s.pluginConnectionID,
    s.sessionTags,
    s.sessionLastTag,
    s.sessionActive,
    s.sessionKind,
    s.sessionInitiator,
    s.sessionType,
    s.sessionStatus,
    s.sessionMeta,
    s.sessionLastMessageID,
    s.sessionRatingStars,
    s.sessionRatingAt,
    s.queuedAt,
    s.manualAt,
    s.closedAt,
    s.closeMotive,
    s.session_createdAt,
    s.session_updatedAt,
    s.sessionMessagesCount,
    s.__sessionMostActiveOperatorID,
    s.sessionDuration,
    s.sessionQueueDuration,
    s.sessionManualDuration,
    s.operator_info,
    s.data_source,
    
    -- Dados de mensagem
    CASE WHEN m.messageAutonomous = 'True' THEN 1 ELSE 0 END as messageAutonomous,
    m.messageExternalID,
    m.messageChannel,
    m.messageDirection,
    m.messageKey,
    m.messageValue,
    m.messageMeta,
    CAST(m.messageStatus as REAL) as messageStatus,
    m.messageFingerprint,
    datetime(m.createdAt) as message_createdAt,
    datetime(m.updatedAt) as message_updatedAt

FROM sessions_merged s
LEFT JOIN temp_messages m 
    ON s.sessionID = m.sessionID 
    AND s.tenantID = m.tenantID 
    AND s.contactID = m.contactID

ORDER BY s.session_createdAt, datetime(m.createdAt);

-- Criar índices para performance
CREATE INDEX idx_talqui_session ON talqui_unified(sessionID);
CREATE INDEX idx_talqui_tenant_contact ON talqui_unified(tenantID, contactID);
CREATE INDEX idx_talqui_operator ON talqui_unified(operatorID);
CREATE INDEX idx_talqui_dates ON talqui_unified(session_createdAt, message_createdAt);

-- Criar views para análises específicas

-- View 1: Resumo por sessão
CREATE VIEW session_summary AS
SELECT 
    sessionID,
    tenantID,
    contactID,
    operatorID,
    operator_info,
    sessionKind,
    sessionStatus,
    sessionDuration,
    sessionMessagesCount,
    COUNT(messageID) as actual_message_count,
    MIN(message_createdAt) as first_message_at,
    MAX(message_createdAt) as last_message_at,
    session_createdAt,
    closedAt,
    closeMotive
FROM talqui_unified 
GROUP BY sessionID, tenantID, contactID;

-- View 2: Métricas de operador
CREATE VIEW operator_metrics AS
SELECT 
    operator_info,
    operatorID,
    COUNT(DISTINCT sessionID) as total_sessions,
    COUNT(messageID) as total_messages,
    AVG(sessionDuration) as avg_session_duration,
    AVG(sessionQueueDuration) as avg_queue_time,
    COUNT(CASE WHEN closeMotive = 'INACTIVITY' THEN 1 END) as inactivity_closures,
    MIN(session_createdAt) as first_session,
    MAX(session_createdAt) as last_session
FROM talqui_unified 
WHERE operator_info IS NOT NULL
GROUP BY operator_info, operatorID;

-- View 3: Análise de mensagens
CREATE VIEW message_analysis AS
SELECT 
    sessionID,
    messageDirection,
    messageKey,
    messageAutonomous,
    COUNT(*) as message_count,
    AVG(messageStatus) as avg_status
FROM talqui_unified 
WHERE messageID IS NOT NULL
GROUP BY sessionID, messageDirection, messageKey, messageAutonomous;

-- Remover tabelas temporárias
DROP TABLE temp_messages;
DROP TABLE temp_operator;
DROP TABLE temp_sessions_plugin;

-- Estatísticas finais
SELECT 'Total de registros na tabela unificada:' as info, COUNT(*) as count FROM talqui_unified
UNION ALL
SELECT 'Sessões únicas:', COUNT(DISTINCT sessionID) FROM talqui_unified
UNION ALL
SELECT 'Mensagens únicas:', COUNT(DISTINCT messageID) FROM talqui_unified WHERE messageID IS NOT NULL
UNION ALL
SELECT 'Operadores únicos:', COUNT(DISTINCT operator_info) FROM talqui_unified WHERE operator_info IS NOT NULL;