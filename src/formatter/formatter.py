from src.domain import Directory, File


class BaseFormatter:
    def format_directory(self, directory: Directory, depth: int = 0) -> str:
        raise NotImplementedError
    
    def format_file(self, file: File, depth: int = 0) -> str:
        raise NotImplementedError


class TreeFormatter(BaseFormatter):
    def format_directory(self, directory: Directory, depth: int = 0) -> str:
        lines = []
        
    
        if depth == 0:
            prefix = ""
        else:
            prefix = "│   " * (depth - 1) + "├── "
        
        dir_prefix = f"{prefix}{directory.name}/"
        if directory.skip_content:
            dir_prefix += " [СОДЕРЖИМОЕ ИСКЛЮЧЕНО]"
        lines.append(dir_prefix)
        
        if directory.skip_content:
            if depth == 0:
                lines.append("└── [СОДЕРЖИМОЕ ДИРЕКТОРИИ ИСКЛЮЧЕНО]")
            else:
                lines.append(f"{'│   ' * depth}└── [СОДЕРЖИМОЕ ДИРЕКТОРИИ ИСКЛЮЧЕНО]")
            return "\n".join(lines)
        
        for i, subdir in enumerate(directory.subdirectories):
            is_last_dir = (i == len(directory.subdirectories) - 1) and (not directory.files)
            if is_last_dir:
                subdir_lines = self.format_directory(subdir, depth + 1)
                first_line = subdir_lines.split("\n", 1)[0]
                if "├── " in first_line:
                    first_line = first_line.replace("├── ", "└── ", 1)
                lines.append(first_line)
                if "\n" in subdir_lines:
                    lines.extend(subdir_lines.split("\n")[1:])
            else:
                lines.append(self.format_directory(subdir, depth + 1))
        
        for i, file in enumerate(directory.files):
            is_last = (i == len(directory.files) - 1)
            prefix = "│   " * depth
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{file.name}")
            
            if file.content:
                content_prefix = "│   " * (depth + 1)
                if file.content.startswith("[Binary file]") or file.content.startswith("[Error"):
                    lines.append(f"{content_prefix}└── {file.content}")
                else:
                    lines.append(f"{content_prefix}└── CONTENT:")
                    for line in file.content.split('\n'):
                        lines.append(f"{content_prefix}    {line}")
                    lines.append(content_prefix)
        
        return "\n".join(lines)
    
    def format_file(self, file: File, depth: int = 0) -> str:
        prefix = "│   " * depth
        lines = [f"{prefix}├── {file.name}"]
        
        if file.content:
            content_prefix = "│   " * (depth + 1)
            if file.content.startswith("[Binary file]") or file.content.startswith("[Error"):
                lines.append(f"{content_prefix}└── {file.content}")
            else:
                lines.append(f"{content_prefix}└── CONTENT:")
                for line in file.content.split('\n'):
                    lines.append(f"{content_prefix}    {line}")
                lines.append(content_prefix)
        
        return "\n".join(lines)


class LLMFormatter(BaseFormatter):
    def format_directory(self, directory: Directory, depth: int = 0) -> str:
        lines = []
        indent = "  " * depth
        
        dir_line = f"{indent}{directory.name}/"
        if directory.skip_content:
            dir_line += " [CONTENT EXCLUDED]"
        lines.append(dir_line)
        
        if directory.skip_content:
            return "\n".join(lines)
        
        for subdir in directory.subdirectories:
            lines.append(self.format_directory(subdir, depth + 1))
        
        for file in directory.files:
            file_indent = "  " * (depth + 1)
            lines.append(f"{file_indent}{file.name}")
            if file.content and not file.content.startswith("[Binary file]"):
                for line in file.content.split('\n'):
                    lines.append(f"{file_indent}  {line}")
        
        return "\n".join(lines)
    
    def format_file(self, file: File, depth: int = 0) -> str:
        indent = "  " * depth
        lines = [f"{indent}{file.name}"]
        
        if file.content and not file.content.startswith("[Binary file]"):
            for line in file.content.split('\n'):
                lines.append(f"{indent}  {line}")
        
        return "\n".join(lines)