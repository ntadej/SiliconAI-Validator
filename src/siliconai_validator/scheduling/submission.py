# Copyright (C) 2024 Tadej Novak
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0

"""Submission helpers and utilities."""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

CONTAINER_PATH = "/cvmfs/atlas.cern.ch/repo/containers/fs/singularity/x86_64-almalinux9"


def create_slurm_submission_script(name: str, run_path: Path) -> Path:
    """Create Slurm submission script."""
    job_name = f"SiliconAI_Validator_{name}"
    submission_file = run_path / "submit.sh"
    slurm_log = run_path / "proc_%a/slurm.log"
    success_file = run_path / "proc_${SLURM_ARRAY_TASK_ID}/SUCCESS"
    run_script = run_path / "proc_${SLURM_ARRAY_TASK_ID}/run.sh"

    if not run_path.exists():
        run_path.mkdir(parents=True)

    with submission_file.open("w") as file:
        file.write(
            "#!/bin/bash\n"
            "\n"
            f'#SBATCH --job-name="{job_name}"\n'
            "#SBATCH --nodes=1\n"
            "#SBATCH --ntasks=1\n"
            "#SBATCH --time=03:00:00\n"
            f"#SBATCH --output={slurm_log}\n"
            "\n"
            'echo "Job ID: ${SLURM_ARRAY_JOB_ID}"\n'
            'echo "Array ID: ${SLURM_ARRAY_TASK_ID}"\n'
            "\n"
            "pwd\n"
            "\n"
            f"singularity run {CONTAINER_PATH} {run_script}\n"
            f"if [ $? -eq 0 ]; then touch {success_file}; fi\n",
        )

    return submission_file


def create_slurm_run_script(run_path: Path, command: str) -> Path:
    """Create Slurm run script."""
    run_script = run_path / "run.sh"

    with run_script.open("w") as file:
        file.write(
            f"#!/bin/bash\n\nsource ./scripts/setup_environment_only.sh\n\n{command}\n",
        )

    run_script.chmod(run_script.stat().st_mode | stat.S_IEXEC)

    return run_script
