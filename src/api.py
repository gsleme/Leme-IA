"""
LEME - API Flask (Versão Final Simplificada)
app.py

3 Endpoints:
1. GET  /health           - Health check
2. POST /suggest_trilha   - Sugere trilha + módulos com URLs
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
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CARREGAR MODELOS
# ============================================

try:
    # Modelo de Classificação
    with open('../models/leme_modelo_classificacao.pkl', 'rb') as f:
        modelo_class = pickle.load(f)
    with open('../models/leme_scaler_class.pkl', 'rb') as f:
        scaler_class = pickle.load(f)
    
    # Modelo de Regressão
    with open('../models/leme_modelo_regressao.pkl', 'rb') as f:
        modelo_reg = pickle.load(f)
    with open('../models/leme_scaler_reg.pkl', 'rb') as f:
        scaler_reg = pickle.load(f)
    
    # Encoders
    with open('../models/leme_encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)
    
    # Catálogo de trilhas (novo formato)
    with open('../data/trilhas.json', 'r', encoding='utf-8') as f:
        TRILHAS = json.load(f)
    
    logger.info("✅ Modelos carregados com sucesso")
    
except Exception as e:
    logger.error(f"❌ Erro ao carregar modelos: {e}")
    raise

# Extrair encoders
le_area = encoders['area']
le_acess = encoders['acessibilidade']
features = encoders['features']

# ============================================
# FUNÇÃO AUXILIAR
# ============================================

def criar_features(area, acessibilidade, modulos, tempo):
    """
    Converte dados do perfil em array de features
    
    Input: area, acessibilidade, modulos_concluidos, tempo_plataforma_dias
    Output: np.array para o modelo
    """
    perfil = {
        'area_encoded': le_area.transform([area])[0],
        'acess_encoded': le_acess.transform([acessibilidade])[0],
        'modulos_concluidos': modulos,
        'tempo_plataforma_dias': tempo
    }
    
    X = np.array([[perfil[f] for f in features]])
    return X

# ============================================
# ENDPOINT 1: HEALTH CHECK
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check
    
    Response:
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
# ENDPOINT 2: SUGERIR TRILHA (SIMPLIFICADO)
# ============================================

@app.route('/suggest_trilha', methods=['POST'])
def suggest_trilha():
    """
    Sugere trilha personalizada
    
    Request Body:
    {
        "area": "Advogado",
        "acessibilidade": "cego",
        "modulos_concluidos": 0,
        "tempo_plataforma_dias": 0
    }
    
    Response:
    {
        "trilha": "IA para Advogados",
        "modulos": [
            {"titulo": "Módulo 1: ...", "url_conteudo": "https://..."},
            {"titulo": "Módulo 2: ...", "url_conteudo": "https://..."},
            ...
        ],
        "confianca": 0.89
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
        
        # Criar features e normalizar
        X = criar_features(area, acessibilidade, modulos, tempo)
        X_scaled = scaler_class.transform(X)
        
        # Predição: o modelo pode retornar "Advogado" ou "Advogado_Acessivel"
        # Como removemos trilhas acessíveis do JSON, vamos limpar o sufixo
        trilha_pred = modelo_class.predict(X_scaled)[0]
        
        # IMPORTANTE: Remover sufixo "_Acessivel" se existir
        # Exemplo: "Advogado_Acessivel" → "Advogado"
        trilha_key = trilha_pred.replace('_Acessivel', '')
        
        # Calcular confiança
        proba = modelo_class.predict_proba(X_scaled)[0]
        confianca = float(proba.max())
        
        # Buscar trilha no catálogo
        if trilha_key not in TRILHAS:
            logger.warning(f"Trilha não encontrada: {trilha_key}")
            return jsonify({'erro': f'Trilha {trilha_key} não encontrada no catálogo'}), 404
        
        trilha_detalhes = TRILHAS[trilha_key]
        
        # Resposta SIMPLIFICADA (sem adaptacoes)
        resposta = {
            'trilha': trilha_detalhes['nome'],
            'modulos': trilha_detalhes['modulos'],  # Agora é lista de objetos
            'confianca': round(confianca, 3)
        }
        
        logger.info(f"Sugestão: {trilha_detalhes['nome']} (confiança: {confianca:.2%})")
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
    Prevê taxa de conclusão
    
    Request Body:
    {
        "area": "Design",
        "acessibilidade": "libras",
        "modulos_concluidos": 2,
        "tempo_plataforma_dias": 15
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
        
        # Validar
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
        
        # Predição
        taxa = float(modelo_reg.predict(X_scaled)[0])
        taxa = max(0.0, min(1.0, taxa))
        
        # Classificar
        if taxa >= 0.75:
            categoria = 'alta'
            recomendacao = 'Usuário tem boa chance de completar a trilha'
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
# EXECUTAR
# ============================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)