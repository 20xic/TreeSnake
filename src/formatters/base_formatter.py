from models import Directory, File


class BaseFormatter:
    def format_directory(self, directory: Directory, depth: int = 0):
        raise NotImplementedError

    def format_file(self, file: File, depth: int = 0):
        raise NotImplementedError
