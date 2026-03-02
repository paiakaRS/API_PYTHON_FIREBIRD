from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
import pandas as pd
from sqlalchemy import create_engine
from fastapi import Body
from sqlalchemy import text # ADICIONE ESTA IMPORTAÇÃO NO TOPO

# CONFIGURAÇÕES
MINHA_CHAVE_SECRETA = "minha-chave-123"
NOME_DO_CABECALHO = "access_token"

app = FastAPI(title="API Firebird Protegida")

# Ajuste para o Swagger entender o cabeçalho corretamente
api_key_header = APIKeyHeader(name=NOME_DO_CABECALHO, auto_error=True)

# Engine Firebird
engine = create_engine(r'firebird+fdb://sysdba:masterkey@localhost:3050/D:\TESTE.FDB')

# VALIDAÇÃO
async def verificar_token(api_key: str = Security(api_key_header)):
    if api_key == MINHA_CHAVE_SECRETA:
        return api_key
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Token inválido ou ausente"
    )

# ROTAS PROTEGIDAS

@app.get("/produtos", dependencies=[Depends(verificar_token)])
def listar_produtos():
    try:
        query = "SELECT FIRST 10 PROD, DESCR, PRREF AS PRECO FROM CADPROD Order by PROD"
        df = pd.read_sql(query, engine)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ROTA DE BUSCA POR CÓDIGO (DE VOLTA!)
@app.get("/produto/{codigo}", dependencies=[Depends(verificar_token)])
def buscar_produto(codigo: int):
    try:
        # Usando f-string para o SQL (Como o ParamByName do Delphi)
        query = f"SELECT PROD, DESCR, PRREF AS PRECO FROM CADPROD WHERE PROD = {codigo}"
        df = pd.read_sql(query, engine)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
            
        return df.to_dict(orient="records")[0] # Retorna apenas o objeto, não uma lista
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/atualizar-preco", dependencies=[Depends(verificar_token)])
def atualizar_preco(codigo: int, novo_preco: float):
    try:
        with engine.begin() as conn:
            sql = text("UPDATE CADPROD SET PRREF = :preco WHERE PROD = :cod")
            conn.execute(sql, {"preco": novo_preco, "cod": codigo})
        return {"status": "Sucesso", "mensagem": f"Produto {codigo} atualizado para {novo_preco}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
