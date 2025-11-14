import pytest
import json
import sys
sys.path.insert(0, '../src')
from api import app

@pytest.fixture
def client():
    """Cria cliente de teste"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ============================================
# TESTES ENDPOINT /health
# ============================================

def test_health_check(client):
    """Testa se API está online"""
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['modelos'] == True


# ============================================
# TESTES ENDPOINT /suggest_trilha
# ============================================

def test_suggest_trilha_advogado_cego(client):
    """Testa sugestão para advogado cego"""
    payload = {
        "area": "Advogado",
        "acessibilidade": "cego"
    }
    
    response = client.post('/suggest_trilha',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verificar estrutura da resposta
    assert 'trilha' in data
    assert 'modulos' in data
    assert 'adaptacoes' in data
    assert 'confianca' in data
    
    # Deve sugerir trilha acessível
    assert 'Acessível' in data['trilha']
    
    # Deve ter adaptações para cego
    assert 'text_to_speech' in data['adaptacoes']
    
    # Deve ter 5 módulos
    assert len(data['modulos']) == 5


def test_suggest_trilha_design_libras(client):
    """Testa sugestão para designer com Libras"""
    payload = {
        "area": "Design",
        "acessibilidade": "libras",
        "modulos_concluidos": 2,
        "tempo_plataforma_dias": 15
    }
    
    response = client.post('/suggest_trilha',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Deve ter adaptações Libras
    assert 'videos_libras' in data['adaptacoes']
    assert 'legendas_ativadas' in data['adaptacoes']


def test_suggest_trilha_sem_acessibilidade(client):
    """Testa sugestão sem acessibilidades"""
    payload = {
        "area": "Contabilidade",
        "acessibilidade": "nenhuma"
    }
    
    response = client.post('/suggest_trilha',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Sem acessibilidade = sem adaptações
    assert data['adaptacoes'] == []
    
    # Não deve ter "Acessível" no nome
    assert 'Acessível' not in data['trilha']


def test_suggest_trilha_campos_faltando(client):
    """Testa validação de campos obrigatórios"""
    payload = {
        "area": "Advogado"
        # Falta 'acessibilidade'
    }
    
    response = client.post('/suggest_trilha',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'erro' in data


# ============================================
# TESTES ENDPOINT /predict_sucesso
# ============================================

def test_predict_sucesso_alta(client):
    """Testa previsão com perfil forte"""
    payload = {
        "area": "SoftSkills",
        "acessibilidade": "nenhuma",
        "modulos_concluidos": 10,
        "tempo_plataforma_dias": 60
    }
    
    response = client.post('/predict_sucesso',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'taxa_sucesso' in data
    assert 'categoria' in data
    assert 'recomendacao' in data
    
    # Taxa deve estar entre 0 e 1
    assert 0.0 <= data['taxa_sucesso'] <= 1.0
    
    # Categoria deve ser uma das três
    assert data['categoria'] in ['alta', 'media', 'baixa']


def test_predict_sucesso_baixa(client):
    """Testa previsão com perfil fraco"""
    payload = {
        "area": "Logistica",
        "acessibilidade": "cego",
        "modulos_concluidos": 0,
        "tempo_plataforma_dias": 0
    }
    
    response = client.post('/predict_sucesso',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Taxa deve ser menor (usuário novo + acessibilidade)
    assert data['taxa_sucesso'] < 0.75


def test_predict_sucesso_campos_faltando(client):
    """Testa validação"""
    payload = {
        "area": "Design"
        # Falta 'acessibilidade'
    }
    
    response = client.post('/predict_sucesso',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 400


# ============================================
# TESTE DE PERFORMANCE
# ============================================

def test_tempo_resposta(client):
    """Testa se API responde rápido (<2s)"""
    import time
    
    payload = {
        "area": "Secretariado",
        "acessibilidade": "libras"
    }
    
    start = time.time()
    response = client.post('/suggest_trilha',
                          data=json.dumps(payload),
                          content_type='application/json')
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 2.0, f"API demorou {elapsed:.2f}s (limite: 2s)"


# ============================================
# EXECUTAR TESTES
# ============================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])


"""
COMANDOS ÚTEIS:

1. Instalar dependências:
   pip install -r requirements.txt

2. Executar API:
   cd src
   python api.py

3. Executar testes:
   pytest tests/test_api.py -v

4. Executar teste específico:
   pytest tests/test_api.py::test_health_check -v
"""