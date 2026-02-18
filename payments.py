# payments.py — Integração com Mercado Pago

import mercadopago
import config
from typing import Optional, Any
import streamlit as st

def get_mp_sdk():
    """Inicializa o SDK do Mercado Pago."""
    if not config.MP_ACCESS_TOKEN:
        return None
    try:
        return mercadopago.SDK(config.MP_ACCESS_TOKEN)
    except Exception as e:
        print(f"[ERR] SDK Init: {e}")
        return None

def create_checkout_preference(username: str, email: str, title: str, price: float, plan_type: str = "vitalicio") -> Optional[str]:
    """
    Cria uma preferência de pagamento e retorna a URL de checkout.
    """
    sdk = get_mp_sdk()
    if sdk is None:
        return None

    # Base URL para retorno (pode vir do config ou deduzir do Streamlit)
    # Em prod, ideal usar uma variavél de ambiente para a URL base.
    # Normalize base_url: remove trailing slashes
    base_url = config.BASE_URL.rstrip('/')
    
    # Construct URLs
    success_url = f"{base_url}/"
    failure_url = f"{base_url}/"
    pending_url = f"{base_url}/"
    
    # Add status parameters
    success_url += "?payment_status=success"
    failure_url += "?payment_status=failure"
    pending_url += "?payment_status=pending"
    
    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "unit_price": float(price),
                "currency_id": "BRL"
            }
        ],
        "payer": {
            "email": email
        },
        "external_reference": f"{username}|{plan_type}",
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url
        },
        "auto_return": "approved",
    }
    
    try:
        preference_response = sdk.preference().create(preference_data)
        status = preference_response.get("status")
        
        if status == 201 and "response" in preference_response:
             preference = preference_response["response"]
             return preference.get("init_point")
        
        # Log failure with more detail for the user
        print(f"[MP ERR] Status: {status}")
        print(f"[MP ERR] Full Response: {preference_response}")
        st.error(f"Erro na API Mercado Pago (Status {status}): {preference_response.get('response', {}).get('message', 'Erro desconhecido')}")
        return None
    except Exception as e:
        import traceback
        error_msg = f"Erro detalhado ao criar preferência MP: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        st.error(f"Erro na API do Mercado Pago: {e}")
        return None

def verify_payment(payment_id: str) -> Optional[dict]:
    """
    Verifica se um pagamento foi aprovado e retorna os dados brutos da resposta.
    """
    sdk = get_mp_sdk()
    if sdk is None or not payment_id:
        return None

    try:
        payment_info = sdk.payment().get(payment_id)
        if payment_info.get("status") == 200:
            return payment_info["response"]
    except Exception as e:
        print(f"[ERR] verify_payment: {e}")
    
    return None
