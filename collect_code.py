# collect_code.py
import os

# Список папок и файлов, которые нужно включить
paths_to_include = [
    'main.py',
    'config.json',
    'logs.txt',
    'requirements.txt',
    'core',
    'ui'
    'icons'
]

# Имя итогового файла
output_filename = "full_project_code.txt"


def collect_files():
    all_files = []
    for path in paths_to_include:
        if os.path.isfile(path):
            all_files.append(path)
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    # Включаем только файлы с нужными расширениями
                    if file.endswith(('.py', '.json', '.txt', '.md')):
                        all_files.append(os.path.join(root, file))
    return all_files


def main():
    files_to_process = collect_files()

    # Открываем итоговый файл для записи в кодировке UTF-8
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        print(f"Найдено {len(files_to_process)} файлов. Начинаю сборку в {output_filename}...")

        for filepath in sorted(files_to_process):
            try:
                # Пишем заголовок
                header = f"--- Файл: {filepath.replace(os.sep, '/')} ---\n\n"
                outfile.write(header)

                # Читаем исходный файл в кодировке UTF-8
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
                    content = infile.read()
                    outfile.write(content)

                # Пишем разделитель
                outfile.write("\n\n")
            except Exception as e:
                error_message = f"--- Ошибка чтения файла: {filepath} ---\n{e}\n\n"
                outfile.write(error_message)
                print(f"Произошла ошибка при чтении файла {filepath}: {e}")

    print("Сборка кода успешно завершена!")


if __name__ == "__main__":
    main()