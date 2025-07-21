from passlib.context import CryptContext

# Asegúrate de que esto es idéntico a lo que tienes en security.py
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

password_to_hash = "admin"
hashed_password = pwd_context.hash(password_to_hash)

print(f"La contraseña '{password_to_hash}' hasheada es:")
print(hashed_password)
