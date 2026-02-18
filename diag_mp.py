import config
import payments

def diag():
    print(f"DEBUG: MP_ACCESS_TOKEN length: {len(config.MP_ACCESS_TOKEN)}")
    print(f"DEBUG: MP_ACCESS_TOKEN starts with: {config.MP_ACCESS_TOKEN[:15]}")
    print(f"DEBUG: MP_PUBLIC_KEY length: {len(config.MP_PUBLIC_KEY)}")
    
    sdk = payments.get_mp_sdk()
    if sdk:
        print("SDK initialized successfully.")
    else:
        print("SDK failed to initialize.")

if __name__ == "__main__":
    diag()
