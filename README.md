# JustMC File Host

Простой файлообменник для модулей JustMC Creative+. Разворачивается на Render.

## Struktura

```
/justmc-filehost
├── app.py              # Flask сервер
├── requirements.txt    # Зависимости
├── Procfile            # Для Render
├── render.yaml         # Конфиг Render
└── files/
    └── ultimate_pvp.json  # Твой модуль PvP арены
```

## Деплой на Render (бесплатно)

### Способ 1: Через GitHub + Render

1. Создай репозиторий на GitHub
2. Залей этот код:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/ТВОЙ_ЛОГИН/justmc-filehost.git
   git push -u origin main
   ```
3. Зайди на [render.com](https://render.com)
4. Connect GitHub → выбери репозиторий `justmc-filehost`
5. Render автоматически подхватит `render.yaml`
6. Deploy

### Способ 2: Через Render CLI (если установлен)

```bash
render deploy
```

## Использование в JustMC

После деплоя Render даст ссылку вида:
```
https://justmc-filehost-xxxx.onrender.com
```

Команда в игре (`creative.justmc.io`):

```
/module loadUrl https://justmc-filehost-xxxx.onrender.com/files/ultimate_pvp.json
```

Или с заменой всего кода:

```
/module loadUrl force https://justmc-filehost-xxxx.onrender.com/files/ultimate_pvp.json
```

Потом:

```
/play
```

## Прямая ссылка на модуль

```
https://justmc-filehost-xxxx.onrender.com/files/ultimate_pvp.json
```

## Локальный запуск для теста

```bash
pip install -r requirements.txt
python app.py
```

Сервер запустится на `http://localhost:5000`
Модуль доступен по: `http://localhost:5000/files/ultimate_pvp.json`
