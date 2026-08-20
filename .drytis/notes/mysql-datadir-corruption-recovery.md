# MySQL datadir corruption recovery — 2026-08-20

## Symptom
After an idle-pause/resume (~10:08 UTC), preview showed 502. procmgr: backend-api
STOPPED, mysql STOPPED. Backend log: pymysql 2003 connection refused. MariaDB
direct start aborted: `InnoDB: File './/undo001' is corrupted`. One file
(`/var/lib/mysql/ddl_recovery-backup.log`) has unreadable inode metadata
(`ls` → "Bad message", `rm` fails even as root) — disk/filesystem damage on the
shared nvme0n1 volume.

## DANGER — disk layout
`/dev/nvme0n1` is bind-mounted at **four** paths: `/workspace`, `/var/lib/mysql`,
`/home/coder`, `/var/logs`. NEVER mkfs it — it is the same volume as all project
code. mkfs on it while mounted will be refused anyway; do not work around that.

## Recovery that worked
1. Start in recovery mode: `sudo mariadbd --user=mysql --datadir=/var/lib/mysql --innodb-force-recovery=5` (takes ~30-60s; TCP probe may time out first try — check the log for "ready for connections")
2. `mysqldump` all data to /tmp (worked fine in recovery mode)
3. `sudo pkill -x mariadbd` (stop recovery instance)
4. Delete datadir contents: `sudo rm -f /var/lib/mysql/{aria_log*,ib_*,undo*,multi-master.info,mariadb_upgrade_info,debian-*.flag}` (the Bad-message file can't be deleted — harmless leftover)
5. `sudo mariadb-install-db --user=mysql --datadir=/var/lib/mysql`
6. Fresh server binds but rejects TCP with 1130 → recreate user via **socket** root:
   `sudo mariadb -e "CREATE USER 'u2512p3115_user'@'localhost' IDENTIFIED BY '...'; CREATE USER ...@'127.0.0.1' ...; CREATE DATABASE ...; GRANT ALL ...; FLUSH PRIVILEGES;"`
   (see get_project_details database{} for current creds/db name)
7. Restore: `mysql -u <user> -p<pass> -h 127.0.0.1 <db> < dump.sql`
8. `procmgr restart mysql` then `procmgr restart service-bg-3882`

## Result
5760 metric rows, reports, pipeline runs all restored; procmgr RUNNING;
preview + API 200.

## Follow-ups
- If 1130/"not allowed to connect" appears on a fresh install: users exist only
  for socket root by default — always create both @'localhost' and @'127.0.0.1'.
- The unreadable `ddl_recovery-backup.log` inode remains; benign but if MariaDB
  ever fails on startup listing it, repeat steps 4-8.
- Root cause: container pause during InnoDB write → torn undo page. Consider
  adding a periodic mysqldump cron for cheap insurance.
