from fastapi import FastAPI

app = FastAPI(title="Assistente de Agenda Pessoal")


@app.get("/")
def raiz():
    return {"mensagem": "Assistente de Agenda Pessoal funcionando"}