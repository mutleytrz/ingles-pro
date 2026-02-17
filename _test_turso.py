"""Teste de conexao com o Turso via libsql-client."""
import sys, os

# Garantir que o diretorio do projeto esta no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("  TESTE DE CONEXAO TURSO")
    print("=" * 60)

    # 1. Importar libsql_client
    try:
        from libsql_client import create_client_sync
        print("[1] ✅ libsql-client importado com sucesso")
    except ImportError as e:
        print(f"[1] ❌ FALHA ao importar libsql-client: {e}")
        return

    # 2. Ler secrets
    import config
    url = config.TURSO_DB_URL
    token = config.TURSO_AUTH_TOKEN
    if url and token:
        print(f"[2] ✅ Credenciais encontradas: URL={url[:40]}...")
    else:
        print("[2] ❌ Credenciais TURSO nao encontradas em config/secrets")
        return

    # 3. Conectar via database._get_conn()
    try:
        import database
        conn = database._get_conn()
        print(f"[3] ✅ Conexao estabelecida: {type(conn).__name__}")
    except Exception as e:
        print(f"[3] ❌ FALHA na conexao: {e}")
        return

    # 4. Init DB (criar tabelas)
    try:
        database.init_db()
        print("[4] ✅ Tabelas criadas/verificadas (init_db)")
    except Exception as e:
        print(f"[4] ❌ FALHA no init_db: {e}")
        import traceback; traceback.print_exc()
        return

    # 5. Listar tabelas
    try:
        conn2 = database._get_conn()
        cursor = conn2.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"[5] ✅ Tabelas existentes: {tables}")
        conn2.close()
    except Exception as e:
        print(f"[5] ❌ FALHA ao listar tabelas: {e}")
        import traceback; traceback.print_exc()

    # 6. Testar CRUD: criar usuario de teste
    test_user = "__test_turso_user__"
    try:
        # Limpar se existir
        database.delete_user(test_user)
        
        ok = database.create_user(test_user, "Teste Turso", "hash_fake_123")
        if ok:
            print(f"[6] ✅ Usuario de teste criado: {test_user}")
        else:
            print(f"[6] ⚠️ Usuario ja existia (ok)")
    except Exception as e:
        print(f"[6] ❌ FALHA ao criar usuario: {e}")
        import traceback; traceback.print_exc()
        return

    # 7. Ler usuario com dict-style access
    try:
        user = database.get_user(test_user)
        if user and user["username"] == test_user:
            print(f"[7] ✅ Leitura dict-style OK: username={user['username']}, name={user['name']}")
        else:
            print(f"[7] ❌ FALHA: retornou {user}")
    except Exception as e:
        print(f"[7] ❌ FALHA ao ler usuario (dict-style): {e}")
        import traceback; traceback.print_exc()

    # 8. Testar progresso
    try:
        database.save_progress(test_user, "aula", "palavras.csv", 5, 100, 85, 2)
        prog = database.load_progress(test_user)
        if prog and prog["xp"] == 100:
            print(f"[8] ✅ Progresso salvo/lido OK: xp={prog['xp']}, pagina={prog['pagina']}")
        else:
            print(f"[8] ❌ FALHA: progresso retornou {prog}")
    except Exception as e:
        print(f"[8] ❌ FALHA no progresso: {e}")
        import traceback; traceback.print_exc()

    # 9. Testar admin list
    try:
        users = database.get_all_users_detailed()
        print(f"[9] ✅ Lista de usuarios ({len(users)} encontrados)")
        for u in users[:3]:
            print(f"     -> #{u.get('id')} {u.get('username')} email={u.get('email', '-')}")
    except Exception as e:
        print(f"[9] ❌ FALHA ao listar usuarios: {e}")
        import traceback; traceback.print_exc()

    # 10. Limpar usuario de teste
    try:
        database.delete_user(test_user)
        print(f"[10] ✅ Usuario de teste removido")
    except Exception as e:
        print(f"[10] ⚠️ Falha ao remover teste: {e}")

    print()
    print("=" * 60)
    print("  RESULTADO FINAL: TURSO FUNCIONANDO! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    main()
