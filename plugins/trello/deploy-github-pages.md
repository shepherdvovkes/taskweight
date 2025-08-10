# Развертывание TaskWeight Power-Up на GitHub Pages

Пошаговая инструкция по размещению Trello Power-Up на GitHub Pages для бесплатного хостинга.

## 🚀 Шаг 1: Создание репозитория

1. Создайте новый репозиторий на GitHub:
   - Название: `taskweight-trello-powerup`
   - Описание: `Trello Power-Up для AI-оценки задач`
   - Публичный репозиторий

2. Клонируйте репозиторий локально:
   ```bash
   git clone https://github.com/your-username/taskweight-trello-powerup.git
   cd taskweight-trello-powerup
   ```

## 📁 Шаг 2: Подготовка файлов

1. Скопируйте все файлы плагина в репозиторий:
   ```
   taskweight-trello-powerup/
   ├── manifest.json
   ├── connector.html
   ├── index.html
   ├── settings.html
   ├── script.js
   ├── style.css
   ├── README.md
   └── deploy-github-pages.md
   ```

2. Создайте файл `.gitignore`:
   ```
   # Системные файлы
   .DS_Store
   Thumbs.db
   
   # Временные файлы
   *.tmp
   *.log
   
   # IDE
   .vscode/
   .idea/
   ```

## ⚙️ Шаг 3: Настройка GitHub Pages

1. Перейдите в настройки репозитория:
   - Settings → Pages

2. В разделе "Source" выберите:
   - Source: `Deploy from a branch`
   - Branch: `main` (или `master`)
   - Folder: `/ (root)`

3. Нажмите "Save"

## 🔧 Шаг 4: Настройка Power-Up

1. Обновите `manifest.json` с правильными URL:
   ```json
   {
     "name": "TaskWeight",
     "details": "AI-powered task estimation system",
     "icon": {
       "url": "https://your-username.github.io/taskweight-trello-powerup/icon.png"
     },
     "capabilities": [
       "callback",
       "card-badges",
       "card-buttons",
       "card-detail-badges",
       "show-settings"
     ],
     "connectors": {
       "iframe": {
         "url": "https://your-username.github.io/taskweight-trello-powerup/connector.html"
       }
     },
     "permissions": [
       "read",
       "write"
     ]
   }
   ```

2. Обновите `connector.html` с правильными URL:
   ```html
   <!-- В connector.html обновите URL -->
   <script>
     window.TrelloPowerUp.initialize({
       'card-buttons': function(t, options) {
         return [{
           text: '🎯 Оценить задачу',
           callback: function(t) {
             return t.modal({
               title: 'TaskWeight - AI Оценка задачи',
               url: 'https://your-username.github.io/taskweight-trello-powerup/index.html',
               height: 600
             });
           }
         }];
       },
       // ... остальной код
     });
   </script>
   ```

3. Обновите `settings.html` с правильными URL:
   ```html
   <!-- В settings.html обновите URL -->
   <script>
     // Обновите URL в настройках
     document.getElementById('api-url').value = 'https://your-domain.com';
   </script>
   ```

## 🎨 Шаг 5: Создание иконки

1. Создайте иконку 16x16px в формате PNG
2. Назовите файл `icon.png`
3. Разместите в корне репозитория

## 📤 Шаг 6: Публикация

1. Добавьте файлы в git:
   ```bash
   git add .
   git commit -m "Initial commit: TaskWeight Trello Power-Up"
   git push origin main
   ```

2. Дождитесь развертывания (обычно 1-2 минуты)

3. Проверьте доступность по адресу:
   ```
   https://your-username.github.io/taskweight-trello-powerup/
   ```

## 🔗 Шаг 7: Создание Power-Up в Trello

1. Перейдите в [Trello Power-Ups Admin](https://trello.com/power-ups/admin)

2. Нажмите "Create a Power-Up"

3. Заполните форму:
   - **Name**: TaskWeight
   - **Details**: AI-powered task estimation system
   - **Icon**: Загрузите `icon.png`
   - **Capabilities**: Выберите все необходимые
   - **Connectors**: 
     ```
     https://your-username.github.io/taskweight-trello-powerup/connector.html
     ```

4. В разделе "Domains" добавьте:
   ```
   your-username.github.io
   ```

5. Сохраните Power-Up

## 🧪 Шаг 8: Тестирование

1. Откройте любую доску Trello
2. Добавьте Power-Up "TaskWeight"
3. Откройте карточку и нажмите "🎯 Оценить задачу"
4. Протестируйте функциональность

## 🔄 Шаг 9: Обновления

Для обновления Power-Up:

1. Внесите изменения в файлы
2. Зафиксируйте изменения:
   ```bash
   git add .
   git commit -m "Update: описание изменений"
   git push origin main
   ```

3. Дождитесь автоматического развертывания

## 🚨 Устранение неполадок

### Power-Up не загружается

1. Проверьте доступность файлов по прямым ссылкам
2. Убедитесь в корректности URL в настройках
3. Проверьте консоль браузера на ошибки

### Ошибки CORS

1. Убедитесь, что домен добавлен в настройки Power-Up
2. Проверьте настройки CORS на вашем API сервере

### Файлы не обновляются

1. Очистите кэш браузера
2. Проверьте статус развертывания в настройках GitHub Pages
3. Убедитесь, что изменения зафиксированы в git

## 📚 Полезные ссылки

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Trello Power-Ups Documentation](https://developer.atlassian.com/cloud/trello/guides/power-ups/)
- [GitHub Pages Troubleshooting](https://docs.github.com/en/pages/getting-started-with-github-pages/troubleshooting-jekyll-build-errors-for-github-pages-sites)

## 🎯 Следующие шаги

После успешного развертывания:

1. Протестируйте Power-Up на разных досках
2. Соберите обратную связь от пользователей
3. Внесите улучшения на основе отзывов
4. Рассмотрите возможность размещения на собственном домене

---

**Успешного развертывания!** 🚀
