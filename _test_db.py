"""Quick verification of database and auth modules."""
from database import init_db, create_user, get_user, save_progress, load_progress, get_all_usersbaguncados 
import os

init_db()
print(f"DB exists: {os.path.exists('ingles_pro.db')}")

ok = create_user('test_user', 'Test User', '$2b$12$fakehashfortest')
print(f"create_user: {ok}")

u = get_user('test_user')
print(f"get_user: {u}")

save_progress('test_user', 'aula', 'escola.csv', 3, 50, 85, 1)
p = load_progress('test_user')
print(f"load_progress: {p}")

all_u = get_all_users()
print(f"get_all_users usernames: {list(all_u['usernames'].keys())}")

# Cleanup
os.remove('ingles_pro.db')
print("ALL TESTS PASSED")
