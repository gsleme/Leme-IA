"""
LEME - Sprint 2, Dias 5-7: API Flask (VERSÃO FINAL)

3 Endpoints:
1. GET  /health           - Verifica se API está online
2. POST /suggest_trilha   - Sugere trilha personalizada
3. POST /predict_sucesso  - Prevê taxa de conclusão
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import json
from datetime import datetime
import logging

# ============================================
# CONFIGURAÇÃO
# ============================================

app = Flask(__name__)
CORS(app)  # Permitir requisições do React

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CARREGAR MODELOS
# ============================================

try:
    # Modelo de Classificação
    with open('./models/leme_modelo_classificacao.pkl', 'rb') as f:
        modelo_class = pickle.load(f)
    with open('./models/leme_scaler_class.pkl', 'rb') as f:
        scaler_class = pickle.load(f)
    
    # Modelo de Regressão
    with open('./models/leme_modelo_regressao.pkl', 'rb') as f:
        modelo_reg = pickle.load(f)
    with open('./models/leme_scaler_reg.pkl', 'rb') as f:
        scaler_reg = pickle.load(f)
    
    # Encoders
    with open('./models/leme_encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)
    
    # Catálogo de trilhas
    with open('./data/leme_trilhas.json', 'r', encoding='utf-8') as f:
        TRILHAS = json.load(f)
    
    logger.info("✅ Modelos carregados com sucesso")
    
except Exception as e:
    logger.error(f"❌ Erro ao carregar modelos: {e}")
    raise

# Extrair encoders e features
le_area = encoders['area']
le_acess = encoders['acessibilidade']
features = encoders['features']

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

def criar_features(area, acessibilidade, modulos, tempo):
    """
    Converte dados do perfil em array de features para o modelo
    
    Input: area, acessibilidade, modulos_concluidos, tempo_plataforma_dias
    Output: np.array com features codificadas
    """
    perfil = {
        'area_encoded': le_area.transform([area])[0],
        'acess_encoded': le_acess.transform([acessibilidade])[0],
        'modulos_concluidos': modulos,
        'tempo_plataforma_dias': tempo
    }
    
    X = np.array([[perfil[f] for f in features]])
    return X


def definir_adaptacoes(acessibilidade):
    """
    Define quais adaptações devem ser ativadas no frontend
    
    Input: tipo de acessibilidade
    Output: lista de adaptações
    """
    if acessibilidade == 'cego':
        return ['text_to_speech', 'alto_contraste', 'navegacao_teclado']
    elif acessibilidade == 'libras':
        return ['videos_libras', 'legendas_ativadas']
    else:
        return []

# ============================================
# ENDPOINT 1: HEALTH CHECK
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """
    Verifica se a API está funcionando
    
    Resposta:
    {
        "status": "ok",
        "timestamp": "2024-11-13T10:30:00",
        "modelos": true
    }
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'modelos': True
    }), 200


# ============================================
# ENDPOINT 2: SUGERIR TRILHA
# ============================================

@app.route('/suggest_trilha', methods=['POST'])
def suggest_trilha():
    """
    Sugere trilha personalizada baseada no perfil do usuário
    
    Request Body (JSON):
    {
        "area": "Advogado",                    // obrigatório
        "acessibilidade": "cego",              // obrigatório
        "modulos_concluidos": 0,               // opcional (padrão: 0)
        "tempo_plataforma_dias": 0             // opcional (padrão: 0)
    }
    
    Response:
    {
        "trilha": "IA para Advogados (Acessível)",
        "modulos": ["Módulo 1: ...", ...],
        "adaptacoes": ["text_to_speech", ...],
        "confianca": 0.89
    }
    """
    try:
        # Receber dados
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data or 'area' not in data or 'acessibilidade' not in data:
            return jsonify({'erro': 'Campos obrigatórios: area, acessibilidade'}), 400
        
        # Extrair dados (com valores padrão)
        area = data['area']
        acessibilidade = data['acessibilidade']
        modulos = data.get('modulos_concluidos', 0)
        tempo = data.get('tempo_plataforma_dias', 0)
        
        # Criar features
        X = criar_features(area, acessibilidade, modulos, tempo)
        X_scaled = scaler_class.transform(X)
        
        # Predição: qual trilha sugerir
        trilha_id = modelo_class.predict(X_scaled)[0]
        proba = modelo_class.predict_proba(X_scaled)[0]
        confianca = float(proba.max())
        
        # Buscar detalhes da trilha
        trilha_detalhes = TRILHAS.get(trilha_id, {
            'nome': 'Trilha Padrão',
            'modulos': []
        })
        
        # Definir adaptações
        adaptacoes = definir_adaptacoes(acessibilidade)
        
        # Resposta
        resposta = {
            'trilha': trilha_detalhes['nome'],
            'modulos': trilha_detalhes['modulos'],
            'adaptacoes': adaptacoes,
            'confianca': round(confianca, 3)
        }
        
        logger.info(f"Sugestão: {trilha_detalhes['nome']} (conf: {confianca:.2%})")
        return jsonify(resposta), 200
        
    except Exception as e:
        logger.error(f"Erro em /suggest_trilha: {e}")
        return jsonify({'erro': str(e)}), 500


# ============================================
# ENDPOINT 3: PREVER SUCESSO
# ============================================

@app.route('/predict_sucesso', methods=['POST'])
def predict_sucesso():
    """
    Prevê probabilidade do usuário completar a trilha
    
    Request Body (JSON):
    {
        "area": "Design",                      // obrigatório
        "acessibilidade": "libras",            // obrigatório
        "modulos_concluidos": 2,               // opcional (padrão: 0)
        "tempo_plataforma_dias": 15            // opcional (padrão: 0)
    }
    
    Response:
    {
        "taxa_sucesso": 0.78,
        "categoria": "alta",
        "recomendacao": "Usuário tem boa chance de completar a trilha"
    }
    """
    try:
        # Receber dados
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data or 'area' not in data or 'acessibilidade' not in data:
            return jsonify({'erro': 'Campos obrigatórios: area, acessibilidade'}), 400
        
        # Extrair dados
        area = data['area']
        acessibilidade = data['acessibilidade']
        modulos = data.get('modulos_concluidos', 0)
        tempo = data.get('tempo_plataforma_dias', 0)
        
        # Criar features
        X = criar_features(area, acessibilidade, modulos, tempo)
        X_scaled = scaler_reg.transform(X)
        
        # Predição: taxa de conclusão
        taxa = float(modelo_reg.predict(X_scaled)[0])
        taxa = max(0.0, min(1.0, taxa))  # Limitar entre 0 e 1
        
        # Classificar taxa
        if taxa >= 0.75:
            categoria = 'alta'
            recomendacao = 'Usuário tem alta chance de completar a trilha'
        elif taxa >= 0.50:
            categoria = 'media'
            recomendacao = 'Usuário tem chance média - considere suporte adicional'
        else:
            categoria = 'baixa'
            recomendacao = 'Usuário pode precisar de módulos mais simples ou suporte'
        
        # Resposta
        resposta = {
            'taxa_sucesso': round(taxa, 3),
            'categoria': categoria,
            'recomendacao': recomendacao
        }
        
        logger.info(f"Previsão: {taxa:.1%} ({categoria})")
        return jsonify(resposta), 200
        
    except Exception as e:
        logger.error(f"Erro em /predict_sucesso: {e}")
        return jsonify({'erro': str(e)}), 500


# ============================================
# EXECUTAR API
# ============================================

if __name__ == '__main__':
    # Desenvolvimento: debug=True
    # Produção: usar Gunicorn (ver instruções abaixo)
    app.run(debug=True, host='0.0.0.0', port=5000)


"""
INSTRUÇÕES DE USO:

1. EXECUTAR LOCALMENTE (Desenvolvimento):
   cd src
   python api.py
   
   API rodará em: http://localhost:5000

2. TESTAR COM CURL:
   
   # Health check
   curl http://localhost:5000/health
   
   # Sugerir trilha
   curl -X POST http://localhost:5000/suggest_trilha \
     -H "Content-Type: application/json" \
     -d '{"area":"Advogado","acessibilidade":"cego"}'
   
   # Prever sucesso
   curl -X POST http://localhost:5000/predict_sucesso \
     -H "Content-Type: application/json" \
     -d '{"area":"Design","acessibilidade":"libras","modulos_concluidos":3,"tempo_plataforma_dias":20}'

3. PRODUÇÃO (Gunicorn):
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 api:app
"""