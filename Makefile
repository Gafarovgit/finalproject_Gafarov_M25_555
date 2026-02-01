# Makefile
install:
    poetry install

project:
    poetry run project

build:
    poetry build

publish:
    poetry publish --dry-run

package-install:
    python3 -m pip install dist/*.whl

lint:
    poetry run ruff check .

# Новые команды для парсера
parser-update:
    python main.py --mode=parser update

parser-status:
    python main.py --mode=parser status

update-rates:
    poetry run project update-rates