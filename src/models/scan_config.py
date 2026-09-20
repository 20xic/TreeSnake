from pydantic import BaseModel, ConfigDict


class ScanConfig(BaseModel):
    exclude_dirs: list[str] = []
    exclude_files: list[str] = []
    exclude_content_dirs: list[str] = []
    exclude_content_files: list[str] = []
    include_dirs: list[str] = []
    include_files: list[str] = []
    max_depth: int | None = None
    max_file_size: int | None = None

    model_config = ConfigDict(from_attributes=True)
