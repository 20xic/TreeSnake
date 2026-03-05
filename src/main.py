from core.creator import DirectoryCreator, FileCreator
from core.file_reader import FileReader
from core.formatter import LLMFormatter
from core.scanner import BaseScanner
from core.template_creator import YamlTemplateCreator
from models.scan_config import ScanConfig

if __name__ == "__main__":
    scanner = BaseScanner()
    dir = scanner.scan("./src", config=ScanConfig())

    formatter = LLMFormatter()
    print(formatter.format(dir))
    file_reader = FileReader()
    file = file_reader.read("./treesnake.exe")
    print(file)
    file_creator = FileCreator()

    directory_creator = DirectoryCreator()
    directory_creator.create("./test")
    file_creator.create("./test/test.txt", "hello!")
    template_creator = YamlTemplateCreator(file_creator=file_creator)
    template_creator.create("./")
