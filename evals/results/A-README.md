# Migration procedure

Do not run either migration command while a restore is active.

1. Make sure that backup A is complete.
2. Run `atlasctl migrate --dry-run`.
3. If this command does not return 0, stop the procedure.
4. If this command returns 0, run `atlasctl migrate --target "North Lab"`.

The button name is **Force Sync**.
