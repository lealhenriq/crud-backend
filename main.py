from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware

# Configurações do Banco de Dados
DATABASE_URL = "sqlite:///./database.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Inicializa o FastAPI
app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos
    allow_headers=["*"],  # Permite todos os headers
)

# Modelo de Usuário para Login
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

# Modelo de Produto
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Cria usuário admin padrão
def create_admin():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(username="admin", password="admin")
        db.add(admin)
        db.commit()
    db.close()

create_admin()

# Dependência do Banco de Dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rota para Login
@app.post("/login")
def login(user_data: dict, db: Session = Depends(get_db)):
    username = user_data.get("username")
    password = user_data.get("password")
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return {"message": "Login realizado com sucesso!"}

# Rota para Criar um Usuário (apenas para testes iniciais)
@app.post("/users")
def create_user(username: str, password: str, db: Session = Depends(get_db)):
    user = User(username=username, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuário criado com sucesso", "user": user}

# Rotas de Produtos
@app.get("/products", response_model=list[dict])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [{"id": p.id, "name": p.name, "description": p.description, "price": p.price} for p in products]

@app.post("/products")
def add_product(product_data: dict, db: Session = Depends(get_db)):
    product = Product(
        name=product_data["name"],
        description=product_data["description"], 
        price=product_data["price"]
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return {"message": "Produto adicionado com sucesso", "product": product}

@app.put("/products/{product_id}") 
def update_product(product_id: int, product_data: dict, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    product.name = product_data["name"]
    product.description = product_data["description"]
    product.price = product_data["price"]
    db.commit()
    return {"message": "Produto atualizado com sucesso", "product": product}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    db.delete(product)
    db.commit()
    return {"message": "Produto excluído com sucesso"}


@app.get("/")
def root(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    total_products = len(products)
    total_value = sum(p.price for p in products)
    return {
        "relatorio": {
            "total_produtos": total_products,
            "valor_total_estoque": f"R$ {total_value:.2f}"
        }
    }