# AQA Python CI/CD — как устроен фреймворк

> Объяснение для дилетанта, который хочет стать Senior AQA Python.
> Каждый слой объяснён так, чтобы понял даже ребёнок.

---

## 🏪 Метафора: ресторан

Представь ресторан. В нём есть комнаты, и в каждой — своя работа:

| Комната | Слой в проекте | Что делает |
|---------|----------------|------------|
| 🍳 Кухня | **Transport** (`ApiClient`) | Готовит и отправляет HTTP-запросы |
| 🍽️ Официант | **Adapter** (`PostsAdapter`) | Переводит заказ на язык кухни и обратно |
| 💼 Менеджер | **Service** (`PostsService`) | Бизнес-логика, работает на понятных словах |
| 📋 Меню и чек | **Models** (`Request/Response`) | Жёсткий контракт: что принять и что вернуть |
| 🕵️ Тайные покупатели | **Tests** | Проверяют весь стек от начала до конца |

---

## 🍳 1. Transport Layer — «Кухня»

**Файл:** `clients/api_client.py`

```python
class ApiClient:
    def _request(self, endpoint, method, **kwargs) -> requests.Response
```

**За что отвечает:**
- Отправляет HTTP-запросы на сервер.
- Повторяет запрос, если сервер устал (`@retry`).
- Замеряет время (`@timing`).
- Пишет всё в отчёт (`allure`).
- Логирует запросы и ответы.

**Почему это круто:**
- Это **единственное место**, где живёт библиотека `requests`.
  Завтра захочешь换成 `httpx` или `aiohttp` — поменяешь **один файл**.
- Retry, логи, тайминги — **декораторами**, они не засоряют бизнес-логику.
- Тесты мокают `Session.request` — **реальный интернет не дёргается**.

---

## 📦 2. Adapter Layer — «Официант»

**Файл:** `clients/services/adapter.py`

```python
class PostsAdapter:
    def create_post(self, request_model: BaseModel | dict) -> CreatePostResponse
```

**За что отвечает:**
- Знает, какие есть эндпоинты (`Routes.POSTS = "/posts"`).
- Переводит объект в JSON (`model_dump(by_alias=True)`).
- Десериализует ответ в модель (`CreatePostResponse.model_validate(...)`).
- Проверяет статус ответа (`raise_for_status()`).

**Почему это круто:**
- Service **не знает** про `/posts`, про `userId` vs `user_id`, про JSON.
- Принимает **и Pydantic-модель, и dict** — удобно и в тестах, и в проде.
- Возвращает **чистую доменную модель**, а не `requests.Response`.
  Верхние слои **не зависят от HTTP-библиотеки**.

---

## 🎯 3. Service Layer — «Менеджер ресторана»

**Файл:** `clients/services/post_service/service.py`

```python
class PostsService:
    def create_post(self, title: str, body: str, userId: int) -> CreatePostResponse
```

**За что отвечает:**
- Бизнес-логика: «создай пост с таким заголовком, текстом и автором».
- Работает на **понятных человеку терминах** (строки, числа).
- Получает Adapter через конструктор (Dependency Injection).

**Почему это круто:**
- Тесты читаются как требования:
  `posts_service.create_post(title="Привет", body="...", userId=1)`.
- В тестах можно подменить Adapter на мок **без монкепатчей**.
- Завтра добавишь кэш, ретраи, бизнес-правила — **только здесь**.
  Adapter и ApiClient остаются нетронутыми.

---

## 📋 4. Models / DTO — «Меню и чек»

**Файлы:**
- `clients/services/models/request_model.py` — `CreatePostRequest`
- `clients/services/models/response_model.py` — `CreatePostResponse`

```python
class CreatePostRequest(BaseModel):
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    user_id: int = Field(alias="userId", gt=0)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )
```

**За что отвечают:**
- Жёсткий контракт: «пришли title не пустой, userId > 0».
- Валидация **на входе** (Request) и **на выходе** (Response).

**Почему это круто:**
- `extra="forbid"` — сервер прислал лишнее поле → **мгновенный краш**, баг не проскочит.
- `alias="userId"` — в коде пишем `user_id`, на провода уходит `userId`. **Никто не путается**.
- Если API вернёт `userId: "abc"` (строку вместо числа) — упадёт `model_validate`
  **со строкой схемы**, а не с загадочным `assert body["userId"] == 1`.

---

## 🧪 5. Tests — «Тайные покупатели»

**Файл:** `tests/test_users.py`

```python
def test_create_post(posts_service, worker_post_data):
    response = posts_service.create_post(**worker_post_data)
    assert response.id > 0
    assert response.title == worker_post_data["title"]
```

**За что отвечают:**
- Проверяют весь стек: Service → Adapter → ApiClient → реальный API.
- Запускаются **параллельно** (`pytest-xdist`).
- Каждый воркер генерирует **уникальные данные** (`worker_scoped_id`).

**Почему это круто:**
- Фикстуры строят **реальный граф зависимостей**:
  `api_client → posts_adapter → posts_service`.
- Мокается **только** `requests.Session.request` — быстро и детерминированно.
- Allure-отчёт — бизнес читает «Создание поста: PASSED», а не код.

---

## 🚀 Параллелизация (pytest-xdist)

### Как устроена

```
                    pytest -n 4
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     gw0 (воркер 0)   gw1 (воркер 1)   gw2, gw3 ...
        │                │
   PYTEST_XDIST_WORKER="gw0"   PYTEST_XDIST_WORKER="gw1"
        │                │
   worker_id = "gw0"  worker_id = "gw1"
        │                │
   worker_scoped_id("post")  worker_scoped_id("post")
        │                │
   post_gw0_a1b2c3d4  post_gw1_e5f6g7h8   ← уникальные данные!
```

### Ключевые файлы

**`utils/worker_utils.py`** — генерация уникальных ID:
```python
def get_worker_id() -> str:
    return os.getenv("PYTEST_XDIST_WORKER", "master")

def worker_scoped_id(base: str) -> str:
    worker = get_worker_id()
    unique = uuid.uuid4().hex[:8]
    return f"{base}_{worker}_{unique}"
```

**`fixtures/worker_fixtures.py`** — фикстуры:
```python
@pytest.fixture(scope="session")
def worker_id() -> str:
    return os.getenv("PYTEST_XDIST_WORKER", "master")

@pytest.fixture(scope="session")
def worker_num(worker_id) -> int:
    if worker_id.startswith("gw"):
        return int(worker_id.replace("gw", ""))
    return 0

@pytest.fixture
def worker_post_data():
    return {
        "title": worker_scoped_id("post"),
        "body": worker_scoped_id("body"),
        "userId": 1,
    }
```

**`tests/conftest.py`** — подключение:
```python
pytest_plugins = [
    "fixtures.worker_fixtures",
    "fixtures.api_fixtures",
]
```

### Почему именно так, а не по-другому

| Решение | Почему так | Почему не иначе |
|---------|-----------|-----------------|
| **`worker_scoped_id` с uuid** | Данные уникальны **даже при повторном запуске**. Воркеры не конфликтуют между собой. | Просто `gw0`/`gw1` — при ретрае теста данные повторятся и могут словить дедупликацию на стороне API. |
| **Данные на уровне фикстуры, а не в тесте** | Один раз написал — работает для всех тестов. Тест читается чисто. | Хардкод в тесте — дублирование, невозможно переиспользовать. |
| **`scope="session"` для `worker_id`** | Переменная окружения не меняется за сессию — читаем **один раз**. | `scope="function"` — лишние обращения к `os.getenv` на каждый тест. |
| **`autouse` фикстура `attach_worker_to_allure`** | В каждый тест автоматически попадает параметр `worker` — видно, где упало. | Ручной вызов в каждом тесте — забудешь, отчёт будет неполным. |
| **`uuid.uuid4().hex[:8]`** | Короткий (8 символов), но достаточно уникальный. Не раздувает логи. | Полный UUID — слишком длинный. Только воркер — не уникален при ретраях. |
| **`worker_num` отдельно от `worker_id`** | Иногда нужен номер (для сегментации данных), иногда строка (для ID). | Один универсальный формат — придётся парсить строку везде. |

### Как это выглядит на практике

```bash
# Запуск в 4 потока
pytest -n 4

# Каждый воркер создаёт свои данные:
# gw0: post_gw0_a1b2c3d4
# gw1: post_gw1_e5f6g7h8
# gw2: post_gw2_i9j0k1l2
# gw3: post_gw3_m3n4o5p6
```

**Никаких гонок, никаких конфликтов, никакого флакинга.**

---

## 🏆 Почему это Senior-уровень

| Принцип | Как реализован |
|---------|----------------|
| **SOLID** | У каждого класса одна причина измениться |
| **Dependency Rule** | Стрелки зависимостей идут только вниз, циклов нет |
| **Тестируемость** | DI, моки на границе слоёв, никаких монкепатчей в бизнес-коде |
| **Observability** | Allure, logging, timing «из коробки» |
| **Параллелизм** | xdist работает из коробки, уникальные данные на воркер |
| **Читаемость** | Тест читается как пользовательская история |

**Это не «тесты». Это поддерживаемая тестовая инфраструктура.**
Именно за такое платят Senior-ам.

---

## 📊 Структура проекта

```
aqa_ci_cd/
├── clients/                          # 🌐 Клиентская часть
│   ├── api_client.py                 #   Transport (HTTP, retry, timing, allure)
│   └── services/
│       ├── adapter.py                #   Adapter (эндпоинты, сериализация)
│       ├── models/                   #   DTO
│       │   ├── request_model.py      #     CreatePostRequest
│       │   └── response_model.py     #     CreatePostResponse
│       └── post_service/
│           └── service.py            #   Service (бизнес-логика)
├── fixtures/                         # 🧪 Тестовые фикстуры
│   ├── api_fixtures.py               #   api_client, posts_adapter, posts_service
│   └── worker_fixtures.py            #   worker_id, worker_num, worker_post_data
├── tests/                            # 🧪 Тесты
│   ├── conftest.py                   #   подключение фикстур
│   └── test_users.py                 #   тест-кейсы
├── utils/                            # 🛠 Кросс-каттинг
│   ├── retry.py                      #   декоратор retry
│   ├── timing.py                     #   декоратор timing
│   └── worker_utils.py               #   worker_scoped_id
├── requirements.txt
├── pytest.ini                        #   pythonpath, testpaths, allure
└── README.md
```

---

## 🎓 Что сказать на собеседовании

**«Почему не всё в одном тесте?»**
> Разделил transport / adapter / service / models. Смена HTTP-клиента — 1 файл,
> новый эндпоинт — 3 файла, сломанная схема ответа — падает на валидации,
> а не в `assert`.

**«Как тестируешь без интернета?»**
> Мокаю `requests.Session.request` на уровне Transport. Service и Adapter
> тестирую с реальным ApiClient на моке — проверяю маппинг, сериализацию,
> валидацию.

**«Зачем Response Model?»**
> Контракт. Если API вернёт `userId: "abc"` — упадёт `model_validate`
> сразу, тест укажет на строку схемы, а не на `assert body["userId"] == 1`.

**«Как параллелизуешь?»**
> `pytest -n 4` + `worker_scoped_id` в фикстурах. Каждый воркер генерит
> уникальные данные (`post_gw0_a1b2c3d4`), конфликтов и гонок нет.

**«Как масштабируешь?»**
> Новый эндпоинт → `Routes` + метод в Adapter + Response Model + метод в Service.
> Старые слои не трогаю. Параллелизм — `worker_scoped_id`, никаких глобальных стейтов.
