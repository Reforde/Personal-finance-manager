"""Swagger 2.0 template for flasgger. Served at /docs (UI) and /apispec_1.json."""

SWAGGER_CONFIG = {
    'headers': [],
    'specs': [
        {
            'endpoint': 'apispec',
            'route': '/api/swagger.json',
            'rule_filter': lambda rule: True,
            'model_filter': lambda tag: True,
        }
    ],
    'static_url_path': '/flasgger_static',
    'swagger_ui': True,
    'specs_route': '/docs',
}

SWAGGER_TEMPLATE = {
    'swagger': '2.0',
    'info': {
        'title': 'Finance App API',
        'description': (
            'REST API для особистого фінансового менеджменту. '
            'Підтримує інтеграцію з Monobank, бюджетування та аналітику витрат. '
            '\n\n**Автентифікація:** JWT у HttpOnly cookies. '
            'Спочатку викличте `POST /api/auth/login`, після чого браузер '
            'автоматично передаватиме cookie у кожному запиті.'
        ),
        'version': '1.0.0',
        'contact': {'email': 'admin@example.com'},
    },
    'basePath': '/',
    'consumes': ['application/json'],
    'produces': ['application/json'],
    'securityDefinitions': {
        'cookieAuth': {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'access_token_cookie',
            'description': 'JWT access token (встановлюється автоматично після /api/auth/login)',
        },
        'csrfToken': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-CSRF-TOKEN',
            'description': 'CSRF-токен (з cookie csrf_access_token)',
        },
    },
    'tags': [
        {'name': 'Auth', 'description': 'Реєстрація, вхід, профіль'},
        {'name': 'Accounts', 'description': 'Підключення банківських рахунків (Monobank)'},
        {'name': 'Transactions', 'description': 'Транзакції (ручні та імпортовані)'},
        {'name': 'Categories', 'description': 'Категорії витрат'},
        {'name': 'Budgets', 'description': 'Місячні бюджети'},
        {'name': 'Analytics', 'description': 'Аналітика та статистика'},
        {'name': 'Balance', 'description': 'Місячний баланс'},
        {'name': 'Rates', 'description': 'Курси валют (PrivatBank)'},
        {'name': 'Webhooks', 'description': 'Вебхуки від Monobank'},
    ],
    'paths': {
        # ── Auth ──────────────────────────────────────────────────────────────
        '/api/auth/register': {
            'post': {
                'tags': ['Auth'],
                'summary': 'Реєстрація нового користувача',
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['email', 'password'],
                            'properties': {
                                'email': {'type': 'string', 'format': 'email', 'example': 'user@example.com'},
                                'password': {'type': 'string', 'minLength': 8, 'example': 'secret123'},
                            },
                        },
                    }
                ],
                'responses': {
                    '201': {
                        'description': 'Успішна реєстрація',
                        'schema': {'$ref': '#/definitions/User'},
                    },
                    '409': {'description': 'Email вже зареєстровано'},
                    '422': {'description': 'Помилка валідації'},
                },
            }
        },
        '/api/auth/login': {
            'post': {
                'tags': ['Auth'],
                'summary': 'Вхід (встановлює JWT cookies)',
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['email', 'password'],
                            'properties': {
                                'email': {'type': 'string', 'format': 'email'},
                                'password': {'type': 'string'},
                            },
                        },
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Успішний вхід',
                        'schema': {'$ref': '#/definitions/User'},
                    },
                    '401': {'description': 'Невірні дані'},
                    '422': {'description': 'Помилка валідації'},
                },
            }
        },
        '/api/auth/logout': {
            'post': {
                'tags': ['Auth'],
                'summary': 'Вихід (очищає cookies)',
                'security': [{'cookieAuth': []}],
                'responses': {
                    '200': {'description': 'Успішний вихід'},
                },
            }
        },
        '/api/auth/me': {
            'get': {
                'tags': ['Auth'],
                'summary': 'Дані поточного користувача',
                'security': [{'cookieAuth': []}],
                'responses': {
                    '200': {
                        'description': 'Профіль користувача',
                        'schema': {'$ref': '#/definitions/User'},
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            }
        },
        '/api/auth/refresh': {
            'post': {
                'tags': ['Auth'],
                'summary': 'Оновлення access token через refresh cookie',
                'security': [{'cookieAuth': []}],
                'responses': {
                    '200': {'description': 'Токен оновлено'},
                    '401': {'description': 'Refresh token недійсний'},
                },
            }
        },
        '/api/auth/password': {
            'put': {
                'tags': ['Auth'],
                'summary': 'Зміна пароля',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['current_password', 'new_password'],
                            'properties': {
                                'current_password': {'type': 'string'},
                                'new_password': {'type': 'string', 'minLength': 8},
                            },
                        },
                    }
                ],
                'responses': {
                    '200': {'description': 'Пароль змінено'},
                    '400': {'description': 'Поточний пароль невірний'},
                    '401': {'description': 'Не авторизовано'},
                },
            }
        },
        '/api/auth/profile': {
            'put': {
                'tags': ['Auth'],
                'summary': 'Оновлення профілю (валюта, баланс)',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'default_currency': {
                                    'type': 'string',
                                    'example': 'UAH',
                                    'enum': ['UAH', 'USD', 'EUR'],
                                },
                                'manual_balance': {
                                    'type': 'integer',
                                    'description': 'Баланс у копійках',
                                    'example': 1000000,
                                },
                            },
                        },
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Профіль оновлено',
                        'schema': {'$ref': '#/definitions/User'},
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            }
        },

        # ── Accounts ──────────────────────────────────────────────────────────
        '/api/accounts': {
            'get': {
                'tags': ['Accounts'],
                'summary': 'Список підключених рахунків',
                'security': [{'cookieAuth': []}],
                'responses': {
                    '200': {
                        'description': 'Масив рахунків',
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/Account'},
                        },
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            }
        },
        '/api/accounts/connect': {
            'post': {
                'tags': ['Accounts'],
                'summary': 'Підключити Monobank (запускає імпорт у фоні)',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['bank_type', 'token'],
                            'properties': {
                                'bank_type': {'type': 'string', 'enum': ['monobank'], 'example': 'monobank'},
                                'token': {
                                    'type': 'string',
                                    'description': 'Персональний токен Monobank',
                                    'example': 'u....',
                                },
                            },
                        },
                    }
                ],
                'responses': {
                    '201': {
                        'description': 'Рахунки підключено',
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/Account'},
                        },
                    },
                    '400': {'description': 'Помилка Monobank API'},
                    '401': {'description': 'Не авторизовано'},
                    '422': {'description': 'Невірні параметри'},
                },
            }
        },
        '/api/accounts/{id}': {
            'delete': {
                'tags': ['Accounts'],
                'summary': 'Відключити рахунок (транзакції зберігаються)',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'}
                ],
                'responses': {
                    '200': {'description': 'Рахунок відключено'},
                    '404': {'description': 'Рахунок не знайдено'},
                },
            }
        },
        '/api/accounts/{id}/sync': {
            'post': {
                'tags': ['Accounts'],
                'summary': 'Запустити синхронізацію транзакцій за останній місяць',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'}
                ],
                'responses': {
                    '202': {
                        'description': 'Синхронізацію запущено',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'message': {'type': 'string'},
                                'task_id': {'type': 'string'},
                            },
                        },
                    },
                    '404': {'description': 'Рахунок не знайдено'},
                },
            }
        },

        # ── Transactions ──────────────────────────────────────────────────────
        '/api/transactions': {
            'get': {
                'tags': ['Transactions'],
                'summary': 'Список транзакцій з фільтрами та пагінацією',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {'in': 'query', 'name': 'from', 'type': 'string', 'format': 'date',
                     'description': 'Від дати (ISO 8601)', 'example': '2025-06-01'},
                    {'in': 'query', 'name': 'to', 'type': 'string', 'format': 'date',
                     'description': 'До дати (ISO 8601)', 'example': '2025-06-30'},
                    {'in': 'query', 'name': 'category_id', 'type': 'integer'},
                    {'in': 'query', 'name': 'type', 'type': 'string',
                     'enum': ['income', 'expense', 'all'], 'default': 'all'},
                    {'in': 'query', 'name': 'min_amount', 'type': 'integer',
                     'description': 'Мінімальна сума у копійках'},
                    {'in': 'query', 'name': 'max_amount', 'type': 'integer'},
                    {'in': 'query', 'name': 'page', 'type': 'integer', 'default': 1},
                    {'in': 'query', 'name': 'per_page', 'type': 'integer',
                     'default': 20, 'maximum': 100},
                ],
                'responses': {
                    '200': {
                        'description': 'Пагінований список транзакцій',
                        'schema': {'$ref': '#/definitions/TransactionPage'},
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            },
            'post': {
                'tags': ['Transactions'],
                'summary': 'Створити ручну транзакцію',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {'$ref': '#/definitions/TransactionCreate'},
                    }
                ],
                'responses': {
                    '201': {
                        'description': 'Транзакцію створено',
                        'schema': {'$ref': '#/definitions/Transaction'},
                    },
                    '422': {'description': 'Помилка валідації'},
                },
            },
        },
        '/api/transactions/{id}': {
            'put': {
                'tags': ['Transactions'],
                'summary': 'Змінити категорію транзакції',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'},
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['category_id'],
                            'properties': {
                                'category_id': {'type': 'integer'},
                            },
                        },
                    },
                ],
                'responses': {
                    '200': {
                        'description': 'Транзакцію оновлено',
                        'schema': {'$ref': '#/definitions/Transaction'},
                    },
                    '404': {'description': 'Транзакцію не знайдено'},
                },
            },
            'delete': {
                'tags': ['Transactions'],
                'summary': 'Видалити ручну транзакцію',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'}
                ],
                'responses': {
                    '200': {'description': 'Транзакцію видалено'},
                    '403': {'description': 'Дозволено лише для ручних транзакцій'},
                    '404': {'description': 'Транзакцію не знайдено'},
                },
            },
        },

        # ── Categories ────────────────────────────────────────────────────────
        '/api/categories': {
            'get': {
                'tags': ['Categories'],
                'summary': 'Дерево категорій (системні + особисті)',
                'security': [{'cookieAuth': []}],
                'responses': {
                    '200': {
                        'description': 'Масив категорій з дочірніми',
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/CategoryTree'},
                        },
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            },
            'post': {
                'tags': ['Categories'],
                'summary': 'Створити власну категорію',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['name'],
                            'properties': {
                                'name': {'type': 'string', 'example': 'Кафе'},
                                'icon': {'type': 'string', 'example': '☕'},
                                'parent_id': {'type': 'integer', 'nullable': True},
                            },
                        },
                    }
                ],
                'responses': {
                    '201': {
                        'description': 'Категорію створено',
                        'schema': {'$ref': '#/definitions/Category'},
                    },
                    '404': {'description': 'Батьківська категорія не знайдена'},
                    '422': {'description': 'Помилка валідації'},
                },
            },
        },
        '/api/categories/{id}': {
            'put': {
                'tags': ['Categories'],
                'summary': 'Оновити назву або іконку категорії',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'},
                    {
                        'in': 'body',
                        'name': 'body',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'icon': {'type': 'string'},
                            },
                        },
                    },
                ],
                'responses': {
                    '200': {
                        'description': 'Категорію оновлено',
                        'schema': {'$ref': '#/definitions/Category'},
                    },
                    '404': {'description': 'Категорію не знайдено або це системна категорія'},
                },
            },
            'delete': {
                'tags': ['Categories'],
                'summary': 'Видалити категорію (транзакції перенесуться у "Інше")',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'}
                ],
                'responses': {
                    '200': {'description': 'Категорію видалено'},
                    '404': {'description': 'Категорію не знайдено або це системна категорія'},
                },
            },
        },

        # ── Budgets ───────────────────────────────────────────────────────────
        '/api/budgets': {
            'get': {
                'tags': ['Budgets'],
                'summary': 'Бюджети на місяць із сумами витрат',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {
                        'in': 'query',
                        'name': 'month',
                        'type': 'string',
                        'description': 'Місяць у форматі YYYY-MM',
                        'example': '2025-06',
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Масив бюджетів з прогресом',
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/Budget'},
                        },
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            },
            'post': {
                'tags': ['Budgets'],
                'summary': 'Створити бюджет на місяць для категорії',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['category_id', 'month', 'planned_amount'],
                            'properties': {
                                'category_id': {'type': 'integer'},
                                'month': {'type': 'string', 'example': '2025-06'},
                                'planned_amount': {
                                    'type': 'integer',
                                    'description': 'Планова сума у копійках',
                                    'example': 500000,
                                },
                            },
                        },
                    }
                ],
                'responses': {
                    '201': {
                        'description': 'Бюджет створено',
                        'schema': {'$ref': '#/definitions/Budget'},
                    },
                    '404': {'description': 'Категорію не знайдено'},
                    '409': {'description': 'Бюджет для цієї категорії на цей місяць вже існує'},
                    '422': {'description': 'Помилка валідації'},
                },
            },
        },
        '/api/budgets/copy': {
            'post': {
                'tags': ['Budgets'],
                'summary': 'Скопіювати бюджети з одного місяця в інший',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['from_month', 'to_month'],
                            'properties': {
                                'from_month': {'type': 'string', 'example': '2025-05'},
                                'to_month': {'type': 'string', 'example': '2025-06'},
                            },
                        },
                    }
                ],
                'responses': {
                    '201': {
                        'description': 'Нові бюджети (вже існуючі пропускаються)',
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/Budget'},
                        },
                    },
                    '404': {'description': 'Бюджети за from_month не знайдено'},
                    '422': {'description': 'from_month та to_month однакові'},
                },
            }
        },
        '/api/budgets/{id}': {
            'put': {
                'tags': ['Budgets'],
                'summary': 'Змінити планову суму бюджету',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'},
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['planned_amount'],
                            'properties': {
                                'planned_amount': {'type': 'integer', 'example': 700000},
                            },
                        },
                    },
                ],
                'responses': {
                    '200': {
                        'description': 'Бюджет оновлено',
                        'schema': {'$ref': '#/definitions/Budget'},
                    },
                    '404': {'description': 'Бюджет не знайдено'},
                },
            },
            'delete': {
                'tags': ['Budgets'],
                'summary': 'Видалити бюджет',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {'in': 'path', 'name': 'id', 'required': True, 'type': 'integer'}
                ],
                'responses': {
                    '200': {'description': 'Бюджет видалено'},
                    '404': {'description': 'Бюджет не знайдено'},
                },
            },
        },

        # ── Analytics ─────────────────────────────────────────────────────────
        '/api/analytics/spending-by-category': {
            'get': {
                'tags': ['Analytics'],
                'summary': 'Витрати по категоріях (для кругової діаграми)',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {'in': 'query', 'name': 'from', 'type': 'string', 'format': 'date-time',
                     'example': '2025-06-01T00:00:00'},
                    {'in': 'query', 'name': 'to', 'type': 'string', 'format': 'date-time',
                     'example': '2025-06-30T23:59:59'},
                ],
                'responses': {
                    '200': {
                        'description': 'Масив категорій із сумами та відсотками',
                        'schema': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'category_id': {'type': 'integer'},
                                    'category': {'$ref': '#/definitions/CategoryRef'},
                                    'amount': {'type': 'integer'},
                                    'percentage': {'type': 'number'},
                                },
                            },
                        },
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            }
        },
        '/api/analytics/monthly-trend': {
            'get': {
                'tags': ['Analytics'],
                'summary': 'Тренд доходів і витрат по місяцях',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {
                        'in': 'query',
                        'name': 'months',
                        'type': 'integer',
                        'default': 12,
                        'minimum': 1,
                        'maximum': 24,
                        'description': 'Кількість місяців для аналізу',
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Масив точок тренду',
                        'schema': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'month': {'type': 'string', 'example': '2025-06'},
                                    'income': {'type': 'integer'},
                                    'expense': {'type': 'integer'},
                                },
                            },
                        },
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            }
        },
        '/api/analytics/daily-heatmap': {
            'get': {
                'tags': ['Analytics'],
                'summary': 'Теплова карта активності (день тижня × година)',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {
                        'in': 'query',
                        'name': 'month',
                        'type': 'string',
                        'description': 'Місяць у форматі YYYY-MM (за замовчуванням — поточний)',
                        'example': '2025-06',
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Масив клітинок теплової карти',
                        'schema': {
                            'type': 'array',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'day': {'type': 'integer', 'description': '0=Нд … 6=Сб'},
                                    'hour': {'type': 'integer', 'minimum': 0, 'maximum': 23},
                                    'amount': {'type': 'integer'},
                                },
                            },
                        },
                    },
                    '401': {'description': 'Не авторизовано'},
                    '422': {'description': 'Невірний формат місяця'},
                },
            }
        },
        '/api/analytics/summary': {
            'get': {
                'tags': ['Analytics'],
                'summary': 'Підсумок: доходи, витрати, баланс, топ-5 категорій',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {'in': 'query', 'name': 'from', 'type': 'string', 'format': 'date-time'},
                    {'in': 'query', 'name': 'to', 'type': 'string', 'format': 'date-time'},
                ],
                'responses': {
                    '200': {
                        'description': 'Фінансовий підсумок',
                        'schema': {'$ref': '#/definitions/Summary'},
                    },
                    '401': {'description': 'Не авторизовано'},
                },
            }
        },

        # ── Balance ───────────────────────────────────────────────────────────
        '/api/balance/{month}': {
            'get': {
                'tags': ['Balance'],
                'summary': 'Отримати місячний баланс',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'month',
                        'required': True,
                        'type': 'string',
                        'description': 'Формат YYYY-MM',
                        'example': '2025-06',
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Баланс за місяць',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'month': {'type': 'string'},
                                'amount': {'type': 'integer'},
                            },
                        },
                    },
                    '401': {'description': 'Не авторизовано'},
                    '422': {'description': 'Невірний формат місяця'},
                },
            },
            'put': {
                'tags': ['Balance'],
                'summary': 'Встановити місячний баланс',
                'security': [{'cookieAuth': []}, {'csrfToken': []}],
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'month',
                        'required': True,
                        'type': 'string',
                        'example': '2025-06',
                    },
                    {
                        'in': 'body',
                        'name': 'body',
                        'required': True,
                        'schema': {
                            'type': 'object',
                            'required': ['amount'],
                            'properties': {
                                'amount': {
                                    'type': 'integer',
                                    'description': 'Баланс у копійках',
                                    'example': 500000,
                                },
                            },
                        },
                    },
                ],
                'responses': {
                    '200': {
                        'description': 'Баланс збережено',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'month': {'type': 'string'},
                                'amount': {'type': 'integer'},
                            },
                        },
                    },
                    '422': {'description': 'Невірні дані'},
                },
            },
        },

        # ── Rates ─────────────────────────────────────────────────────────────
        '/api/rates/current': {
            'get': {
                'tags': ['Rates'],
                'summary': 'Поточні курси валют (PrivatBank, кеш 1 год)',
                'security': [{'cookieAuth': []}],
                'responses': {
                    '200': {
                        'description': 'Масив курсів',
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/Rate'},
                        },
                    },
                    '503': {'description': 'PrivatBank API недоступний'},
                },
            }
        },
        '/api/rates/archive': {
            'get': {
                'tags': ['Rates'],
                'summary': 'Архівні курси на конкретну дату',
                'security': [{'cookieAuth': []}],
                'parameters': [
                    {
                        'in': 'query',
                        'name': 'date',
                        'required': True,
                        'type': 'string',
                        'description': 'Формат DD.MM.YYYY',
                        'example': '01.06.2025',
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Архівні курси',
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/Rate'},
                        },
                    },
                    '422': {'description': 'Невірний формат дати'},
                    '503': {'description': 'PrivatBank API недоступний'},
                },
            }
        },

        # ── Webhooks ──────────────────────────────────────────────────────────
        '/api/webhooks/monobank': {
            'post': {
                'tags': ['Webhooks'],
                'summary': 'Вебхук від Monobank (StatementItem)',
                'description': (
                    'Викликається Monobank при нових транзакціях. '
                    'Перевіряє секрет у query-параметрі, '
                    'зберігає транзакцію та перевіряє бюджет.'
                ),
                'parameters': [
                    {
                        'in': 'query',
                        'name': 'secret',
                        'required': True,
                        'type': 'string',
                        'description': 'WEBHOOK_SECRET з конфігурації',
                    },
                    {
                        'in': 'body',
                        'name': 'body',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'type': {'type': 'string', 'example': 'StatementItem'},
                                'data': {
                                    'type': 'object',
                                    'properties': {
                                        'account': {'type': 'string', 'description': 'bank_account_id'},
                                        'statementItem': {
                                            'type': 'object',
                                            'properties': {
                                                'id': {'type': 'string'},
                                                'time': {'type': 'integer', 'description': 'Unix timestamp'},
                                                'amount': {'type': 'integer', 'description': 'Копійки (< 0 = витрата)'},
                                                'mcc': {'type': 'integer'},
                                                'description': {'type': 'string'},
                                                'currencyCode': {'type': 'integer', 'example': 980},
                                                'balance': {'type': 'integer'},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                ],
                'responses': {
                    '200': {'description': 'Оброблено успішно'},
                    '401': {'description': 'Невірний секрет'},
                },
            }
        },
    },

    # ── Definitions / Models ─────────────────────────────────────────────────
    'definitions': {
        'User': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'email': {'type': 'string', 'format': 'email'},
                'default_currency': {'type': 'string', 'example': 'UAH'},
                'manual_balance': {'type': 'integer'},
            },
        },
        'Account': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'bank_type': {'type': 'string', 'example': 'monobank'},
                'bank_account_id': {'type': 'string'},
                'currency_code': {'type': 'integer', 'example': 980},
                'balance': {'type': 'integer', 'description': 'Баланс у копійках'},
                'last_sync_at': {'type': 'string', 'format': 'date-time', 'nullable': True},
            },
        },
        'Transaction': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'amount': {'type': 'integer', 'description': 'Копійки (< 0 = витрата)'},
                'description': {'type': 'string'},
                'transaction_type': {'type': 'string', 'enum': ['income', 'expense']},
                'currency_code': {'type': 'integer', 'example': 980},
                'timestamp': {'type': 'string', 'format': 'date-time'},
                'is_manual': {'type': 'boolean'},
                'category_id': {'type': 'integer', 'nullable': True},
                'category': {'$ref': '#/definitions/CategoryRef'},
                'mcc_code': {'type': 'integer', 'nullable': True},
            },
        },
        'TransactionCreate': {
            'type': 'object',
            'required': ['amount', 'type', 'timestamp'],
            'properties': {
                'amount': {
                    'type': 'integer',
                    'description': 'Абсолютна сума у копійках (завжди додатня)',
                    'example': 15000,
                },
                'type': {
                    'type': 'string',
                    'enum': ['income', 'expense'],
                    'description': 'Тип транзакції (знак визначається автоматично)',
                },
                'timestamp': {'type': 'string', 'format': 'date-time', 'example': '2025-06-15T12:30:00'},
                'description': {'type': 'string', 'example': 'Обід'},
                'category_id': {'type': 'integer', 'nullable': True},
                'currency_code': {'type': 'integer', 'default': 980},
            },
        },
        'TransactionPage': {
            'type': 'object',
            'properties': {
                'items': {
                    'type': 'array',
                    'items': {'$ref': '#/definitions/Transaction'},
                },
                'total': {'type': 'integer'},
                'page': {'type': 'integer'},
                'per_page': {'type': 'integer'},
                'pages': {'type': 'integer'},
            },
        },
        'Category': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'icon': {'type': 'string', 'nullable': True},
                'user_id': {'type': 'integer', 'nullable': True, 'description': 'null = системна'},
                'parent_id': {'type': 'integer', 'nullable': True},
                'is_default': {'type': 'boolean'},
            },
        },
        'CategoryRef': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'icon': {'type': 'string', 'nullable': True},
            },
        },
        'CategoryTree': {
            'allOf': [
                {'$ref': '#/definitions/Category'},
                {
                    'type': 'object',
                    'properties': {
                        'children': {
                            'type': 'array',
                            'items': {'$ref': '#/definitions/CategoryTree'},
                        }
                    },
                },
            ]
        },
        'Budget': {
            'type': 'object',
            'properties': {
                'id': {'type': 'integer'},
                'category_id': {'type': 'integer'},
                'month': {'type': 'string', 'example': '2025-06'},
                'planned_amount': {'type': 'integer', 'description': 'Копійки'},
                'spent': {'type': 'integer', 'description': 'Витрачено за місяць (копійки)'},
                'remaining': {'type': 'integer'},
                'progress': {'type': 'number', 'description': '0.0 … 1.0+'},
                'category': {'$ref': '#/definitions/CategoryRef'},
            },
        },
        'Summary': {
            'type': 'object',
            'properties': {
                'total_income': {'type': 'integer'},
                'total_expense': {'type': 'integer'},
                'balance': {'type': 'integer'},
                'top_categories': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'category_id': {'type': 'integer'},
                            'category': {'$ref': '#/definitions/CategoryRef'},
                            'amount': {'type': 'integer'},
                        },
                    },
                },
            },
        },
        'Rate': {
            'type': 'object',
            'properties': {
                'ccy': {'type': 'string', 'example': 'USD'},
                'base_ccy': {'type': 'string', 'example': 'UAH'},
                'buy': {'type': 'string', 'example': '39.85'},
                'sale': {'type': 'string', 'example': '40.15'},
            },
        },
    },
}
