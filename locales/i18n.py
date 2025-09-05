#locales/i18n.py
class Localization:
    def __init__(self, locale_dir="locales"):
        self.locale_dir = locale_dir
        self.strings = {}
        self.current_lang = "en"

    def load_language(self, lang_code):
        try:
            with open(os.path.join(self.locale_dir, f"{lang_code}.json")) as f:
                self.strings = json.load(f)
                self.current_lang = lang_code
        except FileNotFoundError:
            logger.warning(f"Language pack not found: {lang_code}")

    def tr(self, key):
        """Получение переведённой строки"""
        return self.strings.get(key, key)