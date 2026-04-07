from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel

engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Game(Base):
    __tablename__ = "Games"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    score = Column(Integer)


class GameIn(BaseModel):
    name: str
    email: str
    score: int


class GameOut(GameIn):
    id: int

    class Config:
        from_attributes = True


app = FastAPI()
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/Game/", response_model=GameOut)
def create(game_in: GameIn, db: Session = Depends(get_db)):
    db_game = Game(name=game_in.name, email=game_in.email, score=game_in.score)
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


@app.get("/Game/", response_model=list[GameOut])
def get_items(db: Session = Depends(get_db)):
    return db.execute(select(Game)).scalars().all()


@app.get("/Game/{game_id}", response_model=GameOut)
def get_item(game_id: int, db: Session = Depends(get_db)):
    game = db.execute(select(Game).where(Game.id == game_id)).scalar_one_or_none()
    if game is None:
        raise HTTPException(status_code=404)
    return game