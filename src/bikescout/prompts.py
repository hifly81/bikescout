# BikeScout - Tactical Intelligence for Cyclists
# Copyright (C) 2026 hifly81 (https://github.com/hifly81/bikescout)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from pathlib import Path

class BikeScoutPrompts:
    def __init__(self):
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.prompts_data = {}
        self._load_all_prompts()

    def _load_all_prompts(self):
        if self.prompts_dir.exists():
            for md_file in self.prompts_dir.glob("*.md"):
                slug = md_file.stem
                self.prompts_data[slug] = md_file.read_text(encoding="utf-8")
