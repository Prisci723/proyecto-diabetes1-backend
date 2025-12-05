# app/routers/users.py
"""
Router para gestión de usuarios
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import UserCreate, UserLogin, UserResponse
from app.services.users_service import create_user, authenticate_user, update_formulario_inicio

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registra un nuevo usuario en el sistema
    
    Args:
        user_data: Datos del nuevo usuario (username, password, formulario_inicio)
        db: Sesión de base de datos
        
    Returns:
        Datos del usuario creado
        
    Raises:
        HTTPException 400: Si el usuario ya existe
    """
    try:
        new_user = create_user(db, user_data)
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            formulario_inicio=new_user.formulario_inicio,
            created_at=new_user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=UserResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Autentica un usuario y devuelve sus datos
    
    Args:
        login_data: Credenciales del usuario (username, password)
        db: Sesión de base de datos
        
    Returns:
        Datos del usuario autenticado
        
    Raises:
        HTTPException 401: Si las credenciales son incorrectas
    """
    try:
        user = authenticate_user(db, login_data)
        return UserResponse(
            id=user.id,
            username=user.username,
            formulario_inicio=user.formulario_inicio,
            created_at=user.created_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.patch("/{user_id}/formulario-inicio")
def update_formulario(
    user_id: int,
    completed: bool,
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado del formulario inicial de un usuario
    
    Args:
        user_id: ID del usuario
        completed: Si completó el formulario
        db: Sesión de base de datos
        
    Returns:
        Mensaje de confirmación
        
    Raises:
        HTTPException 404: Si el usuario no existe
    """
    try:
        user = update_formulario_inicio(db, user_id, completed)
        return {
            "message": "Formulario inicial actualizado",
            "user_id": user.id,
            "formulario_inicio": user.formulario_inicio
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
