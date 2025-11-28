from typing import List
from fastapi import APIRouter, Depends

from app.routers.access import check_access
from app.schemas.auth import StatusResponse
from app.schemas.items import ItemOut


router = APIRouter(prefix='/items', tags=['Items'])


@router.get('/', response_model=List[ItemOut])
def list_items(user=Depends(check_access('items', 'read'))):
    return [
        ItemOut(
            id=1,
            name='Item A',
            description='...',
        ),
        ItemOut(
            id=2,
            name='Item B',
            description='...',
        ),
    ]


@router.post('/', response_model=StatusResponse)
def create_item(user=Depends(check_access('items', 'write'))):
    return StatusResponse(status='created')
