# Настройка окружения

Установить улучшенный `pip` (называемый `pip-tools`)

```
pip install pip-tools
```

Установить зависимости, необходимые для запуска проекта (файл `requirements.txt`), и зависимости для разработки (файл `dev-requirements.txt`)

```
pip-sync requirements.txt dev-requirements.txt
```
# Запуск приложения

```bash
python main.py
```
