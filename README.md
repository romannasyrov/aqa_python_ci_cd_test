**Общая информация**

Проект представляет собой учебный-фреймворк для бэкенд автотестов

Основной стек:
````
- pytest + allure + requests + pydantic
- Service + Adapter паттерн
- Поддержка авторизованных и неавторизованных запросов
- Allure-отчёты с детальными шагами
````

Установка зависимостей:
````
pip install -r requirements.txt
````

Запуск тестов:
````
python -m pytest --alluredir=./allure-results

allure serve ./allure-results/  
````