from pathlib import Path

from app.domain.schemas import NormalizedDiff


class DiffService:
    SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".lock", ".min.js", ".map"}

    def normalize(self, changed_files: list[dict]) -> NormalizedDiff:
        files = []
        additions = 0
        deletions = 0
        languages = set()

        for item in changed_files:
            filename = item.get("filename", "")
            if self._ignore_file(filename):
                continue
            ext = Path(filename).suffix.lower()
            additions += int(item.get("additions", 0))
            deletions += int(item.get("deletions", 0))
            if ext:
                languages.add(ext.replace(".", ""))
            files.append(
                {
                    "filename": filename,
                    "status": item.get("status", "modified"),
                    "additions": item.get("additions", 0),
                    "deletions": item.get("deletions", 0),
                    "patch": item.get("patch", "")[:5000],
                }
            )

        return NormalizedDiff(
            files=files,
            file_count=len(files),
            additions=additions,
            deletions=deletions,
            languages_detected=sorted(languages),
        )

    def _ignore_file(self, filename: str) -> bool:
        path = Path(filename)
        if any(part in {"node_modules", "dist", "build", ".git"} for part in path.parts):
            return True
        return any(filename.endswith(suffix) for suffix in self.SKIP_SUFFIXES)
