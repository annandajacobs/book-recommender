def test_register_login_and_me(client):
    register_payload = {
        "nome": "Teste CI",
        "email": "ci@teste.com",
        "senha": "senha12345",
    }
    r = client.post("/api/v1/auth/register", json=register_payload)
    assert r.status_code == 201
    assert r.json()["email"] == "ci@teste.com"

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "ci@teste.com", "senha": "senha12345"},
    )
    assert r.status_code == 200
    token = r.json()["access_token"]
    assert token

    r = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    assert r.json()["email"] == "ci@teste.com"


def test_login_com_senha_errada_falha(client):
    client.post(
        "/api/v1/auth/register",
        json={"nome": "Teste", "email": "erro@teste.com", "senha": "senhacerta"},
    )
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "erro@teste.com", "senha": "senhaerrada"},
    )
    assert r.status_code == 401