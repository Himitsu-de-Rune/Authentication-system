from fastapi import APIRouter, Depends

from access import check_access


router = APIRouter(prefix='/items')


@router.get('/')
def list_items(user=Depends(check_access('items', 'read'))):
    return [{'id': 1, 'name': 'Item A'}, {'id': 2, 'name': 'Item B'}]


@router.post('/')
def create_item(user=Depends(check_access('items', 'write'))):
    return {'status': 'created'}
