# Override wiring

Not installed. Not a live path change.

`scripts/build.py` and `scripts/merge.py` read `ROOT/data/user_overrides.json`. ROOT is the parent of the `scripts` directory. On a training-dashboard tree that file is `training-dashboard/data/user_overrides.json`.

The canonical fitness file is separate: `fitness-dashboard/user_overrides.json`. The generators do not open that path. A future install could point the training path at the canonical file with a symlink. That symlink is not created here, and `/workspace/training-dashboard` is not created here.

The isolated test copies the generators into a temp `training-dashboard/scripts` directory and links `training-dashboard/data/user_overrides.json` to a temp `fitness-dashboard/user_overrides.json`. Both commands exit 0 and the class history keeps the established provider baseline. Rollback of a future install would be to remove only that symlink if it still points at the canonical file.

`provider_cancellation_verified` stays false unless an override fixture explicitly says true. This branch does not include such a fixture. A CANCELLED value in the feed column is not that evidence.
