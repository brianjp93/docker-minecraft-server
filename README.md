# Backups

- Backups are being done using `restic`
- Get a list of snapshots
    - `restic snapshots`

### Restore a backup
```bash
# first do a backup
/start-backup
# then do restore of whatever snapshot you want
restic restore <snapshotID> --target /data/world
```
