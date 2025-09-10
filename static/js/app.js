// Conversation Analyzer - JavaScript Application

class ConversationAnalyzer {
    constructor() {
        this.selectedConversation = null;
        this.currentFilters = {};
        this.conversations = [];
        this.filtersData = {};
        
        this.init();
    }
    
    async init() {
        try {
            this.showLoading(true);
            
            // Carregar dados iniciais
            await this.loadFiltersData();
            await this.loadStats();
            await this.loadConversations();
            
            // Setup event listeners
            this.setupEventListeners();
            
            this.showLoading(false);
        } catch (error) {
            console.error('Erro na inicialização:', error);
            this.showError('Erro ao carregar dados iniciais');
            this.showLoading(false);
        }
    }
    
    setupEventListeners() {
        // Clear filters
        document.getElementById('clearFilters').addEventListener('click', () => {
            this.clearFilters();
        });
        
        // Search box removido - funcionalidade não mais necessária
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSelection();
            }
        });
    }
    
    async loadFiltersData() {
        try {
            const response = await fetch('/api/filters');
            const result = await response.json();
            
            if (result.success) {
                this.filtersData = result.data;
                this.renderFilters();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao carregar filtros:', error);
            throw error;
        }
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const result = await response.json();
            
            if (result.success) {
                this.renderStats(result.data);
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
        }
    }
    
    async loadConversations() {
        try {
            const queryParams = new URLSearchParams();
            
            // Adicionar filtros ativos
            Object.keys(this.currentFilters).forEach(key => {
                if (this.currentFilters[key] !== null && this.currentFilters[key] !== undefined) {
                    queryParams.set(key, this.currentFilters[key]);
                }
            });
            
            const response = await fetch(`/api/conversations?${queryParams}`);
            const result = await response.json();
            
            if (result.success) {
                this.conversations = result.data.conversations;
                this.totalCount = result.data.total_count;
                this.renderConversations();
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Erro ao carregar conversas:', error);
            throw error;
        }
    }
    
    renderStats(stats) {
        const statsContainer = document.getElementById('headerStats');
        statsContainer.innerHTML = `
            <div class="stat-item">
                <div class="stat-value">${stats.total_conversations.toLocaleString()}</div>
                <div class="stat-label">Conversas</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${(stats.avg_confidence * 100).toFixed(1)}%</div>
                <div class="stat-label">Confiança Média</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${stats.handoff_rate}%</div>
                <div class="stat-label">Taxa Transbordo</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">${stats.unique_agents}</div>
                <div class="stat-label">Agentes</div>
            </div>
        `;
    }
    
    renderFilters() {
        // Renderizar categorias
        this.renderFilterSection('categoryFilter', this.filtersData.categories, 'category');
        
        // Renderizar subcategorias
        this.renderFilterSection('subcategoryFilter', this.filtersData.subcategories, 'subcategory');
        
        // Renderizar agentes
        this.renderFilterSection('agentFilter', this.filtersData.agents, 'agent');
        
        // Renderizar faixas de confiança
        this.renderConfidenceFilter();
        
        // Renderizar status de transbordo
        this.renderHandoffFilter();
        
        // Renderizar status RLHF
        this.renderRlhfFilter();
    }
    
    renderFilterSection(containerId, items, filterKey) {
        const container = document.getElementById(containerId);
        
        if (!items || items.length === 0) {
            container.innerHTML = '<div class="no-data">Nenhum dado disponível</div>';
            return;
        }
        
        container.innerHTML = items.map(item => `
            <div class="filter-item" data-filter="${filterKey}" data-value="${item.name}">
                <span class="filter-name">${item.name || 'Não definido'}</span>
                <span class="filter-count">${item.count}</span>
            </div>
        `).join('');
        
        // Event listeners para filtros
        container.querySelectorAll('.filter-item').forEach(item => {
            item.addEventListener('click', () => {
                this.toggleFilter(item);
            });
        });
    }
    
    renderConfidenceFilter() {
        const container = document.getElementById('confidenceFilter');
        
        container.innerHTML = this.filtersData.confidence_ranges.map(range => `
            <div class="filter-item" data-filter="confidence" data-min="${range.min}" data-max="${range.max}">
                <span class="filter-name">${range.name}</span>
                <span class="filter-count">-</span>
            </div>
        `).join('');
        
        // Event listeners
        container.querySelectorAll('.filter-item').forEach(item => {
            item.addEventListener('click', () => {
                this.toggleConfidenceFilter(item);
            });
        });
    }
    
    renderHandoffFilter() {
        const container = document.getElementById('handoffFilter');
        
        container.innerHTML = this.filtersData.handoff_status.map(status => `
            <div class="filter-item" data-filter="handoff" data-value="${status.name === 'Com Transbordo' ? 'true' : 'false'}">
                <span class="filter-name">${status.name}</span>
                <span class="filter-count">${status.count}</span>
            </div>
        `).join('');
        
        // Event listeners
        container.querySelectorAll('.filter-item').forEach(item => {
            item.addEventListener('click', () => {
                this.toggleHandoffFilter(item);
            });
        });
    }
    
    renderRlhfFilter() {
        const container = document.getElementById('rlhfFilter');
        
        // Opções do filtro RLHF com "Não Validado" como padrão selecionado
        const rlhfOptions = [
            { name: 'Todos', value: 'all', count: '-' },
            { name: 'Validado', value: 'true', count: this.filtersData.rlhf_status.find(s => s.name === 'Validado')?.count || 0 },
            { name: 'Não Validado', value: 'false', count: this.filtersData.rlhf_status.find(s => s.name === 'Não Validado')?.count || 0 }
        ];
        
        container.innerHTML = rlhfOptions.map(option => `
            <div class="filter-item ${option.value === 'false' ? 'active' : ''}" data-filter="rlhf" data-value="${option.value}">
                <span class="filter-name">${option.name}</span>
                <span class="filter-count">${option.count}</span>
            </div>
        `).join('');
        
        // Definir filtro padrão "Não Validado"
        this.currentFilters['rlhf'] = 'false';
        
        // Event listeners
        container.querySelectorAll('.filter-item').forEach(item => {
            item.addEventListener('click', () => {
                this.toggleRlhfFilter(item);
            });
        });
    }
    
    renderConversations() {
        const container = document.getElementById('conversationsList');
        const countElement = document.getElementById('conversationCount');
        
        countElement.textContent = `(${this.totalCount || 0})`;
        
        if (this.conversations.length === 0) {
            container.innerHTML = `
                <div class="no-conversations">
                    <i class="fas fa-inbox"></i>
                    <h3>Nenhuma conversa encontrada</h3>
                    <p>Ajuste os filtros para ver mais resultados</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.conversations.map(conv => {
            const confidenceLevel = this.getConfidenceLevel(conv.confidence);
            const confidenceWidth = (conv.confidence * 100);
            
            return `
                <div class="conversation-item" data-session-id="${conv.sessionID}">
                    <div class="conversation-header">
                        <div class="conversation-id">${conv.sessionID.substring(0, 8)}...</div>
                        <div class="conversation-date">
                            ${new Date(conv.classified_at).toLocaleDateString('pt-BR')}
                            ${conv.rlhf ? '<i class="fas fa-check-circle rlhf-check" title="Validado por RLHF"></i>' : ''}
                        </div>
                    </div>
                    <div class="conversation-summary">
                        ${conv.summary || 'Sem resumo disponível'}
                    </div>
                    <div class="conversation-meta">
                        <div class="confidence-bar">
                            <span class="confidence-value">${(conv.confidence * 100).toFixed(1)}%</span>
                            <div class="confidence-indicator">
                                <div class="confidence-fill ${confidenceLevel}" style="width: ${confidenceWidth}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        // Event listeners para conversas
        container.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectConversation(item);
            });
        });
    }
    
    async selectConversation(element) {
        try {
            // Marcar como selecionado
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.remove('selected');
            });
            element.classList.add('selected');
            
            const sessionId = element.dataset.sessionId;
            this.selectedConversationId = sessionId;
            
            this.showLoading(true);
            
            // Carregar detalhes da conversa
            const response = await fetch(`/api/conversation/${sessionId}`);
            const result = await response.json();
            
            if (result.success) {
                this.selectedConversation = result.data;
                this.renderConversationViewer();
                this.renderConversationInfo();
            } else {
                throw new Error(result.error);
            }
            
            this.showLoading(false);
            
        } catch (error) {
            console.error('Erro ao carregar conversa:', error);
            this.showError('Erro ao carregar detalhes da conversa');
            this.showLoading(false);
        }
    }
    
    renderConversationViewer() {
        const container = document.getElementById('conversationViewer');
        
        if (!this.selectedConversation || !this.selectedConversation.messages) {
            container.innerHTML = `
                <div class="viewer-placeholder">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Erro ao carregar conversa</h3>
                    <p>Não foi possível carregar as mensagens desta conversa</p>
                </div>
            `;
            return;
        }
        
        const messages = this.selectedConversation.messages;
        
        container.innerHTML = `
            <div class="messages-container">
                ${messages.map(message => this.renderMessage(message)).join('')}
            </div>
            <div class="template-section">
                <div class="template-question">
                    <p><strong>Essa conversa deve ser usado como modelo para treinamento?</strong></p>
                    <div class="template-checkbox-container">
                        <input type="checkbox" 
                               id="templateCheckbox" 
                               class="template-checkbox" 
                               data-session-id="${this.selectedConversationId || ''}"
                               ${this.selectedConversation.session_info?.template ? 'checked' : ''}>
                        <label for="templateCheckbox" class="template-checkbox-label">
                            <span class="template-checkbox-custom"></span>
                            ${this.selectedConversation.session_info?.template ? 'Sim, usar como template' : 'Não usar como template'}
                        </label>
                    </div>
                </div>
            </div>
        `;
        
        // Scroll para o final
        container.scrollTop = container.scrollHeight;
        
        // Setup event listeners for template checkbox
        this.setupEditableFields();
    }
    
    renderMessage(message) {
        if (!message.content || message.content.trim() === '') {
            return '';
        }
        
        const isOutbound = message.direction === 'outbound';
        const timestamp = new Date(message.timestamp).toLocaleString('pt-BR');
        const avatarText = isOutbound ? 'A' : 'C';
        
        return `
            <div class="message ${message.direction}">
                <div class="message-avatar">${avatarText}</div>
                <div class="message-content">
                    <div class="message-bubble">
                        ${this.formatMessageContent(message.content)}
                    </div>
                    <div class="message-meta">
                        <span class="message-time">${timestamp}</span>
                        ${message.operator_info ? `<span class="operator-info">${message.operator_info}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    formatMessageContent(content) {
        // Escapar HTML e formatar quebras de linha
        return content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/\n/g, '<br>')
            .replace(/\*([^*]+)\*/g, '<strong>$1</strong>'); // Bold para *texto*
    }
    
    renderConversationInfo() {
        const container = document.getElementById('conversationInfo');
        
        if (!this.selectedConversation || !this.selectedConversation.session_info) {
            container.innerHTML = `
                <div class="info-placeholder">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Informações não disponíveis</p>
                </div>
            `;
            return;
        }
        
        const info = this.selectedConversation.session_info;
        const effectivenessLevel = this.getEffectivenessLevel(info.effectiveness_score);
        
        container.innerHTML = `
            <div class="info-section">
                <h4><i class="fas fa-tags"></i> Tags & Status</h4>
                <div class="tags-display">
                    <span class="info-tag category">${info.category}</span>
                    ${info.primary_agent ? `<span class="info-tag agent">${info.primary_agent}</span>` : ''}
                    <span class="info-tag ${info.has_handoff ? 'handoff' : 'no-handoff'}">
                        ${info.has_handoff ? 'Com Transbordo' : 'Sem Transbordo'}
                    </span>
                    <span class="info-tag rlhf ${info.rlhf ? 'rlhf-true' : 'rlhf-false'}">
                        RLHF ${info.rlhf ? '✅' : '❌'}
                    </span>
                </div>
            </div>
            
            <div class="info-section">
                <h4><i class="fas fa-tag"></i> Classificação</h4>
                <div class="info-item editable-item">
                    <span class="info-label">Categoria:</span>
                    <span class="info-value highlight editable-field" data-field="category" data-session-id="${this.selectedConversationId || ''}">${info.category}</span>
                    <i class="fas fa-edit edit-icon" title="Clique para editar"></i>
                </div>
                <div class="info-item editable-item">
                    <span class="info-label">Subcategoria:</span>
                    <span class="info-value editable-field" data-field="subcategory" data-session-id="${this.selectedConversationId || ''}">${info.subcategory}</span>
                    <i class="fas fa-edit edit-icon" title="Clique para editar"></i>
                </div>
                <div class="info-item">
                    <span class="info-label">Confiança:</span>
                    <span class="info-value highlight">${(info.confidence * 100).toFixed(1)}%</span>
                </div>
            </div>
            
            <div class="info-section">
                <h4><i class="fas fa-user"></i> Cliente</h4>
                <div class="info-item editable-item">
                    <span class="info-label">Nome:</span>
                    <span class="info-value editable-field" data-field="name" data-session-id="${this.selectedConversationId || ''}">${info.name || 'Não informado'}</span>
                    <i class="fas fa-edit edit-icon" title="Clique para editar"></i>
                </div>
                <div class="info-item editable-item">
                    <span class="info-label">Empresa:</span>
                    <span class="info-value editable-field" data-field="company" data-session-id="${this.selectedConversationId || ''}">${info.company || 'Não informado'}</span>
                    <i class="fas fa-edit edit-icon" title="Clique para editar"></i>
                </div>
                <div class="info-item editable-item">
                    <span class="info-label">ERP:</span>
                    <span class="info-value editable-field" data-field="erp" data-session-id="${this.selectedConversationId || ''}">${info.erp || 'Não informado'}</span>
                    <i class="fas fa-edit edit-icon" title="Clique para editar"></i>
                </div>
                <div class="info-item editable-item">
                    <span class="info-label">Canal:</span>
                    <span class="info-value editable-field" data-field="channel" data-session-id="${this.selectedConversationId || ''}">${info.channel || 'Não informado'}</span>
                    <i class="fas fa-edit edit-icon" title="Clique para editar"></i>
                </div>
                <div class="info-item editable-item">
                    <span class="info-label">Nº Cliente:</span>
                    <span class="info-value editable-field" data-field="customerNumber" data-session-id="${this.selectedConversationId || ''}">${info.customerNumber || 'Não informado'}</span>
                    <i class="fas fa-edit edit-icon" title="Clique para editar"></i>
                </div>
            </div>
            
            <div class="info-section">
                <h4><i class="fas fa-users"></i> Agentes</h4>
                <div class="info-item">
                    <span class="info-label">Agente Principal:</span>
                    <span class="info-value highlight">${info.primary_agent || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Agente Final:</span>
                    <span class="info-value">${info.final_agent || 'N/A'}</span>
                </div>
            </div>
            
            <div class="effectiveness-score ${effectivenessLevel}">
                <div class="score-value">${(info.effectiveness_score * 100).toFixed(0)}%</div>
                <div class="score-label">Eficácia</div>
            </div>
            
            <div class="handoff-info ${info.has_handoff ? '' : 'no-handoff'}">
                <h5><i class="fas fa-exchange-alt"></i> Status do Atendimento</h5>
                ${info.has_handoff ? `
                    <p><strong>Com Transbordo</strong> (${info.handoff_count} transferência${info.handoff_count > 1 ? 's' : ''})</p>
                    <div class="handoff-path">
                        <span class="agent-name">${info.primary_agent}</span>
                        <i class="fas fa-arrow-right handoff-arrow"></i>
                        <span class="agent-name">${info.final_agent}</span>
                    </div>
                ` : `
                    <p><strong>Sem Transbordo</strong></p>
                    <p>Resolvido diretamente por ${info.primary_agent || 'agente inicial'}</p>
                `}
            </div>
            
            <div class="info-section">
                <h4><i class="fas fa-exchange-alt"></i> Configuração Handoff</h4>
                <div class="info-item handoff-checkbox-item">
                    <span class="info-label">Handoff Ativo:</span>
                    <div class="checkbox-container">
                        <input type="checkbox" 
                               id="handoffCheckbox" 
                               class="editable-checkbox" 
                               data-field="has_handoff" 
                               data-session-id="${this.selectedConversationId || ''}"
                               ${info.has_handoff ? 'checked' : ''}>
                        <label for="handoffCheckbox" class="checkbox-label">
                            <span class="checkbox-custom"></span>
                            ${info.has_handoff ? 'Sim' : 'Não'}
                        </label>
                    </div>
                </div>
                <div class="info-item resolution-checkbox-item">
                    <span class="info-label">Resolução:</span>
                    <div class="checkbox-container">
                        <input type="checkbox" 
                               id="resolutionCheckbox" 
                               class="editable-checkbox" 
                               data-field="resolution" 
                               data-session-id="${this.selectedConversationId || ''}"
                               ${info.resolution ? 'checked' : ''}>
                        <label for="resolutionCheckbox" class="checkbox-label">
                            <span class="checkbox-custom"></span>
                            ${info.resolution ? 'Resolvido' : 'Pendente'}
                        </label>
                    </div>
                </div>
            </div>
            
            <div class="info-section">
                <h4><i class="fas fa-chart-line"></i> Métricas</h4>
                <div class="info-item">
                    <span class="info-label">Mensagens:</span>
                    <span class="info-value">${info.messages_analyzed}</span>
                </div>
                <div class="info-item rlhf-checkbox-item">
                    <span class="info-label">RLHF:</span>
                    <div class="checkbox-container">
                        <input type="checkbox" 
                               id="rlhfCheckbox" 
                               class="editable-checkbox" 
                               data-field="rlhf" 
                               data-session-id="${this.selectedConversationId || ''}"
                               ${info.rlhf ? 'checked' : ''}>
                        <label for="rlhfCheckbox" class="checkbox-label">
                            <span class="checkbox-custom"></span>
                            ${info.rlhf ? 'Validado' : 'Não validado'}
                        </label>
                    </div>
                </div>
                <div class="info-item">
                    <span class="info-label">Classificado em:</span>
                    <span class="info-value">${new Date(info.classified_at).toLocaleString('pt-BR')}</span>
                </div>
            </div>
            
            <div class="info-section">
                <h4><i class="fas fa-comment-alt"></i> Resumo</h4>
                <div class="summary-text">
                    ${info.summary || 'Sem resumo disponível'}
                </div>
            </div>
            
            ${info.reasoning ? `
                <div class="info-section">
                    <h4><i class="fas fa-brain"></i> Reasoning</h4>
                    <div class="reasoning-text">
                        ${info.reasoning}
                    </div>
                </div>
            ` : ''}
        `;
        
        // Add event listeners for editable fields
        this.setupEditableFields();
    }
    
    setupEditableFields() {
        const editableFields = document.querySelectorAll('.editable-field');
        
        editableFields.forEach(field => {
            field.addEventListener('click', (e) => {
                this.makeFieldEditable(e.target);
            });
            
            // Also add click listener to the edit icon
            const editIcon = field.parentElement.querySelector('.edit-icon');
            if (editIcon) {
                editIcon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.makeFieldEditable(field);
                });
            }
        });
        
        // Add event listener for handoff checkbox
        const handoffCheckbox = document.getElementById('handoffCheckbox');
        if (handoffCheckbox) {
            handoffCheckbox.addEventListener('change', (e) => {
                this.updateHandoffField(e.target);
            });
        }
        
        // Add event listener for resolution checkbox
        const resolutionCheckbox = document.getElementById('resolutionCheckbox');
        if (resolutionCheckbox) {
            resolutionCheckbox.addEventListener('change', (e) => {
                this.updateResolutionField(e.target);
            });
        }
        
        // Add event listener for template checkbox
        const templateCheckbox = document.getElementById('templateCheckbox');
        if (templateCheckbox) {
            templateCheckbox.addEventListener('change', (e) => {
                this.updateTemplateField(e.target);
            });
        }
        
        // Add event listener for RLHF checkbox
        const rlhfCheckbox = document.getElementById('rlhfCheckbox');
        if (rlhfCheckbox) {
            rlhfCheckbox.addEventListener('change', (e) => {
                this.updateRlhfField(e.target);
            });
        }
    }
    
    makeFieldEditable(fieldElement) {
        const currentValue = fieldElement.textContent.trim();
        const fieldType = fieldElement.dataset.field;
        const sessionId = fieldElement.dataset.sessionId;
        
        // Determine if this is a dropdown field or text field
        const isDropdownField = fieldType === 'category' || fieldType === 'subcategory';
        
        if (isDropdownField) {
            // Create select element for dropdown fields
            const select = document.createElement('select');
            select.className = 'field-editor-select';
            
            // Get options based on field type
            const options = fieldType === 'category' 
                ? this.filtersData.categories 
                : this.filtersData.subcategories;
            
            // Add options to select
            options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option.name;
                optionElement.textContent = option.name;
                if (option.name === currentValue) {
                    optionElement.selected = true;
                }
                select.appendChild(optionElement);
            });
            
            // Replace field with select
            fieldElement.style.display = 'none';
            fieldElement.parentElement.appendChild(select);
            
            // Focus the select
            select.focus();
            
            this.setupSelectHandlers(select, fieldElement, fieldType, sessionId);
        } else {
            // Create input element for text fields (name, company)
            const input = document.createElement('input');
            input.type = 'text';
            input.value = currentValue === 'Não informado' ? '' : currentValue;
            input.className = 'field-editor';
            const placeholders = {
                'name': 'Digite o nome do cliente',
                'company': 'Digite o nome da empresa',
                'erp': 'Digite o código ERP',
                'channel': 'Digite o canal',
                'customerNumber': 'Digite o número do cliente'
            };
            input.placeholder = placeholders[fieldType] || 'Digite o valor';
            
            // Replace field with input
            fieldElement.style.display = 'none';
            fieldElement.parentElement.appendChild(input);
            
            // Focus and select all text
            input.focus();
            input.select();
            
            this.setupInputHandlers(input, fieldElement, fieldType, sessionId);
        }
    }
    
    setupSelectHandlers(select, fieldElement, fieldType, sessionId) {
        const currentValue = fieldElement.textContent.trim();
        
        // Handle save on change or blur
        const saveEdit = async () => {
            const newValue = select.value.trim();
            
            if (newValue !== currentValue && newValue !== '') {
                try {
                    await this.updateConversationField(sessionId, fieldType, newValue);
                    fieldElement.textContent = newValue;
                    
                    // Update the local data
                    if (this.selectedConversation && this.selectedConversation.session_info) {
                        this.selectedConversation.session_info[fieldType] = newValue;
                        this.selectedConversation.session_info.rlhf = true;
                    }
                    
                    // Refresh the info panel to show updated RLHF status
                    this.renderConversationInfo();
                    
                } catch (error) {
                    console.error('Erro ao atualizar campo:', error);
                    this.showError('Erro ao salvar alteração');
                }
            }
            
            // Restore original field
            fieldElement.style.display = '';
            select.remove();
        };
        
        // Handle cancel on Escape
        const cancelEdit = () => {
            fieldElement.style.display = '';
            select.remove();
        };
        
        select.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveEdit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelEdit();
            }
        });
        
        select.addEventListener('change', saveEdit);
        select.addEventListener('blur', saveEdit);
    }
    
    setupInputHandlers(input, fieldElement, fieldType, sessionId) {
        const currentValue = fieldElement.textContent.trim();
        const originalValue = currentValue === 'Não informado' ? '' : currentValue;
        
        // Handle save on Enter or blur
        const saveEdit = async () => {
            const newValue = input.value.trim();
            
            if (newValue !== originalValue) {
                try {
                    await this.updateConversationField(sessionId, fieldType, newValue);
                    fieldElement.textContent = newValue || 'Não informado';
                    
                    // Update the local data
                    if (this.selectedConversation && this.selectedConversation.session_info) {
                        this.selectedConversation.session_info[fieldType] = newValue;
                        this.selectedConversation.session_info.rlhf = true;
                    }
                    
                    // Refresh the info panel to show updated RLHF status
                    this.renderConversationInfo();
                    
                } catch (error) {
                    console.error('Erro ao atualizar campo:', error);
                    this.showError('Erro ao salvar alteração');
                }
            }
            
            // Restore original field
            fieldElement.style.display = '';
            input.remove();
        };
        
        // Handle cancel on Escape
        const cancelEdit = () => {
            fieldElement.style.display = '';
            input.remove();
        };
        
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                saveEdit();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                cancelEdit();
            }
        });
        
        input.addEventListener('blur', saveEdit);
    }
    
    async updateConversationField(sessionId, fieldType, newValue) {
        if (!sessionId) {
            throw new Error('Session ID não encontrado');
        }
        
        const updateData = {};
        
        // Get current values to send complete update
        const currentInfo = this.selectedConversation?.session_info;
        if (!currentInfo) {
            throw new Error('Informações da sessão não disponíveis');
        }
        
        updateData.category = fieldType === 'category' ? newValue : currentInfo.category;
        updateData.subcategory = fieldType === 'subcategory' ? newValue : currentInfo.subcategory;
        
        const response = await fetch(`/api/conversation/${sessionId}/update`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Erro ao atualizar conversa');
        }
        
        return result;
    }
    
    async updateHandoffField(checkboxElement) {
        try {
            const sessionId = checkboxElement.dataset.sessionId;
            const newValue = checkboxElement.checked;
            
            if (!sessionId) {
                throw new Error('Session ID não encontrado');
            }
            
            // Get current values to send complete update
            const currentInfo = this.selectedConversation?.session_info;
            if (!currentInfo) {
                throw new Error('Informações da sessão não disponíveis');
            }
            
            const updateData = {
                category: currentInfo.category,
                subcategory: currentInfo.subcategory,
                has_handoff: newValue
            };
            
            const response = await fetch(`/api/conversation/${sessionId}/update`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData)
            });
            
            const result = await response.json();
            
            if (!result.success) {
                // Revert checkbox state on error
                checkboxElement.checked = !newValue;
                throw new Error(result.error || 'Erro ao atualizar handoff');
            }
            
            // Update the local data
            if (this.selectedConversation && this.selectedConversation.session_info) {
                this.selectedConversation.session_info.has_handoff = newValue;
                this.selectedConversation.session_info.rlhf = true;
            }
            
            // Update the label text
            const label = checkboxElement.nextElementSibling;
            if (label) {
                label.childNodes[1].textContent = newValue ? 'Sim' : 'Não';
            }
            
            // Refresh the info panel to show updated RLHF status and handoff info
            this.renderConversationInfo();
            
        } catch (error) {
            console.error('Erro ao atualizar handoff:', error);
            this.showError('Erro ao salvar alteração do handoff');
        }
    }
    
    async updateResolutionField(checkboxElement) {
        try {
            const sessionId = checkboxElement.dataset.sessionId;
            const newValue = checkboxElement.checked;
            
            if (!sessionId) {
                throw new Error('Session ID não encontrado');
            }
            
            // Get current values to send complete update
            const currentInfo = this.selectedConversation?.session_info;
            if (!currentInfo) {
                throw new Error('Informações da sessão não disponíveis');
            }
            
            const updateData = {
                category: currentInfo.category,
                subcategory: currentInfo.subcategory,
                resolution: newValue
            };
            
            const response = await fetch(`/api/conversation/${sessionId}/update`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData)
            });
            
            const result = await response.json();
            
            if (!result.success) {
                // Revert checkbox state on error
                checkboxElement.checked = !newValue;
                throw new Error(result.error || 'Erro ao atualizar resolution');
            }
            
            // Update the local data
            if (this.selectedConversation && this.selectedConversation.session_info) {
                this.selectedConversation.session_info.resolution = newValue;
                this.selectedConversation.session_info.rlhf = true;
            }
            
            // Update the label text
            const label = checkboxElement.nextElementSibling;
            if (label) {
                label.childNodes[1].textContent = newValue ? 'Resolvido' : 'Pendente';
            }
            
            // Refresh the info panel to show updated RLHF status
            this.renderConversationInfo();
            
        } catch (error) {
            console.error('Erro ao atualizar resolution:', error);
            this.showError('Erro ao salvar alteração da resolução');
        }
    }
    
    async updateTemplateField(checkboxElement) {
        try {
            const sessionId = checkboxElement.dataset.sessionId;
            const newValue = checkboxElement.checked;
            
            if (!sessionId) {
                throw new Error('Session ID não encontrado');
            }
            
            // Get current values to send complete update
            const currentInfo = this.selectedConversation?.session_info;
            if (!currentInfo) {
                throw new Error('Informações da sessão não disponíveis');
            }
            
            const updateData = {
                category: currentInfo.category,
                subcategory: currentInfo.subcategory,
                template: newValue
            };
            
            const response = await fetch(`/api/conversation/${sessionId}/update`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData)
            });
            
            const result = await response.json();
            
            if (!result.success) {
                // Revert checkbox state on error
                checkboxElement.checked = !newValue;
                throw new Error(result.error || 'Erro ao atualizar template');
            }
            
            // Update the local data
            if (this.selectedConversation && this.selectedConversation.session_info) {
                this.selectedConversation.session_info.template = newValue;
                this.selectedConversation.session_info.rlhf = true;
            }
            
            // Update the label text
            const label = checkboxElement.nextElementSibling;
            if (label) {
                label.childNodes[1].textContent = newValue ? 'Sim, usar como template' : 'Não usar como template';
            }
            
            // Show feedback message
            if (newValue) {
                this.showSuccess('Conversa marcada como template para treinamento');
            } else {
                this.showSuccess('Conversa removida dos templates de treinamento');
            }
            
        } catch (error) {
            console.error('Erro ao atualizar template:', error);
            this.showError('Erro ao salvar configuração de template');
        }
    }
    
    async updateRlhfField(checkboxElement) {
        try {
            const sessionId = checkboxElement.dataset.sessionId;
            const newValue = checkboxElement.checked;
            
            if (!sessionId) {
                throw new Error('Session ID não encontrado');
            }
            
            // Get current values to send complete update
            const currentInfo = this.selectedConversation?.session_info;
            if (!currentInfo) {
                throw new Error('Informações da sessão não disponíveis');
            }
            
            const updateData = {
                category: currentInfo.category,
                subcategory: currentInfo.subcategory,
                rlhf: newValue
            };
            
            const response = await fetch(`/api/conversation/${sessionId}/update`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData)
            });
            
            const result = await response.json();
            
            if (!result.success) {
                // Revert checkbox state on error
                checkboxElement.checked = !newValue;
                throw new Error(result.error || 'Erro ao atualizar RLHF');
            }
            
            // Update the local data
            if (this.selectedConversation && this.selectedConversation.session_info) {
                this.selectedConversation.session_info.rlhf = newValue;
            }
            
            // Update the label text
            const label = checkboxElement.nextElementSibling;
            if (label) {
                label.childNodes[1].textContent = newValue ? 'Validado' : 'Não validado';
            }
            
            // Show feedback message
            if (newValue) {
                this.showSuccess('RLHF marcado como validado');
            } else {
                this.showSuccess('RLHF marcado como não validado');
            }
            
        } catch (error) {
            console.error('Erro ao atualizar RLHF:', error);
            this.showError('Erro ao salvar alteração do RLHF');
        }
    }
    
    toggleFilter(element) {
        const filterKey = element.dataset.filter;
        const filterValue = element.dataset.value;
        
        // Toggle active state
        const isActive = element.classList.contains('active');
        
        // Limpar outros filtros do mesmo tipo
        element.parentElement.querySelectorAll('.filter-item').forEach(item => {
            item.classList.remove('active');
        });
        
        if (!isActive) {
            element.classList.add('active');
            this.currentFilters[filterKey] = filterValue;
        } else {
            delete this.currentFilters[filterKey];
        }
        
        this.loadConversations();
    }
    
    toggleConfidenceFilter(element) {
        const min = parseFloat(element.dataset.min);
        const max = parseFloat(element.dataset.max);
        
        // Toggle active state
        const isActive = element.classList.contains('active');
        
        // Limpar outros filtros de confiança
        element.parentElement.querySelectorAll('.filter-item').forEach(item => {
            item.classList.remove('active');
        });
        
        if (!isActive) {
            element.classList.add('active');
            this.currentFilters['confidence_min'] = min;
            this.currentFilters['confidence_max'] = max;
        } else {
            delete this.currentFilters['confidence_min'];
            delete this.currentFilters['confidence_max'];
        }
        
        this.loadConversations();
    }
    
    toggleHandoffFilter(element) {
        const filterValue = element.dataset.value;
        
        // Toggle active state
        const isActive = element.classList.contains('active');
        
        // Limpar outros filtros de transbordo
        element.parentElement.querySelectorAll('.filter-item').forEach(item => {
            item.classList.remove('active');
        });
        
        if (!isActive) {
            element.classList.add('active');
            this.currentFilters['has_handoff'] = filterValue;
        } else {
            delete this.currentFilters['has_handoff'];
        }
        
        this.loadConversations();
    }
    
    toggleRlhfFilter(element) {
        const filterValue = element.dataset.value;
        
        // Toggle active state
        const isActive = element.classList.contains('active');
        
        // Limpar outros filtros RLHF
        element.parentElement.querySelectorAll('.filter-item').forEach(item => {
            item.classList.remove('active');
        });
        
        if (!isActive) {
            element.classList.add('active');
            if (filterValue === 'all') {
                delete this.currentFilters['rlhf'];
            } else {
                this.currentFilters['rlhf'] = filterValue;
            }
        } else {
            delete this.currentFilters['rlhf'];
        }
        
        this.loadConversations();
    }
    
    clearFilters() {
        this.currentFilters = {};
        
        // Remover estado ativo de todos os filtros
        document.querySelectorAll('.filter-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Redefinir filtro RLHF para padrão "Não Validado"
        this.currentFilters['rlhf'] = 'false';
        const rlhfFalseFilter = document.querySelector('#rlhfFilter .filter-item[data-value="false"]');
        if (rlhfFalseFilter) {
            rlhfFalseFilter.classList.add('active');
        }
        
        // Limpar busca não é mais necessário
        
        this.loadConversations();
    }
    
    clearSelection() {
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        this.selectedConversation = null;
        
        // Resetar viewers
        document.getElementById('conversationViewer').innerHTML = `
            <div class="viewer-placeholder">
                <i class="fas fa-comments"></i>
                <h3>Selecione uma conversa</h3>
                <p>Clique em uma conversa da lista para visualizar as mensagens</p>
            </div>
        `;
        
        document.getElementById('conversationInfo').innerHTML = `
            <div class="info-placeholder">
                <i class="fas fa-arrow-left"></i>
                <p>Selecione uma conversa para ver as informações detalhadas</p>
            </div>
        `;
    }
    
    // Função filterConversations removida - busca não é mais necessária
    
    getConfidenceLevel(confidence) {
        if (confidence >= 0.9) return 'high';
        if (confidence >= 0.7) return 'medium';
        return 'low';
    }
    
    getEffectivenessLevel(score) {
        if (score >= 0.8) return 'high';
        if (score >= 0.6) return 'medium';
        return 'low';
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }
    
    showError(message) {
        // Implementar toast/notification de erro
        console.error(message);
        alert(message); // Por enquanto, usar alert simples
    }
    
    showSuccess(message) {
        // Implementar toast/notification de sucesso
        console.log(message);
        // Por enquanto, usar alert simples para feedback positivo
        alert(message);
    }
}

// Inicializar aplicação quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new ConversationAnalyzer();
});