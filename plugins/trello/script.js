// TaskWeight Trello Power-Up JavaScript

class TaskWeightPowerUp {
    constructor() {
        this.t = window.TrelloPowerUp.iframe();
        this.apiUrl = 'http://localhost:8000'; // По умолчанию
        this.currentCardId = null;
        this.estimationData = null;
        this.settings = {};
        this.logger = new Logger('TaskWeight');
        this.autoUpdateInterval = null;
        this.isInitialized = false;
        
        this.init();
    }
    
    async init() {
        try {
            this.logger.info('Инициализация TaskWeight Power-Up');
            
            // Получаем ID карточки
            this.currentCardId = await this.t.arg('card', 'id');
            this.logger.info(`Карточка ID: ${this.currentCardId}`);
            
            // Загружаем настройки
            await this.loadSettings();
            
            // Загружаем существующую оценку
            await this.loadExistingEstimation();
            
            // Инициализируем обработчики событий
            this.initEventHandlers();
            
            // Проверяем подключение к API
            await this.checkApiConnection();
            
            // Запускаем автоматическое обновление
            this.startAutoUpdate();
            
            // Инициализируем расширенные функции Trello
            await this.initTrelloExtensions();
            
            this.isInitialized = true;
            this.logger.info('Power-Up успешно инициализирован');
            
        } catch (error) {
            this.logger.error('Ошибка инициализации:', error);
            this.showError('Ошибка инициализации Power-Up: ' + error.message);
        }
    }
    
    async initTrelloExtensions() {
        try {
            // Добавляем кнопки в заголовок карточки
            await this.addCardButtons();
            
            // Добавляем метки для сложности и приоритета
            await this.addComplexityLabels();
            
            // Настраиваем автоматическое обновление времени
            await this.setupTimeTracking();
            
            this.logger.info('Trello расширения инициализированы');
        } catch (error) {
            this.logger.warn('Не удалось инициализировать Trello расширения:', error);
        }
    }
    
    async addCardButtons() {
        try {
            // Добавляем кнопку быстрой оценки в заголовок карточки
            await this.t.render(async (t) => {
                return t.card('id', 'name').then((card) => {
                    return [{
                        icon: {
                            dark: 'https://cdn.glitch.global/taskweight-icon-dark.png',
                            light: 'https://cdn.glitch.global/taskweight-icon-light.png'
                        },
                        text: 'TaskWeight',
                        callback: (t) => {
                            return t.modal({
                                title: 'TaskWeight - Оценка задачи',
                                url: './index.html',
                                height: 600
                            });
                        }
                    }];
                });
            });
        } catch (error) {
            this.logger.warn('Не удалось добавить кнопки карточки:', error);
        }
    }
    
    async addComplexityLabels() {
        try {
            // Получаем существующие метки
            const card = await this.t.card('id', 'labels');
            const existingLabels = card.labels || [];
            
            // Проверяем, есть ли уже метки сложности
            const hasComplexityLabel = existingLabels.some(label => 
                label.name.includes('Сложность:') || 
                label.name.includes('Complexity:')
            );
            
            if (!hasComplexityLabel && this.estimationData) {
                // Добавляем метку сложности на основе оценки
                const complexity = this.getComplexityFromEstimation(this.estimationData.estimatedHours);
                const labelName = `Сложность: ${complexity}`;
                
                // Создаем метку (если у пользователя есть права)
                try {
                    await this.t.arg('callback')({
                        action: 'addLabel',
                        labelName: labelName,
                        color: this.getComplexityColor(complexity)
                    });
                } catch (error) {
                    this.logger.log('Не удалось создать метку автоматически');
                }
            }
        } catch (error) {
            this.logger.warn('Не удалось добавить метки сложности:', error);
        }
    }
    
    getComplexityFromEstimation(hours) {
        if (hours <= 2) return 'Низкая';
        if (hours <= 8) return 'Средняя';
        if (hours <= 24) return 'Высокая';
        return 'Критическая';
    }
    
    getComplexityColor(complexity) {
        switch (complexity) {
            case 'Низкая': return 'green';
            case 'Средняя': return 'yellow';
            case 'Высокая': return 'orange';
            case 'Критическая': return 'red';
            default: return 'blue';
        }
    }
    
    async setupTimeTracking() {
        try {
            // Добавляем поле для отслеживания времени
            const card = await this.t.card('id', 'customFieldItems');
            const customFields = card.customFieldItems || [];
            
            // Ищем поле для времени
            const timeField = customFields.find(field => 
                field.idCustomField && 
                field.value && 
                field.value.text
            );
            
            if (!timeField && this.estimationData) {
                // Создаем поле для отслеживания времени
                await this.t.arg('callback')({
                    action: 'addCustomField',
                    fieldName: 'Время выполнения',
                    fieldType: 'number',
                    defaultValue: this.estimationData.estimatedHours
                });
            }
        } catch (error) {
            this.logger.warn('Не удалось настроить отслеживание времени:', error);
        }
    }
    
    startAutoUpdate() {
        // Обновляем данные каждые 30 секунд
        this.autoUpdateInterval = setInterval(async () => {
            if (this.isInitialized) {
                try {
                    await this.refreshData();
                } catch (error) {
                    this.logger.warn('Ошибка автоматического обновления:', error);
                }
            }
        }, 30000);
    }
    
    async refreshData() {
        try {
            // Обновляем статус подключения
            await this.checkApiConnection();
            
            // Обновляем статистику если есть
            if (this.estimationData) {
                await this.loadCardStatistics();
            }
            
            // Проверяем обновления в Trello
            await this.checkTrelloUpdates();
            
        } catch (error) {
            this.logger.warn('Ошибка обновления данных:', error);
        }
    }
    
    async checkTrelloUpdates() {
        try {
            const card = await this.t.card('id', 'name', 'desc', 'labels', 'due', 'idMembers');
            
            // Проверяем изменения в описании
            if (this.lastCardData && this.lastCardData.desc !== card.desc) {
                this.logger.info('Обнаружены изменения в описании карточки');
                this.suggestReestimation('Изменено описание задачи');
            }
            
            // Проверяем изменения в метках
            if (this.lastCardData && this.lastCardData.labels !== card.labels) {
                this.logger.info('Обнаружены изменения в метках карточки');
                this.suggestReestimation('Изменены метки задачи');
            }
            
            // Сохраняем текущие данные для сравнения
            this.lastCardData = card;
            
        } catch (error) {
            this.logger.warn('Не удалось проверить обновления Trello:', error);
        }
    }
    
    suggestReestimation(reason) {
        if (!this.estimationData || this.estimationData.status !== 'estimated') return;
        
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = 'reestimation-suggestion';
        suggestionDiv.innerHTML = `
            <div class="suggestion-content">
                <p>🔄 <strong>Рекомендуется переоценка:</strong> ${reason}</p>
                <button class="btn btn-primary btn-sm" onclick="window.taskWeightPowerUp.reestimateTask('${reason}')">
                    Переоценить
                </button>
                <button class="btn btn-secondary btn-sm" onclick="this.parentElement.parentElement.remove()">
                    Позже
                </button>
            </div>
        `;
        
        const container = document.querySelector('.power-up-container');
        if (container) {
            container.appendChild(suggestionDiv);
            
            // Автоматически скрываем через 10 секунд
            setTimeout(() => {
                if (suggestionDiv.parentNode) {
                    suggestionDiv.parentNode.removeChild(suggestionDiv);
                }
            }, 10000);
        }
    }
    
    async loadSettings() {
        try {
            const settings = await this.t.arg('settings');
            if (settings) {
                this.settings = settings;
                this.apiUrl = settings.apiUrl || this.apiUrl;
                this.logger.info('Настройки загружены:', this.settings);
            }
            
            // Загружаем настройки из localStorage как fallback
            const localSettings = localStorage.getItem('taskweight_settings');
            if (localSettings) {
                try {
                    const parsed = JSON.parse(localSettings);
                    this.settings = { ...this.settings, ...parsed };
                    this.apiUrl = this.settings.apiUrl || this.apiUrl;
                    this.logger.info('Локальные настройки загружены:', parsed);
                } catch (error) {
                    this.logger.warn('Ошибка парсинга локальных настроек:', error);
                }
            }
            
            // Применяем настройки
            this.applySettings();
            
        } catch (error) {
            this.logger.warn('Не удалось загрузить настройки, используем значения по умолчанию');
        }
    }
    
    applySettings() {
        // Применяем настройки уведомлений
        if (this.settings.enableNotifications) {
            this.requestNotificationPermission();
        }
        
        // Применяем настройки автообновления
        if (this.settings.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
            this.autoUpdateInterval = setInterval(async () => {
                if (this.isInitialized) {
                    await this.refreshData();
                }
            }, this.settings.autoUpdateInterval * 1000);
        }
        
        // Применяем настройки логирования
        if (this.settings.debugMode !== undefined) {
            this.logger.enabled = this.settings.debugMode;
        }
        
        // Применяем настройки API
        if (this.settings.apiTimeout) {
            this.apiTimeout = this.settings.apiTimeout * 1000;
        }
    }
    
    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            try {
                const permission = await Notification.requestPermission();
                if (permission === 'granted') {
                    this.logger.info('Разрешение на уведомления получено');
                } else {
                    this.logger.warn('Разрешение на уведомления отклонено');
                }
            } catch (error) {
                this.logger.warn('Ошибка запроса разрешения на уведомления:', error);
            }
        }
    }
    
    async saveSettings(newSettings) {
        try {
            this.settings = { ...this.settings, ...newSettings };
            
            // Сохраняем в Trello
            await this.t.set('board', 'shared', 'taskweight_settings', this.settings);
            
            // Сохраняем локально как fallback
            localStorage.setItem('taskweight_settings', JSON.stringify(this.settings));
            
            // Применяем новые настройки
            this.applySettings();
            
            this.logger.info('Настройки сохранены:', this.settings);
            this.showSuccess('Настройки успешно сохранены!');
            
            return true;
        } catch (error) {
            this.logger.error('Ошибка сохранения настроек:', error);
            this.showError('Ошибка при сохранении настроек');
            return false;
        }
    }
    
    async loadExistingEstimation() {
        try {
            const estimation = await this.t.get('card', 'shared', 'taskweight_estimation');
            if (estimation) {
                this.estimationData = estimation;
                this.showEstimationResult(estimation);
                this.logger.info('Существующая оценка загружена:', estimation);
                
                // Загружаем дополнительную статистику
                await this.loadCardStatistics();
            }
        } catch (error) {
            this.logger.log('Существующая оценка не найдена');
        }
    }
    
    async loadCardStatistics() {
        try {
            const response = await this.makeApiRequest(`/api/v1/trello/card/${this.currentCardId}/stats`);
            if (response.ok) {
                const stats = await response.json();
                this.showCardStatistics(stats);
                this.logger.info('Статистика карточки загружена:', stats);
                
                // Кэшируем статистику
                this.cachedStats = {
                    data: stats,
                    timestamp: Date.now()
                };
            }
        } catch (error) {
            this.logger.warn('Не удалось загрузить статистику карточки:', error);
            
            // Показываем кэшированную статистику если есть
            if (this.cachedStats && (Date.now() - this.cachedStats.timestamp) < 300000) { // 5 минут
                this.showCardStatistics(this.cachedStats.data);
                this.logger.info('Показана кэшированная статистика');
            }
        }
    }
    
    showCardStatistics(stats) {
        const statsContainer = document.getElementById('card-statistics');
        if (!statsContainer) return;
        
        let statsHTML = `
            <div class="stats-section">
                <h4>📊 Статистика карточки</h4>
                <div class="stats-grid">
        `;
        
        // Статистика точности
        if (stats.accuracy) {
            statsHTML += `
                <div class="stat-item">
                    <span class="stat-label">Точность оценок:</span>
                    <span class="stat-value">${stats.accuracy.average_accuracy || 0}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Всего оценок:</span>
                    <span class="stat-value">${stats.accuracy.total_estimations || 0}</span>
                </div>
            `;
        }
        
        // Распределение по сложности
        if (stats.complexityDistribution) {
            const complexityStats = Object.entries(stats.complexityDistribution)
                .filter(([_, count]) => count > 0)
                .map(([complexity, count]) => `${complexity}: ${count}`)
                .join(', ');
            
            if (complexityStats) {
                statsHTML += `
                    <div class="stat-item">
                        <span class="stat-label">Сложность:</span>
                        <span class="stat-value">${complexityStats}</span>
                    </div>
                `;
            }
        }
        
        // Распределение по приоритету
        if (stats.priorityDistribution) {
            const priorityStats = Object.entries(stats.priorityDistribution)
                .filter(([_, count]) => count > 0)
                .map(([priority, count]) => `${priority}: ${count}`)
                .join(', ');
            
            if (priorityStats) {
                statsHTML += `
                    <div class="stat-item">
                        <span class="stat-label">Приоритет:</span>
                        <span class="stat-value">${priorityStats}</span>
                    </div>
                `;
            }
        }
        
        statsHTML += `
                </div>
            </div>
        `;
        
        // История оценок
        if (stats.history && stats.history.estimations && stats.history.estimations.length > 0) {
            statsHTML += `
                <div class="history-section">
                    <h4>📈 История оценок</h4>
                    <div class="history-list">
            `;
            
            stats.history.estimations.slice(0, 3).forEach(est => {
                const date = new Date(est.createdAt).toLocaleDateString('ru-RU');
                const status = this.getStatusEmoji(est.status);
                statsHTML += `
                    <div class="history-item">
                        <span class="history-date">${date}</span>
                        <span class="history-status">${status}</span>
                        <span class="history-hours">${est.estimatedHours || 0}ч</span>
                    </div>
                `;
            });
            
            statsHTML += `
                    </div>
                </div>
            `;
        }
        
        statsContainer.innerHTML = statsHTML;
        statsContainer.classList.remove('hidden');
    }
    
    getStatusEmoji(status) {
        switch (status) {
            case 'estimated': return '✅';
            case 'processing': return '⏳';
            case 'completed': return '🎯';
            case 'failed': return '❌';
            default: return '❓';
        }
    }

    async checkApiConnection() {
        try {
            const response = await this.makeApiRequest('/health', { 
                method: 'GET',
                timeout: this.apiTimeout || 5000 
            });
            
            if (response.ok) {
                this.logger.info('API соединение установлено');
                this.updateConnectionStatus(true);
                return true;
            } else {
                this.logger.warn('API недоступен:', response.status);
                this.updateConnectionStatus(false);
                return false;
            }
        } catch (error) {
            this.logger.warn('Ошибка подключения к API:', error.message);
            this.updateConnectionStatus(false);
            return false;
        }
    }
    
    async makeApiRequest(endpoint, options = {}) {
        const maxRetries = options.maxRetries || 3;
        const retryDelay = options.retryDelay || 1000;
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const url = `${this.apiUrl}${endpoint}`;
                const requestOptions = {
                    method: options.method || 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers
                    },
                    timeout: options.timeout || this.apiTimeout || 10000,
                    ...options
                };
                
                // Убираем timeout из fetch options (он не поддерживается)
                delete requestOptions.timeout;
                
                this.logger.debug(`API запрос ${attempt}/${maxRetries}: ${requestOptions.method} ${url}`);
                
                const response = await fetch(url, requestOptions);
                
                if (response.ok || response.status < 500) {
                    return response;
                }
                
                // Серверная ошибка - пробуем повторить
                if (response.status >= 500 && attempt < maxRetries) {
                    this.logger.warn(`Попытка ${attempt}/${maxRetries} не удалась: ${response.status}`);
                    await this.delay(retryDelay * attempt);
                    continue;
                }
                
                return response;
                
            } catch (error) {
                lastError = error;
                this.logger.warn(`Попытка ${attempt}/${maxRetries} не удалась:`, error.message);
                
                if (attempt < maxRetries) {
                    await this.delay(retryDelay * attempt);
                }
            }
        }
        
        throw new Error(`API запрос не удался после ${maxRetries} попыток: ${lastError?.message || 'Неизвестная ошибка'}`);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    updateConnectionStatus(isConnected) {
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
            statusIndicator.textContent = isConnected ? '🟢 API доступен' : '🔴 API недоступен';
        }
    }
    
    initEventHandlers() {
        // Кнопка оценки
        const estimateBtn = document.getElementById('estimate-btn');
        if (estimateBtn) {
            estimateBtn.addEventListener('click', () => this.estimateTask());
        }
        
        // Кнопка отмены
        const cancelBtn = document.getElementById('cancel-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeModal());
        }
        
        // Кнопка сохранения оценки
        const saveBtn = document.getElementById('save-estimation');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveEstimation());
        }
        
        // Кнопка новой оценки
        const newBtn = document.getElementById('new-estimation');
        if (newBtn) {
            newBtn.addEventListener('click', () => this.resetForm());
        }
        
        // Кнопка экспорта
        const exportBtn = document.getElementById('export-estimation');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportEstimation());
        }
        
        // Кнопка переоценки
        const reestimateBtn = document.getElementById('reestimate-btn');
        if (reestimateBtn) {
            reestimateBtn.addEventListener('click', () => this.reestimateTask());
        }
        
        // Валидация формы
        this.initFormValidation();
        
        // Автосохранение формы
        this.initAutoSave();
    }
    
    initFormValidation() {
        const repoUrlInput = document.getElementById('repo-url');
        const taskDescriptionInput = document.getElementById('task-description');
        
        if (repoUrlInput && taskDescriptionInput) {
            [repoUrlInput, taskDescriptionInput].forEach(input => {
                input.addEventListener('input', () => this.validateForm());
                input.addEventListener('blur', () => this.validateForm());
            });
        }
    }
    
    initAutoSave() {
        const formInputs = document.querySelectorAll('#estimation-form input, #estimation-form textarea, #estimation-form select');
        formInputs.forEach(input => {
            input.addEventListener('change', () => this.autoSaveForm());
        });
    }
    
    autoSaveForm() {
        const formData = this.getFormData();
        if (formData) {
            localStorage.setItem(`taskweight_form_${this.currentCardId}`, JSON.stringify(formData));
        }
    }
    
    loadAutoSavedForm() {
        try {
            const saved = localStorage.getItem(`taskweight_form_${this.currentCardId}`);
            if (saved) {
                const formData = JSON.parse(saved);
                this.fillForm(formData);
                this.logger.info('Форма восстановлена из автосохранения');
            }
        } catch (error) {
            this.logger.warn('Ошибка загрузки автосохраненной формы:', error);
        }
    }
    
    fillForm(formData) {
        const repoUrl = document.getElementById('repo-url');
        const taskDescription = document.getElementById('task-description');
        const priority = document.getElementById('priority');
        const complexity = document.getElementById('complexity');
        
        if (repoUrl) repoUrl.value = formData.repoUrl || '';
        if (taskDescription) taskDescription.value = formData.taskDescription || '';
        if (priority) priority.value = formData.priority || 'medium';
        if (complexity) complexity.value = formData.complexity || 'medium';
        
        this.validateForm();
    }
    
    validateForm() {
        const repoUrl = document.getElementById('repo-url')?.value;
        const taskDescription = document.getElementById('task-description')?.value;
        const estimateBtn = document.getElementById('estimate-btn');
        
        if (estimateBtn) {
            const isValid = repoUrl && taskDescription && this.isValidGitHubUrl(repoUrl);
            estimateBtn.disabled = !isValid;
            
            if (!isValid) {
                estimateBtn.classList.add('btn-disabled');
            } else {
                estimateBtn.classList.remove('btn-disabled');
            }
        }
    }
    
    isValidGitHubUrl(url) {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname === 'github.com' && urlObj.pathname.split('/').length >= 3;
        } catch {
            return false;
        }
    }
    
    async estimateTask() {
        try {
            this.logger.info('Запуск оценки задачи');
            
            // Получаем данные формы
            const formData = this.getFormData();
            if (!formData) return;
            
            // Показываем состояние загрузки
            this.showLoadingState();
            
            // Проверяем подключение к API
            await this.checkApiConnection();
            
            // Получаем данные карточки Trello для улучшенной оценки
            const cardData = await this.getTrelloCardData();
            
            // Отправляем запрос на оценку с Trello контекстом
            const response = await this.sendEnhancedEstimationRequest(formData, cardData);
            
            if (response.status === 'processing') {
                this.logger.info('Оценка запущена, начинаем опрос статуса');
                // Запускаем опрос статуса
                this.pollEstimationStatus(response.cardId);
            } else {
                this.showError('Неожиданный ответ от сервера');
            }
            
        } catch (error) {
            this.logger.error('Ошибка оценки:', error);
            this.showError('Ошибка при оценке задачи: ' + error.message);
            this.hideLoadingState();
        }
    }
    
    async getTrelloCardData() {
        try {
            // Получаем данные карточки через Trello API
            const cardData = await this.t.card('id', 'name', 'desc', 'labels', 'due', 'idMembers', 'checklists', 'attachments', 'badges');
            
            return {
                id: cardData.id,
                name: cardData.name,
                desc: cardData.desc,
                labels: cardData.labels || [],
                due: cardData.due,
                idMembers: cardData.idMembers || [],
                checklists: cardData.checklists || [],
                attachments: cardData.attachments || [],
                badges: cardData.badges || {}
            };
        } catch (error) {
            this.logger.warn('Не удалось получить данные карточки Trello:', error);
            return {
                id: this.currentCardId,
                name: 'Карточка Trello',
                desc: 'Описание недоступно'
            };
        }
    }
    
    getFormData() {
        const repoUrl = document.getElementById('repo-url')?.value;
        const taskDescription = document.getElementById('task-description')?.value;
        const priority = document.getElementById('priority')?.value;
        const complexity = document.getElementById('complexity')?.value;
        
        if (!repoUrl || !taskDescription) {
            this.showError('Пожалуйста, заполните все обязательные поля');
            return null;
        }
        
        if (!this.isValidGitHubUrl(repoUrl)) {
            this.showError('Пожалуйста, укажите корректную ссылку на GitHub репозиторий');
            return null;
        }
        
        return {
            cardId: this.currentCardId,
            taskDescription: taskDescription,
            repoUrl: repoUrl,
            priority: priority,
            complexity: complexity,
            timestamp: new Date().toISOString()
        };
    }
    
    async pollEstimationStatus(cardId) {
        const maxAttempts = 30; // Максимум 5 минут (30 * 10 секунд)
        let attempts = 0;
        
        this.logger.info(`Начинаем опрос статуса для карточки ${cardId}`);
        
        const poll = async () => {
            try {
                attempts++;
                this.logger.debug(`Попытка ${attempts}/${maxAttempts}`);
                
                const response = await fetch(`${this.apiUrl}/api/v1/estimate/${cardId}`);
                
                if (response.ok) {
                    const estimation = await response.json();
                    this.logger.info('Получен статус оценки:', estimation);
                    
                    if (estimation.status === 'estimated') {
                        // Оценка завершена
                        this.estimationData = estimation;
                        this.showEstimationResult(estimation);
                        this.hideLoadingState();
                        this.logger.info('Оценка успешно завершена');
                        return;
                    } else if (estimation.status === 'failed') {
                        // Ошибка оценки
                        this.showError('Ошибка при оценке: ' + (estimation.error || 'Неизвестная ошибка'));
                        this.hideLoadingState();
                        this.logger.error('Оценка завершилась с ошибкой:', estimation.error);
                        return;
                    }
                }
                
                // Продолжаем опрос
                if (attempts < maxAttempts) {
                    setTimeout(poll, 10000); // 10 секунд
                } else {
                    this.showError('Превышено время ожидания оценки');
                    this.hideLoadingState();
                    this.logger.warn('Превышено время ожидания оценки');
                }
                
            } catch (error) {
                this.logger.error('Ошибка опроса статуса:', error);
                if (attempts < maxAttempts) {
                    setTimeout(poll, 10000);
                } else {
                    this.showError('Ошибка при получении статуса оценки');
                    this.hideLoadingState();
                }
            }
        };
        
        // Запускаем первый опрос
        poll();
    }
    
    async sendEnhancedEstimationRequest(formData, cardData) {
        this.logger.info('Отправка улучшенного запроса на оценку:', { formData, cardData });
        
        // Валидируем данные перед отправкой
        const validationResult = this.validateEstimationData(formData, cardData);
        if (!validationResult.isValid) {
            throw new Error(`Ошибка валидации: ${validationResult.errors.join(', ')}`);
        }
        
        // Используем новый эндпоинт для Trello карточек
        const response = await this.makeApiRequest(`/api/v1/trello/card/${this.currentCardId}/estimate`, {
            method: 'POST',
            body: JSON.stringify({
                ...formData,
                trelloCardData: cardData,
                metadata: {
                    powerUpVersion: '1.0.0',
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent,
                    settings: this.settings
                }
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }
        
        const result = await response.json();
        this.logger.info('Ответ от улучшенного API:', result);
        return result;
    }
    
    validateEstimationData(formData, cardData) {
        const errors = [];
        
        // Проверяем обязательные поля
        if (!formData.repoUrl) {
            errors.push('URL репозитория обязателен');
        } else if (!this.isValidGitHubUrl(formData.repoUrl)) {
            errors.push('Некорректный URL GitHub репозитория');
        }
        
        if (!formData.taskDescription) {
            errors.push('Описание задачи обязательно');
        } else if (formData.taskDescription.length < 10) {
            errors.push('Описание задачи должно содержать минимум 10 символов');
        }
        
        if (!formData.priority) {
            errors.push('Приоритет обязателен');
        }
        
        if (!formData.complexity) {
            errors.push('Сложность обязательна');
        }
        
        // Проверяем данные карточки
        if (!cardData || !cardData.id) {
            errors.push('ID карточки Trello обязателен');
        }
        
        // Проверяем размер данных
        const totalSize = JSON.stringify(formData).length + JSON.stringify(cardData).length;
        if (totalSize > 1000000) { // 1MB
            errors.push('Размер данных превышает допустимый лимит');
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
    
    async getEstimationHistory() {
        try {
            const response = await this.makeApiRequest(`/api/v1/trello/card/${this.currentCardId}/history`);
            if (response.ok) {
                const history = await response.json();
                this.showEstimationHistory(history);
                return history;
            }
        } catch (error) {
            this.logger.warn('Не удалось загрузить историю оценок:', error);
        }
        return null;
    }
    
    showEstimationHistory(history) {
        const historyContainer = document.getElementById('estimation-history');
        if (!historyContainer || !history.estimations) return;
        
        let historyHTML = `
            <div class="history-section">
                <h4>📚 История оценок</h4>
                <div class="history-timeline">
        `;
        
        history.estimations.forEach((estimation, index) => {
            const date = new Date(estimation.createdAt).toLocaleDateString('ru-RU');
            const time = new Date(estimation.createdAt).toLocaleTimeString('ru-RU');
            const status = this.getStatusEmoji(estimation.status);
            const hours = estimation.estimatedHours || 'N/A';
            const confidence = estimation.confidence ? `${estimation.confidence}%` : 'N/A';
            
            historyHTML += `
                <div class="history-item ${index === 0 ? 'current' : ''}">
                    <div class="history-header">
                        <span class="history-date">${date} ${time}</span>
                        <span class="history-status">${status}</span>
                    </div>
                    <div class="history-details">
                        <span class="history-hours">${hours}ч</span>
                        <span class="history-confidence">${confidence}</span>
                    </div>
                    ${estimation.reasoning ? `<div class="history-reasoning">${estimation.reasoning}</div>` : ''}
                </div>
            `;
        });
        
        historyHTML += `
                </div>
            </div>
        `;
        
        historyContainer.innerHTML = historyHTML;
        historyContainer.classList.remove('hidden');
    }
    
    async exportEstimationHistory() {
        try {
            const history = await this.getEstimationHistory();
            if (!history) {
                this.showError('Не удалось загрузить историю оценок');
                return;
            }
            
            const exportData = {
                cardId: this.currentCardId,
                cardName: await this.getCardName(),
                history: history,
                exportedAt: new Date().toISOString(),
                source: 'TaskWeight Trello Power-Up'
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
                type: 'application/json' 
            });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `taskweight_history_${this.currentCardId}_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showSuccess('История оценок экспортирована!');
            
        } catch (error) {
            this.logger.error('Ошибка экспорта истории:', error);
            this.showError('Ошибка при экспорте истории оценок');
        }
    }
    
    async getCardName() {
        try {
            const card = await this.t.card('id', 'name');
            return card.name || 'Неизвестная карточка';
        } catch (error) {
            return 'Неизвестная карточка';
        }
    }

    async updateCardMetadata(metadata) {
        try {
            const response = await this.makeApiRequest(`/api/v1/trello/card/${this.currentCardId}/metadata`, {
                method: 'POST',
                body: JSON.stringify(metadata)
            });
            
            if (response.ok) {
                this.logger.info('Метаданные карточки обновлены');
                return true;
            } else {
                this.logger.warn('Не удалось обновить метаданные карточки');
                return false;
            }
        } catch (error) {
            this.logger.error('Ошибка обновления метаданных:', error);
            return false;
        }
    }
    
    // Функция для очистки ресурсов
    cleanup() {
        try {
            // Останавливаем автоматическое обновление
            if (this.autoUpdateInterval) {
                clearInterval(this.autoUpdateInterval);
                this.autoUpdateInterval = null;
            }
            
            // Очищаем кэш
            this.cachedStats = null;
            this.lastCardData = null;
            
            // Сбрасываем флаги
            this.isInitialized = false;
            
            this.logger.info('Ресурсы очищены');
        } catch (error) {
            this.logger.error('Ошибка при очистке ресурсов:', error);
        }
    }
    
    // Функция для перезагрузки Power-Up
    async reload() {
        try {
            this.logger.info('Перезагрузка Power-Up');
            
            // Очищаем ресурсы
            this.cleanup();
            
            // Перезагружаем страницу
            window.location.reload();
            
        } catch (error) {
            this.logger.error('Ошибка при перезагрузке:', error);
        }
    }
    
    // Функция для получения диагностической информации
    getDiagnosticInfo() {
        return {
            powerUpVersion: '1.0.0',
            isInitialized: this.isInitialized,
            currentCardId: this.currentCardId,
            apiUrl: this.apiUrl,
            apiConnection: this.lastApiCheck,
            settings: this.settings,
            estimationData: this.estimationData ? {
                status: this.estimationData.status,
                estimatedHours: this.estimationData.estimatedHours,
                createdAt: this.estimationData.createdAt
            } : null,
            cachedStats: this.cachedStats ? {
                timestamp: this.cachedStats.timestamp,
                age: Date.now() - this.cachedStats.timestamp
            } : null,
            userAgent: navigator.userAgent,
            timestamp: new Date().toISOString()
        };
    }
    
    // Функция для экспорта диагностической информации
    exportDiagnostics() {
        try {
            const diagnostics = this.getDiagnosticInfo();
            const blob = new Blob([JSON.stringify(diagnostics, null, 2)], { 
                type: 'application/json' 
            });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `taskweight_diagnostics_${this.currentCardId}_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showSuccess('Диагностическая информация экспортирована!');
            
        } catch (error) {
            this.logger.error('Ошибка экспорта диагностики:', error);
            this.showError('Ошибка при экспорте диагностической информации');
        }
    }
    
    // Функция для проверки производительности
    async checkPerformance() {
        const startTime = performance.now();
        
        try {
            // Проверяем время ответа API
            const apiStart = performance.now();
            await this.checkApiConnection();
            const apiTime = performance.now() - apiStart;
            
            // Проверяем время загрузки данных карточки
            const cardStart = performance.now();
            await this.t.card('id', 'name', 'desc');
            const cardTime = performance.now() - cardStart;
            
            const totalTime = performance.now() - startTime;
            
            const performanceData = {
                apiResponseTime: Math.round(apiTime),
                cardLoadTime: Math.round(cardTime),
                totalTime: Math.round(totalTime),
                timestamp: new Date().toISOString()
            };
            
            this.logger.info('Результаты проверки производительности:', performanceData);
            
            // Показываем результаты пользователю
            this.showPerformanceResults(performanceData);
            
            return performanceData;
            
        } catch (error) {
            this.logger.error('Ошибка проверки производительности:', error);
            return null;
        }
    }
    
    showPerformanceResults(performanceData) {
        const performanceDiv = document.createElement('div');
        performanceDiv.className = 'performance-results';
        performanceDiv.innerHTML = `
            <div class="performance-content">
                <h4>⚡ Результаты проверки производительности</h4>
                <div class="performance-metrics">
                    <div class="metric">
                        <span class="metric-label">API:</span>
                        <span class="metric-value">${performanceData.apiResponseTime}ms</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Trello:</span>
                        <span class="metric-value">${performanceData.cardLoadTime}ms</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Общее:</span>
                        <span class="metric-value">${performanceData.totalTime}ms</span>
                    </div>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="this.parentElement.parentElement.remove()">
                    Закрыть
                </button>
            </div>
        `;
        
        const container = document.querySelector('.power-up-container');
        if (container) {
            container.appendChild(performanceDiv);
            
            // Автоматически скрываем через 8 секунд
            setTimeout(() => {
                if (performanceDiv.parentNode) {
                    performanceDiv.parentNode.removeChild(performanceDiv);
                }
            }, 8000);
        }
    }

    async reestimateTask(reason = 'Запрос пользователя') {
        try {
            this.logger.info('Запуск переоценки задачи');
            
            this.showLoadingState();
            
            const response = await this.makeApiRequest(`/api/v1/trello/card/${this.currentCardId}/reestimate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ reason })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.logger.info('Переоценка запущена:', result);
                
                // Показываем сообщение о переоценке
                this.showSuccess('Переоценка запущена!');
                
                // Обновляем данные
                this.estimationData = result;
                this.showEstimationResult(result);
                
            } else {
                throw new Error('Ошибка при запуске переоценки');
            }
            
        } catch (error) {
            this.logger.error('Ошибка переоценки:', error);
            this.showError('Ошибка при переоценке: ' + error.message);
        } finally {
            this.hideLoadingState();
        }
    }

    showLoadingState() {
        const estimateBtn = document.getElementById('estimate-btn');
        const btnText = document.querySelector('.btn-text');
        const btnLoading = document.querySelector('.btn-loading');
        
        if (estimateBtn && btnText && btnLoading) {
            estimateBtn.disabled = true;
            btnText.classList.add('hidden');
            btnLoading.classList.remove('hidden');
        }
    }
    
    hideLoadingState() {
        const estimateBtn = document.getElementById('estimate-btn');
        const btnText = document.querySelector('.btn-text');
        const btnLoading = document.querySelector('.btn-loading');
        
        if (estimateBtn && btnText && btnLoading) {
            estimateBtn.disabled = false;
            btnText.classList.remove('hidden');
            btnLoading.classList.add('hidden');
        }
    }
    
    showEstimationResult(estimation) {
        // Скрываем форму
        const estimationForm = document.getElementById('estimation-form');
        if (estimationForm) {
            estimationForm.classList.add('hidden');
        }
        
        // Показываем результат
        const estimationResult = document.getElementById('estimation-result');
        if (estimationResult) {
            estimationResult.classList.remove('hidden');
        }
        
        // Обновляем статус
        this.updateStatusBadge(estimation);
        
        // Обновляем детали
        this.updateEstimationDetails(estimation);
        
        // Показываем Trello факторы если есть
        this.showTrelloFactors(estimation);
        
        // Сохраняем в Trello
        this.saveEstimationToTrello(estimation);
        
        // Очищаем автосохранение
        localStorage.removeItem(`taskweight_form_${this.currentCardId}`);
        
        // Показываем уведомление если включено
        if (this.settings.enableNotifications) {
            this.showNotification('Оценка завершена', `Задача оценена в ${estimation.estimatedHours} часов`);
        }
    }
    
    showTrelloFactors(estimation) {
        const trelloFactorsContainer = document.getElementById('trello-factors');
        if (!trelloFactorsContainer || !estimation.metadata) return;
        
        const trelloAnalysis = estimation.metadata.trello_analysis;
        if (!trelloAnalysis) return;
        
        let factorsHTML = '<h4>🏷️ Факторы Trello</h4><div class="trello-factors-list">';
        
        // Показываем индикаторы сложности
        if (trelloAnalysis.complexity_indicators && trelloAnalysis.complexity_indicators.length > 0) {
            factorsHTML += `
                <div class="factor-group">
                    <span class="factor-label">Сложность:</span>
                    <span class="factor-values">${trelloAnalysis.complexity_indicators.join(', ')}</span>
                </div>
            `;
        }
        
        // Показываем индикаторы приоритета
        if (trelloAnalysis.priority_indicators && trelloAnalysis.priority_indicators.length > 0) {
            factorsHTML += `
                <div class="factor-group">
                    <span class="factor-label">Приоритет:</span>
                    <span class="factor-values">${trelloAnalysis.priority_indicators.join(', ')}</span>
                </div>
            `;
        }
        
        // Показываем общую статистику
        if (trelloAnalysis.label_count > 0) {
            factorsHTML += `
                <div class="factor-group">
                    <span class="factor-label">Метки:</span>
                    <span class="factor-values">${trelloAnalysis.label_count} шт.</span>
                </div>
            `;
        }
        
        if (trelloAnalysis.has_due_date) {
            factorsHTML += `
                <div class="factor-group">
                    <span class="factor-label">Срок:</span>
                    <span class="factor-values">Установлен</span>
                </div>
            `;
        }
        
        factorsHTML += '</div>';
        trelloFactorsContainer.innerHTML = factorsHTML;
        trelloFactorsContainer.classList.remove('hidden');
    }
    
    updateStatusBadge(estimation) {
        const statusBadge = document.getElementById('status-badge');
        const statusText = document.querySelector('.status-text');
        
        if (statusBadge && statusText) {
            statusBadge.className = `status-badge status-${estimation.status}`;
            
            switch (estimation.status) {
                case 'estimated':
                    statusText.textContent = `✅ Оценка завершена: ${estimation.estimatedHours} часов`;
                    break;
                case 'processing':
                    statusText.textContent = '⏳ Оценка выполняется...';
                    break;
                case 'failed':
                    statusText.textContent = '❌ Ошибка оценки';
                    break;
                default:
                    statusText.textContent = '❓ Неизвестный статус';
            }
        }
    }
    
    updateEstimationDetails(estimation) {
        const estimateDetails = document.getElementById('estimate-details');
        
        if (estimateDetails) {
            let detailsHTML = '';
            
            if (estimation.status === 'estimated') {
                detailsHTML = `
                    <h4>📊 Детали оценки</h4>
                    <p><span class="highlight">Прогноз времени:</span> ${estimation.estimatedHours} часов</p>
                    <p><span class="highlight">Дата оценки:</span> ${new Date(estimation.createdAt).toLocaleString('ru-RU')}</p>
                    <p><span class="highlight">Статус:</span> Оценка завершена успешно</p>
                    ${estimation.confidence ? `<p><span class="highlight">Уверенность:</span> ${estimation.confidence}%</p>` : ''}
                    ${estimation.reasoning ? `<p><span class="highlight">Обоснование:</span> ${estimation.reasoning}</p>` : ''}
                `;
            } else if (estimation.status === 'processing') {
                detailsHTML = `
                    <h4>⏳ Оценка в процессе</h4>
                    <p>AI анализирует задачу и репозиторий...</p>
                    <p>Это может занять несколько минут</p>
                `;
            } else if (estimation.status === 'failed') {
                detailsHTML = `
                    <h4>❌ Ошибка оценки</h4>
                    <p><span class="highlight">Причина:</span> ${estimation.error || 'Неизвестная ошибка'}</p>
                    <p>Попробуйте повторить оценку позже</p>
                `;
            }
            
            estimateDetails.innerHTML = detailsHTML;
        }
    }
    
    async saveEstimationToTrello(estimation) {
        try {
            await this.t.set('card', 'shared', 'taskweight_estimation', estimation);
            
            // Обновляем бейджи
            await this.t.arg('callback')({ success: true, estimation: estimation });
            
            this.logger.info('Оценка сохранена в Trello');
            
        } catch (error) {
            this.logger.error('Ошибка сохранения в Trello:', error);
        }
    }
    
    async saveEstimation() {
        if (this.estimationData) {
            try {
                await this.saveEstimationToTrello(this.estimationData);
                this.showSuccess('Оценка успешно сохранена в Trello!');
                
                // Закрываем модальное окно
                setTimeout(() => this.closeModal(), 1500);
                
            } catch (error) {
                this.logger.error('Ошибка сохранения:', error);
                this.showError('Ошибка при сохранении оценки');
            }
        }
    }
    
    async exportEstimation() {
        if (this.estimationData) {
            try {
                const exportData = {
                    ...this.estimationData,
                    exportedAt: new Date().toISOString(),
                    source: 'TaskWeight Trello Power-Up',
                    trelloCardId: this.currentCardId,
                    exportVersion: '1.0'
                };
                
                // Создаем несколько форматов экспорта
                const formats = {
                    json: {
                        data: JSON.stringify(exportData, null, 2),
                        mimeType: 'application/json',
                        extension: 'json'
                    },
                    csv: {
                        data: this.convertToCSV(exportData),
                        mimeType: 'text/csv',
                        extension: 'csv'
                    },
                    txt: {
                        data: this.convertToText(exportData),
                        mimeType: 'text/plain',
                        extension: 'txt'
                    }
                };
                
                // Показываем выбор формата
                const format = await this.showFormatSelector();
                if (!format || !formats[format]) return;
                
                const selectedFormat = formats[format];
                const blob = new Blob([selectedFormat.data], { type: selectedFormat.mimeType });
                const url = URL.createObjectURL(blob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = `taskweight_estimation_${this.currentCardId}_${new Date().toISOString().split('T')[0]}.${selectedFormat.extension}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showSuccess(`Оценка экспортирована в формате ${format.toUpperCase()}!`);
                this.logger.info(`Оценка экспортирована в формате ${format}`);
                
            } catch (error) {
                this.logger.error('Ошибка экспорта:', error);
                this.showError('Ошибка при экспорте оценки');
            }
        }
    }
    
    async showFormatSelector() {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'format-selector-modal';
            modal.innerHTML = `
                <div class="format-selector-content">
                    <h4>Выберите формат экспорта</h4>
                    <div class="format-options">
                        <button class="format-option" data-format="json">
                            <span class="format-icon">📄</span>
                            <span class="format-name">JSON</span>
                            <span class="format-desc">Полные данные для импорта</span>
                        </button>
                        <button class="format-option" data-format="csv">
                            <span class="format-icon">📊</span>
                            <span class="format-name">CSV</span>
                            <span class="format-desc">Таблица для Excel</span>
                        </button>
                        <button class="format-option" data-format="txt">
                            <span class="format-icon">📝</span>
                            <span class="format-name">TXT</span>
                            <span class="format-desc">Читаемый текст</span>
                        </button>
                    </div>
                    <button class="btn btn-secondary cancel-btn">Отмена</button>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Обработчики событий
            modal.querySelectorAll('.format-option').forEach(btn => {
                btn.addEventListener('click', () => {
                    const format = btn.dataset.format;
                    document.body.removeChild(modal);
                    resolve(format);
                });
            });
            
            modal.querySelector('.cancel-btn').addEventListener('click', () => {
                document.body.removeChild(modal);
                resolve(null);
            });
            
            // Закрытие по клику вне модального окна
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    document.body.removeChild(modal);
                    resolve(null);
                }
            });
        });
    }
    
    convertToCSV(data) {
        const rows = [
            ['Поле', 'Значение'],
            ['ID оценки', data.id || 'N/A'],
            ['ID карточки', data.cardId || 'N/A'],
            ['Статус', data.status || 'N/A'],
            ['Прогноз часов', data.estimatedHours || 'N/A'],
            ['Дата создания', data.createdAt || 'N/A'],
            ['Уверенность', data.confidence ? `${data.confidence}%` : 'N/A'],
            ['Описание', data.taskDescription || 'N/A'],
            ['Репозиторий', data.repoUrl || 'N/A'],
            ['Приоритет', data.priority || 'N/A'],
            ['Сложность', data.complexity || 'N/A']
        ];
        
        return rows.map(row => 
            row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
        ).join('\n');
    }
    
    convertToText(data) {
        return `ОЦЕНКА ЗАДАЧИ TASKWEIGHT
===============================

ID оценки: ${data.id || 'N/A'}
ID карточки: ${data.cardId || 'N/A'}
Статус: ${data.status || 'N/A'}
Прогноз времени: ${data.estimatedHours || 'N/A'} часов
Дата создания: ${data.createdAt || 'N/A'}
Уверенность: ${data.confidence ? `${data.confidence}%` : 'N/A'}

ОПИСАНИЕ ЗАДАЧИ:
${data.taskDescription || 'N/A'}

РЕПОЗИТОРИЙ:
${data.repoUrl || 'N/A'}

ПАРАМЕТРЫ:
- Приоритет: ${data.priority || 'N/A'}
- Сложность: ${data.complexity || 'N/A'}

${data.reasoning ? `ОБОСНОВАНИЕ:
${data.reasoning}` : ''}

Экспортировано: ${new Date().toISOString()}
Источник: TaskWeight Trello Power-Up`;
    }
    
    resetForm() {
        // Скрываем результат
        const estimationResult = document.getElementById('estimation-result');
        if (estimationResult) {
            estimationResult.classList.add('hidden');
        }
        
        // Показываем форму
        const estimationForm = document.getElementById('estimation-form');
        if (estimationForm) {
            estimationForm.classList.remove('hidden');
        }
        
        // Очищаем форму
        this.clearForm();
        
        // Сбрасываем данные
        this.estimationData = null;
        
        // Загружаем автосохраненную форму
        this.loadAutoSavedForm();
    }
    
    clearForm() {
        const repoUrl = document.getElementById('repo-url');
        const taskDescription = document.getElementById('task-description');
        const priority = document.getElementById('priority');
        const complexity = document.getElementById('complexity');
        
        if (repoUrl) repoUrl.value = '';
        if (taskDescription) taskDescription.value = '';
        if (priority) priority.value = 'medium';
        if (complexity) complexity.value = 'medium';
        
        // Валидируем форму
        this.validateForm();
    }
    
    closeModal() {
        try {
            this.t.closeModal();
        } catch (error) {
            this.logger.log('Модальное окно уже закрыто');
        }
    }
    
    showError(message) {
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        
        if (errorMessage && errorText) {
            errorText.textContent = message;
            errorMessage.classList.remove('hidden');
            
            // Автоматически скрываем через 5 секунд
            setTimeout(() => {
                errorMessage.classList.add('hidden');
            }, 5000);
        }
        
        this.logger.error('Показана ошибка:', message);
    }
    
    showSuccess(message) {
        // Создаем временное сообщение об успехе
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `<p>✅ ${message}</p>`;
        
        const container = document.querySelector('.power-up-container');
        if (container) {
            container.appendChild(successDiv);
            
            // Удаляем через 3 секунды
            setTimeout(() => {
                if (successDiv.parentNode) {
                    successDiv.parentNode.removeChild(successDiv);
                }
            }, 3000);
        }
        
        this.logger.info('Показано сообщение об успехе:', message);
    }
    
    showNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body, icon: 'https://cdn.glitch.global/your-icon-dark.png' });
        }
    }
}

// Класс для логирования
class Logger {
    constructor(prefix) {
        this.prefix = prefix;
        this.enabled = true;
    }
    
    log(...args) {
        if (this.enabled) {
            console.log(`[${this.prefix}]`, ...args);
        }
    }
    
    info(...args) {
        if (this.enabled) {
            console.info(`[${this.prefix}]`, ...args);
        }
    }
    
    warn(...args) {
        if (this.enabled) {
            console.warn(`[${this.prefix}]`, ...args);
        }
    }
    
    error(...args) {
        if (this.enabled) {
            console.error(`[${this.prefix}]`, ...args);
        }
    }
    
    debug(...args) {
        if (this.enabled && console.debug) {
            console.debug(`[${this.prefix}]`, ...args);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Создаем глобальный экземпляр для доступа из HTML
    window.taskWeightPowerUp = new TaskWeightPowerUp();
    
    // Добавляем обработчики для глобальных событий
    window.addEventListener('beforeunload', () => {
        if (window.taskWeightPowerUp) {
            window.taskWeightPowerUp.cleanup();
        }
    });
    
    // Добавляем обработчики для сообщений от iframe
    window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'taskweight') {
            window.taskWeightPowerUp.handleMessage(event.data);
        }
    });
});

// Добавляем метод для обработки сообщений
TaskWeightPowerUp.prototype.handleMessage = function(message) {
    try {
        switch (message.action) {
            case 'checkPerformance':
                this.checkPerformance();
                break;
            case 'exportDiagnostics':
                this.exportDiagnostics();
                break;
            case 'reload':
                this.reload();
                break;
            case 'getDiagnosticInfo':
                return this.getDiagnosticInfo();
            default:
                this.logger.warn('Неизвестное сообщение:', message);
        }
    } catch (error) {
        this.logger.error('Ошибка обработки сообщения:', error);
    }
};

// Экспорт для тестирования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TaskWeightPowerUp;
}

// Добавляем глобальные утилиты
window.TaskWeightUtils = {
    // Форматирование времени
    formatDuration: (hours) => {
        if (hours < 1) return `${Math.round(hours * 60)} мин`;
        if (hours < 24) return `${hours}ч`;
        const days = Math.floor(hours / 24);
        const remainingHours = hours % 24;
        return `${days}д ${remainingHours}ч`;
    },
    
    // Форматирование даты
    formatDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Валидация URL
    isValidUrl: (url) => {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },
    
    // Генерация уникального ID
    generateId: () => {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },
    
    // Дебаунс функция
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Добавляем глобальные константы
window.TaskWeightConstants = {
    VERSION: '1.0.0',
    API_ENDPOINTS: {
        HEALTH: '/health',
        ESTIMATE: '/api/v1/trello/card',
        STATS: '/api/v1/trello/card',
        HISTORY: '/api/v1/trello/card'
    },
    STATUSES: {
        PROCESSING: 'processing',
        ESTIMATED: 'estimated',
        FAILED: 'failed'
    },
    COMPLEXITY_LEVELS: {
        LOW: 'low',
        MEDIUM: 'medium',
        HIGH: 'high',
        CRITICAL: 'critical'
    },
    PRIORITY_LEVELS: {
        LOW: 'low',
        MEDIUM: 'medium',
        HIGH: 'high',
        URGENT: 'urgent'
    },
    DEFAULT_SETTINGS: {
        apiUrl: 'http://localhost:8000',
        enableNotifications: true,
        autoUpdateInterval: 30,
        debugMode: false,
        apiTimeout: 10
    }
};
