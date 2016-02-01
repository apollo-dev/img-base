cp db/img_db.sqlite3 db/img_db_backup.sqlite3;
sh scripts/remove_migrations.sh
sh scripts/make_migrations.sh
python3 manage.py migrate
