// TaskWeight Trello Power-Up JavaScript

class TaskWeightPowerUp {
    constructor() {
        this.t = window.TrelloPowerUp.iframe();
        this.apiUrl = 'http://localhost:8000'; // По умолчанию
        this.currentCardId = null;
        this.estimationData = null;
        this.settings = {};
        this.logger = new Logger('TaskWeight');
        
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
            
            this.logger.info('Power-Up успешно инициализирован');
            
        } catch (error) {
            this.logger.error('Ошибка инициализации:', error);
            this.showError('Ошибка инициализации Power-Up: ' + error.message);
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
        } catch (error) {
            this.logger.warn('Не удалось загрузить настройки, используем значения по умолчанию');
        }
    }
    
    async loadExistingEstimation() {
        try {
            const estimation = await this.t.get('card', 'shared', 'taskweight_estimation');
            if (estimation) {
                this.estimationData = estimation;
                this.showEstimationResult(estimation);
                this.logger.info('Существующая оценка загружена:', estimation);
            }
        } catch (error) {
            this.logger.log('Существующая оценка не найдена');
        }
    }
    
    async checkApiConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/health`, { 
                method: 'GET',
                timeout: 5000 
            });
            
            if (response.ok) {
                this.logger.info('API соединение установлено');
                this.updateConnectionStatus(true);
            } else {
                this.logger.warn('API недоступен:', response.status);
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            this.logger.warn('Ошибка подключения к API:', error.message);
            this.updateConnectionStatus(false);
        }
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
            
            // Отправляем запрос на оценку
            const response = await this.sendEstimationRequest(formData);
            
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
    
    async sendEstimationRequest(formData) {
        this.logger.info('Отправка запроса на оценку:', formData);
        
        const response = await fetch(`${this.apiUrl}/api/v1/estimate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }
        
        const result = await response.json();
        this.logger.info('Ответ от API:', result);
        return result;
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
        
        // Сохраняем в Trello
        this.saveEstimationToTrello(estimation);
        
        // Очищаем автосохранение
        localStorage.removeItem(`taskweight_form_${this.currentCardId}`);
        
        // Показываем уведомление если включено
        if (this.settings.enableNotifications) {
            this.showNotification('Оценка завершена', `Задача оценена в ${estimation.estimatedHours} часов`);
        }
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
                    source: 'TaskWeight Trello Power-Up'
                };
                
                const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                const a = document.createElement('a');
                a.href = url;
                a.download = `taskweight_estimation_${this.currentCardId}_${new Date().toISOString().split('T')[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                this.showSuccess('Оценка экспортирована!');
                this.logger.info('Оценка экспортирована');
                
            } catch (error) {
                this.logger.error('Ошибка экспорта:', error);
                this.showError('Ошибка при экспорте оценки');
            }
        }
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
    new TaskWeightPowerUp();
});

// Экспорт для тестирования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TaskWeightPowerUp;
}
