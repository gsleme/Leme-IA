"""
LEME - API Flask (VERSÃO FINAL - Retorna UUIDs)
app.py

3 Endpoints:
1. GET  /health           - Health check
2. POST /suggest_trilha   - Retorna UUID da trilha sugerida
3. POST /predict_sucesso  - Retorna taxa de sucesso e categoria
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import numpy as np
import json
from datetime import datetime
import logging
import traceback

# ============================================
# CONFIGURAÇÃO
# ============================================

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
# CARREGAR MODELOS E DADOS
# ============================================

try:
    # Modelo de Classificação
    with open('./models/leme_modelo_classificacao.pkl', 'rb') as f:
        modelo_class = pickle.load(f)
    logger.info("✅ Modelo de classificação carregado")
    
    with open('./models/leme_scaler_class.pkl', 'rb') as f:
        scaler_class = pickle.load(f)
    logger.info("✅ Scaler de classificação carregado")
    
    # Modelo de Regressão
    with open('./models/leme_modelo_regressao.pkl', 'rb') as f:
        modelo_reg = pickle.load(f)
    logger.info("✅ Modelo de regressão carregado")
    
    with open('./models/leme_scaler_reg.pkl', 'rb') as f:
        scaler_reg = pickle.load(f)
    logger.info("✅ Scaler de regressão carregado")
    
    # Encoders
    with open('./models/leme_encoders.pkl', 'rb') as f:
        encoders = pickle.load(f)
    logger.info("✅ Encoders carregados")
    
    # Catálogo de trilhas (com UUIDs)
    with open('./data/leme_trilhas.json', 'r', encoding='utf-8') as f:
        TRILHAS = json.load(f)
    logger.info(f"✅ Catálogo carregado: {len(TRILHAS)} trilhas")
    
    logger.info("="*60)
    logger.info("✅ TODOS OS MODELOS CARREGADOS COM SUCESSO")
    logger.info("="*60)
    
except FileNotFoundError as e:
    logger.error(f"❌ Arquivo não encontrado: {e}")
    logger.error("Verifique os caminhos:")
    logger.error("  - models/leme_modelo_classificacao.pkl")
    logger.error("  - models/leme_scaler_class.pkl")
    logger.error("  - models/leme_modelo_regressao.pkl")
    logger.error("  - models/leme_scaler_reg.pkl")
    logger.error("  - models/leme_encoders.pkl")
    logger.error("  - data/trilhas.json")
    raise
except Exception as e:
    logger.error(f"❌ Erro ao carregar modelos: {e}")
    logger.error(traceback.format_exc())
    raise

# Extrair encoders
le_area = encoders['area']
le_acess = encoders['acessibilidade']
features = encoders['features']

logger.info(f"Features: {features}")
logger.info(f"Áreas: {list(le_area.classes_)}")
logger.info(f"Acessibilidades: {list(le_acess.classes_)}")

# ============================================
# FUNÇÃO AUXILIAR
# ============================================

def criar_features(area, acessibilidade, modulos, tempo):
    """
    Converte dados do perfil em array de features para o modelo
    
    Args:
        area (str): Área profissional
        acessibilidade (str): Tipo de acessibilidade
        modulos (int): Módulos concluídos
        tempo (int): Dias na plataforma
    
    Returns:
        np.array: Array de features normalizado
    """
    try:
        perfil = {
            'area_encoded': le_area.transform([area])[0],
            'acess_encoded': le_acess.transform([acessibilidade])[0],
            'modulos_concluidos': modulos,
            'tempo_plataforma_dias': tempo
        }
        
        X = np.array([[perfil[f] for f in features]])
        return X
    except Exception as e:
        logger.error(f"Erro em criar_features: {e}")
        raise

# ============================================
# ENDPOINT 1: HEALTH CHECK
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """
    Health check - Verifica se API está online
    
    Response:
        200: {
            "status": "ok",
            "timestamp": "2024-11-18T10:30:00",
            "modelos": true,
            "trilhas_disponiveis": 12
        }
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'modelos': True,
        'trilhas_disponiveis': len(TRILHAS)
    }), 200


# ============================================
# ENDPOINT 2: SUGERIR TRILHA (RETORNA UUID)
# ============================================

@app.route('/suggest_trilha', methods=['POST'])
def suggest_trilha():
    """
    Sugere trilha personalizada e retorna apenas o UUID
    
    Request Body:
        {
            "area": "Advogado",
            "acessibilidade": "cego",
            "modulos_concluidos": 0,        // opcional
            "tempo_plataforma_dias": 0      // opcional
        }
    
    Response:
        200: {
            "id_trilha": "a1b2c3d4-e5f6-47a8-9b0c-1d2e3f4a5b6c",
            "confianca": 0.89
        }
        
        400: {"erro": "Campo obrigatório: area"}
        404: {"erro": "Trilha não encontrada"}
        500: {"erro": "Erro interno"}
    """
    try:
        # Receber dados JSON
        data = request.get_json()
        
        if not data:
            logger.warning("Requisição sem JSON")
            return jsonify({'erro': 'Request body deve ser JSON'}), 400
        
        logger.info(f"Requisição recebida: {data}")
        
        # Validar campos obrigatórios
        if 'area' not in data:
            return jsonify({'erro': 'Campo obrigatório: area'}), 400
        if 'acessibilidade' not in data:
            return jsonify({'erro': 'Campo obrigatório: acessibilidade'}), 400
        
        # Extrair dados
        area = data['area']
        acessibilidade = data['acessibilidade']
        modulos = data.get('modulos_concluidos', 0)
        tempo = data.get('tempo_plataforma_dias', 0)
        
        # Validar valores das áreas
        areas_validas = list(le_area.classes_)
        if area not in areas_validas:
            return jsonify({
                'erro': f'Área inválida. Valores aceitos: {areas_validas}'
            }), 400
        
        # Validar acessibilidades
        acess_validas = list(le_acess.classes_)
        if acessibilidade not in acess_validas:
            return jsonify({
                'erro': f'Acessibilidade inválida. Valores aceitos: {acess_validas}'
            }), 400
        
        # Criar features e normalizar
        X = criar_features(area, acessibilidade, modulos, tempo)
        X_scaled = scaler_class.transform(X)
        
        # Predição do modelo
        trilha_pred = modelo_class.predict(X_scaled)[0]
        logger.info(f"Modelo previu: {trilha_pred}")
        
        # Calcular confiança
        proba = modelo_class.predict_proba(X_scaled)[0]
        confianca = float(proba.max())
        
        # Buscar trilha no catálogo para pegar o UUID
        if trilha_pred not in TRILHAS:
            logger.error(f"Trilha {trilha_pred} não encontrada no catálogo")
            logger.error(f"Trilhas disponíveis: {list(TRILHAS.keys())}")
            return jsonify({
                'erro': f'Trilha {trilha_pred} não encontrada no catálogo'
            }), 404
        
        trilha_detalhes = TRILHAS[trilha_pred]
        id_trilha = trilha_detalhes['id_trilha']
        
        # Resposta FINAL: apenas UUID e confiança
        resposta = {
            'id_trilha': id_trilha,
            'confianca': round(confianca, 3)
        }
        
        logger.info(f"✅ Sugestão: {id_trilha} (confiança: {confianca:.2%})")
        return jsonify(resposta), 200
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro em /suggest_trilha: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500


# ============================================
# ENDPOINT 3: PREVER SUCESSO (SEM RECOMENDAÇÃO)
# ============================================

@app.route('/predict_sucesso', methods=['POST'])
def predict_sucesso():
    """
    Prevê taxa de conclusão do usuário
    
    Request Body:
        {
            "area": "Design",
            "acessibilidade": "libras",
            "modulos_concluidos": 2,        // opcional
            "tempo_plataforma_dias": 15     // opcional
        }
    
    Response:
        200: {
            "taxa_sucesso": 0.780,
            "categoria": "alta"
        }
        
        400: {"erro": "Campo obrigatório: area"}
        500: {"erro": "Erro interno"}
    """
    try:
        # Receber dados
        data = request.get_json()
        
        if not data:
            logger.warning("Requisição sem JSON")
            return jsonify({'erro': 'Request body deve ser JSON'}), 400
        
        logger.info(f"Requisição recebida: {data}")
        
        # Validar campos obrigatórios
        if 'area' not in data:
            return jsonify({'erro': 'Campo obrigatório: area'}), 400
        if 'acessibilidade' not in data:
            return jsonify({'erro': 'Campo obrigatório: acessibilidade'}), 400
        
        # Extrair dados
        area = data['area']
        acessibilidade = data['acessibilidade']
        modulos = data.get('modulos_concluidos', 0)
        tempo = data.get('tempo_plataforma_dias', 0)
        
        # Validar valores
        areas_validas = list(le_area.classes_)
        if area not in areas_validas:
            return jsonify({
                'erro': f'Área inválida. Valores aceitos: {areas_validas}'
            }), 400
        
        acess_validas = list(le_acess.classes_)
        if acessibilidade not in acess_validas:
            return jsonify({
                'erro': f'Acessibilidade inválida. Valores aceitos: {acess_validas}'
            }), 400
        
        # Criar features
        X = criar_features(area, acessibilidade, modulos, tempo)
        X_scaled = scaler_reg.transform(X)
        
        # Predição
        taxa = float(modelo_reg.predict(X_scaled)[0])
        taxa = max(0.0, min(1.0, taxa))
        
        # Classificar em categorias
        if taxa >= 0.75:
            categoria = 'alta'
        elif taxa >= 0.50:
            categoria = 'media'
        else:
            categoria = 'baixa'
        
        # Resposta FINAL: apenas taxa e categoria (SEM recomendacao)
        resposta = {
            'taxa_sucesso': round(taxa, 3),
            'categoria': categoria
        }
        
        logger.info(f"✅ Previsão: {taxa:.1%} ({categoria})")
        return jsonify(resposta), 200
        
    except ValueError as e:
        logger.error(f"Erro de validação: {e}")
        return jsonify({'erro': str(e)}), 400
    except Exception as e:
        logger.error(f"Erro em /predict_sucesso: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500


# ============================================
# EXECUTAR API
# ============================================

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("🚀 Iniciando API LEME - Versão Final")
    logger.info("="*60)
    app.run(debug=True, host='0.0.0.0', port=5000)