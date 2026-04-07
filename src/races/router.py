from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.auth.service import fastapi_users
from src.auth.models import User
from src.races import service
from src.races.schemas import RaceShort, RaceOut, RaceResultsOut, RaceCreate
current_user = fastapi_users.current_user()
router = APIRouter()


@router.get("/", response_model=list[RaceShort])
async def list_races(session: AsyncSession = Depends(get_session)):
    races = await service.get_all_races(session)
    
    result = []
    for race in races:
        count = await service.get_count_users(race.id, session)
        result.append(RaceShort.model_validate({
            "id": race.id,
            "name": race.name,
            "race": race.race,
            "time": race.time,
            "status": race.status,
            "maxuser": race.maxuser,
            "users": count
        }))
    
    return result

@router.post("/", response_model=RaceOut, status_code=status.HTTP_201_CREATED)
async def create_race(
    race_data: RaceCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session)
):
    race = await service.create_race(
        name=race_data.name,
        race=race_data.race,
        about=race_data.about,
        time=race_data.time,
        maxuser=race_data.maxuser,
        status=race_data.status,
        created_by=str(user.id),
        session=session
    )
    
    return RaceOut.model_validate({
        "id": race.id,
        "name": race.name,
        "race": race.race,
        "about": race.about,
        "time": race.time,
        "status": race.status,
        "maxuser": race.maxuser,
        "users": 0
    })

@router.get("/{race_id}", response_model=RaceOut)
async def get_race(race_id: int, session: AsyncSession = Depends(get_session)):
    race = await service.get_race(race_id, session)
    count = await service.get_count_users(race_id, session)
    
    return RaceOut.model_validate({
        "id": race.id,
        "name": race.name,
        "race": race.race,
        "about": race.about,
        "time": race.time,
        "status": race.status,
        "maxuser": race.maxuser,
        "users": count
    })


@router.get("/{race_id}/all_users")
async def get_participants(race_id: int, session: AsyncSession = Depends(get_session)):
    await service.get_race(race_id, session)
    participants = await service.get_all_users(race_id, session)
    
    return [
        {
            "user_id": p.user_id,
        }
        for p in participants
    ]


@router.get("/{race_id}/results", response_model=RaceResultsOut)
async def get_results(race_id: int, session: AsyncSession = Depends(get_session)):
    race = await service.get_race(race_id, session)
    results = await service.get_results(race_id, session)
    
    return RaceResultsOut.model_validate({
        "race_id": race.id,
        "race_name": race.name,
        "results": [
            {
                "user_id": r.user_id,
                "username": r.user.username,
                "position": r.position
            }
            for r in results
        ]
    })


@router.post("/{race_id}/register", status_code=status.HTTP_201_CREATED)
async def register(
    race_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session)
):
    await service.register_user(race_id, str(user.id), session)
    return {"message": "registered"}


@router.delete("/{race_id}/unregister", status_code=status.HTTP_204_NO_CONTENT)
async def unregister(
    race_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session)
):
    await service.unregister_user(race_id, str(user.id), session)