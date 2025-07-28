#!/bin/bash
# Apply the license annotations to the project files
uvx reuse annotate --license=MPL-2.0 -r src/ --template siliconai --skip-unrecognised --skip-existing
uvx reuse annotate --license=MPL-2.0 -r tests/ --template siliconai --skip-unrecognised --skip-existing
