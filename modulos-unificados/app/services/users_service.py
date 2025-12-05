# app/services/users_service.py
"""
Servicio para gestión de usuarios
"""

from sqlalchemy.orm import Session
from app.models.db_models import User
from app.models.schemas import UserCreate, UserLogin, UserResponse
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando SHA-256
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Hash de la contraseña
    """
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Crea un nuevo usuario en la base de datos
    
    Args:
        db: Sesión de base de datos
        user_data: Datos del usuario a crear
        
    Returns:
        Usuario creado
        
    Raises:
        ValueError: Si el usuario ya existe
    """
    # Verificar si el usuario ya existe
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(f"Intento de crear usuario duplicado: {user_data.username}")
        raise ValueError(f"El usuario '{user_data.username}' ya existe")
    
    # Crear el nuevo usuario
    password_hash = hash_password(user_data.password)
    
    new_user = User(
        username=user_data.username,
        password_hash=password_hash,
        formulario_inicio=user_data.formulario_inicio,
        created_at=datetime.now()
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"Usuario creado exitosamente: {new_user.username}")
    return new_user


def authenticate_user(db: Session, login_data: UserLogin) -> User:
    """
    Autentica un usuario verificando sus credenciales
    
    Args:
        db: Sesión de base de datos
        login_data: Datos de login (username y password)
        
    Returns:
        Usuario autenticado
        
    Raises:
        ValueError: Si las credenciales son incorrectas
    """
    # Buscar el usuario
    user = db.query(User).filter(User.username == login_data.username).first()
    
    if not user:
        logger.warning(f"Intento de login con usuario inexistente: {login_data.username}")
        raise ValueError("Usuario o contraseña incorrectos")
    
    # Verificar la contraseña
    password_hash = hash_password(login_data.password)
    
    if user.password_hash != password_hash:
        logger.warning(f"Intento de login con contraseña incorrecta para: {login_data.username}")
        raise ValueError("Usuario o contraseña incorrectos")
    
    logger.info(f"Usuario autenticado exitosamente: {user.username}")
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Obtiene un usuario por su ID
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        
    Returns:
        Usuario encontrado o None
    """
    return db.query(User).filter(User.id == user_id).first()


def update_formulario_inicio(db: Session, user_id: int, completed: bool) -> User:
    """
    Actualiza el estado del formulario inicial de un usuario
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        completed: Si completó el formulario
        
    Returns:
        Usuario actualizado
        
    Raises:
        ValueError: Si el usuario no existe
    """
    user = get_user_by_id(db, user_id)
    
    if not user:
        raise ValueError(f"Usuario con ID {user_id} no encontrado")
    
    user.formulario_inicio = completed
    db.commit()
    db.refresh(user)
    
    logger.info(f"Formulario inicial actualizado para usuario {user.username}: {completed}")
    return user
