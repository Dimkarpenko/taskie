# Taskie - таск-менеджер

### Инструкция по развёртыванию
1. Создать бд на Postgresql, внести данные для подключения в файл /modules/db_manager.py в переменную ```conn_string```
2. Подключиться к бд через пользовательский интерфейс и ввести команду ```ALTER TABLE boards ADD CONSTRAINT boards_project_id_unique UNIQUE (project_id);```
3. Установить зависимости проекта ```pip install -r requirements.txt```
4. Запустить файл main.py